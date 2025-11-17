"""
Optimized RTSP to HLS Stream Manager using ffmpeg
Converts RTSP streams to HLS format for browser playback with low latency and minimal resource usage
"""
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamManager:
    def __init__(self, output_dir: str = "static/streams"):
        """
        Initialize the Optimized Stream Manager
        
        Args:
            output_dir: Directory to store HLS segments and playlists
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Dictionary to track active streams with enhanced metadata
        # Format: {stream_id: {
        #   'process': subprocess.Popen,
        #   'uri': str,
        #   'started_at': float,
        #   'playlist': str,
        #   'last_segment_time': float,
        #   'health_check_count': int,
        #   'reconnect_count': int
        # }}
        self.active_streams: Dict[str, Dict] = {}
        
        # Lock for thread-safe operations
        self._lock = threading.Lock()
        
        # Stream health monitoring thread
        self._health_check_thread = None
        self._health_check_interval = 10  # Check every 10 seconds
        self._health_check_running = False
        self._start_health_monitor()
    
    def _start_health_monitor(self):
        """Start background thread for stream health monitoring"""
        if self._health_check_thread is None or not self._health_check_thread.is_alive():
            self._health_check_running = True
            self._health_check_thread = threading.Thread(
                target=self._health_monitor_loop,
                daemon=True,
                name="StreamHealthMonitor"
            )
            self._health_check_thread.start()
            logger.info("Stream health monitor started")
    
    def _health_monitor_loop(self):
        """Background loop to monitor stream health and auto-recover"""
        while self._health_check_running:
            try:
                time.sleep(self._health_check_interval)
                self._check_stream_health()
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")
    
    def _check_stream_health(self):
        """Check health of all active streams and recover if needed"""
        with self._lock:
            for stream_id in list(self.active_streams.keys()):
                stream_info = self.active_streams[stream_id]
                
                # Check if process is still running
                if not self.is_stream_active(stream_id):
                    logger.warning(f"Stream {stream_id} process died, attempting recovery...")
                    self._recover_stream(stream_id)
                    continue
                
                # Check if playlist is being updated (segment freshness)
                playlist_path = self.output_dir / stream_id / "stream.m3u8"
                if playlist_path.exists():
                    last_modified = playlist_path.stat().st_mtime
                    age = time.time() - last_modified
                    
                    # If playlist hasn't been updated in 3 seconds, stream might be stuck (ultra low latency mode)
                    if age > 3:
                        logger.warning(f"Stream {stream_id} playlist stale (age: {age:.1f}s), checking...")
                        stream_info['health_check_count'] = stream_info.get('health_check_count', 0) + 1
                        
                        # If stale for multiple checks, restart stream
                        if stream_info['health_check_count'] > 2:
                            logger.error(f"Stream {stream_id} appears stuck, restarting...")
                            self._recover_stream(stream_id)
                else:
                    # Playlist doesn't exist yet, give it more time if recently started
                    if time.time() - stream_info['started_at'] > 30:
                        logger.warning(f"Stream {stream_id} playlist never created, restarting...")
                        self._recover_stream(stream_id)
    
    def _recover_stream(self, stream_id: str):
        """Attempt to recover a failed stream"""
        if stream_id not in self.active_streams:
            return
        
        stream_info = self.active_streams[stream_id]
        reconnect_count = stream_info.get('reconnect_count', 0)
        
        # Limit reconnection attempts
        if reconnect_count >= 3:
            logger.error(f"Stream {stream_id} exceeded max reconnection attempts, stopping")
            self._stop_stream_internal(stream_id)
            return
        
        logger.info(f"Recovering stream {stream_id} (attempt {reconnect_count + 1})")
        
        # Stop current process
        self._stop_stream_internal(stream_id)
        
        # Get original URI and credentials
        rtsp_uri = stream_info['uri']
        username = stream_info.get('username')
        password = stream_info.get('password')
        
        # Extract clean URI if credentials are already embedded
        # This prevents credential duplication on recovery
        if '@' in rtsp_uri and '://' in rtsp_uri:
            protocol, rest = rtsp_uri.split('://', 1)
            if '@' in rest:
                # Extract host part (everything after @)
                at_index = rest.find('@')
                host_part = rest[at_index + 1:]
                # Store clean URI for recovery (credentials will be added fresh)
                rtsp_uri = f"{protocol}://{host_part}"
        
        # Update reconnect count
        stream_info['reconnect_count'] = reconnect_count + 1
        stream_info['health_check_count'] = 0
        
        # Restart (without lock to avoid deadlock)
        threading.Timer(2.0, lambda: self.start_stream(
            stream_id, rtsp_uri, username, password
        )).start()
    
    def start_stream(
        self,
        stream_id: str,
        rtsp_uri: str,
        username: str = None,
        password: str = None,
        quality: str = "auto",
        max_bitrate: Optional[int] = None
    ) -> bool:
        """
        Start converting an RTSP stream to HLS with optimized settings
        
        Args:
            stream_id: Unique identifier for this stream
            rtsp_uri: RTSP URL to convert
            username: Optional RTSP username
            password: Optional RTSP password
            quality: Quality preset ("low", "medium", "high", "auto")
            max_bitrate: Maximum bitrate in kbps (None = no limit)
            
        Returns:
            True if stream started successfully, False otherwise
        """
        with self._lock:
            # Check if stream already running
            if stream_id in self.active_streams:
                if self.is_stream_active(stream_id):
                    logger.info(f"Stream {stream_id} is already running, reusing existing stream")
                    return True
                else:
                    # Clean up dead stream
                    logger.info(f"Cleaning up dead stream {stream_id}")
                    self._stop_stream_internal(stream_id)
            
            # Create output directory for this stream
            stream_dir = self.output_dir / stream_id
            stream_dir.mkdir(parents=True, exist_ok=True)
            
            # Clean any existing segments
            for file in stream_dir.glob("*.ts"):
                try:
                    file.unlink()
                except:
                    pass
            
            # Build RTSP URI with authentication if provided
            # Store clean URI first (for recovery), then build URI with credentials for FFmpeg
            clean_rtsp_uri = rtsp_uri
            ffmpeg_rtsp_uri = rtsp_uri
            
            # Check if credentials are already in the URI to avoid duplication
            if username and password:
                if '://' in rtsp_uri:
                    # Check if URI already has credentials embedded
                    protocol, rest = rtsp_uri.split('://', 1)
                    if '@' in rest:
                        # URI already has credentials, extract the host part
                        # Format: rtsp://user:pass@host:port/path
                        # We want to replace with new credentials
                        at_index = rest.find('@')
                        host_part = rest[at_index + 1:]  # Everything after @
                        clean_rtsp_uri = f"{protocol}://{host_part}"  # Store clean version
                        ffmpeg_rtsp_uri = f"{protocol}://{username}:{password}@{host_part}"
                    else:
                        # No credentials in URI, add them
                        clean_rtsp_uri = rtsp_uri  # Store original clean version
                        ffmpeg_rtsp_uri = f"{protocol}://{username}:{password}@{rest}"
            
            # Output playlist and segment pattern
            playlist_path = stream_dir / "stream.m3u8"
            segment_pattern = stream_dir / "segment_%03d.ts"
            
            # Build optimized ffmpeg command (use URI with credentials)
            cmd = self._build_ffmpeg_command(
                rtsp_uri=ffmpeg_rtsp_uri,
                playlist_path=playlist_path,
                segment_pattern=segment_pattern,
                quality=quality,
                max_bitrate=max_bitrate
            )
            
            try:
                # Log the command for debugging (without credentials)
                safe_cmd = [arg if '@' not in str(arg) else 'rtsp://***:***@...' for arg in cmd]
                logger.info(f"Starting FFmpeg for {stream_id} with command: {' '.join(safe_cmd[:10])}...")
                
                # Start ffmpeg process with optimized settings
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,  # Discard stdout to reduce overhead
                    stderr=subprocess.PIPE,      # Keep stderr for error logging
                    stdin=subprocess.DEVNULL,    # No stdin needed
                    preexec_fn=os.setsid if hasattr(os, 'setsid') else None  # Create new process group
                )
                
                # Give process a moment to start and check if it's still alive
                time.sleep(0.5)
                if process.poll() is not None:
                    # Process died immediately, get error
                    stderr_output = process.stderr.read().decode('utf-8', errors='ignore') if process.stderr else 'No stderr available'
                    logger.error(f"FFmpeg process for {stream_id} died immediately with return code {process.returncode}")
                    logger.error(f"FFmpeg stderr output: {stderr_output[:500]}")
                    return False
                
                # Store stream info with enhanced metadata
                relative_playlist = f"static/streams/{stream_id}/stream.m3u8"
                
                self.active_streams[stream_id] = {
                    'process': process,
                    'uri': clean_rtsp_uri,  # Store clean URI (without credentials) for recovery
                    'username': username,
                    'password': password,
                    'started_at': time.time(),
                    'last_segment_time': time.time(),
                    'playlist': relative_playlist,
                    'health_check_count': 0,
                    'reconnect_count': 0,
                    'quality': quality,
                    'max_bitrate': max_bitrate,
                    'stderr_buffer': []  # Store recent stderr output
                }
                
                # Start background thread to monitor FFmpeg stderr for errors
                stderr_thread = threading.Thread(
                    target=self._monitor_ffmpeg_stderr,
                    args=(stream_id, process),
                    daemon=True
                )
                stderr_thread.start()
                
                logger.info(f"Started optimized stream {stream_id} from {ffmpeg_rtsp_uri}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to start stream {stream_id}: {e}", exc_info=True)
                return False
    
    def _build_ffmpeg_command(
        self,
        rtsp_uri: str,
        playlist_path: Path,
        segment_pattern: Path,
        quality: str = "auto",
        max_bitrate: Optional[int] = None
    ) -> list:
        """
        Build optimized FFmpeg command for RTSP to HLS conversion
        
        Optimizations:
        - Skip audio re-encoding if possible (major CPU savings)
        - Lower latency settings
        - Better buffering
        - Connection timeouts
        - Reduced segment count for lower memory
        """
        cmd = ['ffmpeg']
        
        # RTSP input settings - optimized for reliability and low latency
        cmd.extend([
            '-rtsp_transport', 'tcp',           # TCP for reliability
            '-rtsp_flags', 'prefer_tcp',        # Prefer TCP
            '-timeout', '5000000',              # 5 second timeout (microseconds) - FFmpeg 8.x uses -timeout
            '-fflags', 'nobuffer+flush_packets', # Minimal buffering for low latency
            '-flags', 'low_delay',              # Low delay flag
        ])
        
        # Input
        cmd.extend(['-i', rtsp_uri])
        
        # Video codec - try to copy first (no re-encoding = minimal CPU)
        # Only re-encode if quality/bitrate limits are needed
        # Note: We'll set -c:v in the audio section to ensure proper mapping
        
        # Stream mapping and codec selection
        # Handle video and audio separately for better compatibility
        if quality != "auto" or max_bitrate:
            # Re-encoding needed - map streams explicitly
            cmd.extend(['-map', '0:v:0'])  # Map video
            cmd.extend(['-map', '0:a:0?'])  # Map audio if present (optional)
            
            # Determine video encoding settings based on quality
            if quality == "low":
                cmd.extend(['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28', '-maxrate', '500k', '-bufsize', '1000k'])
            elif quality == "medium":
                cmd.extend(['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-maxrate', '1500k', '-bufsize', '3000k'])
            elif quality == "high":
                cmd.extend(['-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-maxrate', '3000k', '-bufsize', '6000k'])
            else:
                # Auto: fast encode
                cmd.extend(['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23'])
            
            if max_bitrate:
                cmd.extend(['-maxrate', f'{max_bitrate}k', '-bufsize', f'{max_bitrate * 2}k'])
            
            # Audio encoding (if present)
            cmd.extend(['-c:a', 'aac', '-b:a', '64k', '-ar', '44100', '-ac', '2'])
        else:
            # Copy mode - simpler and faster
            cmd.extend(['-c:v', 'copy'])  # Copy video
            # Audio: HLS requires AAC, so we need to encode
            # Handle PCM_ALAW and other audio formats properly
            cmd.extend(['-c:a', 'aac', '-b:a', '64k', '-ar', '8000', '-ac', '1'])  # Match source audio properties
        
        # Fix timestamp issues
        cmd.extend(['-avoid_negative_ts', 'make_zero'])
        
        # HLS output settings - LOW LATENCY for real-time viewing
        # Simplified for FFmpeg 8.x compatibility
        cmd.extend([
            '-f', 'hls',
            '-hls_time', '2.0',                 # 2-second segments (more stable)
            '-hls_list_size', '5',              # Keep 5 segments (10 seconds total)
            '-hls_flags', 'delete_segments+independent_segments',  # Simplified flags (removed problematic ones)
            '-hls_segment_type', 'mpegts',      # MPEG-TS segments
            '-hls_segment_filename', str(segment_pattern),
            '-start_number', '0',
            '-hls_allow_cache', '0',            # Disable caching for live streams
        ])
        
        # Additional optimizations (only if re-encoding)
        if quality != "auto" or max_bitrate:
            cmd.extend([
                '-threads', '2',                    # Limit threads (reduce CPU usage)
                '-g', '30',                          # GOP size (keyframe every 30 frames ~1s at 30fps)
                '-keyint_min', '30',                 # Minimum keyframe interval
            ])
        
        # Output
        cmd.append(str(playlist_path))
        
        return cmd
    
    def _monitor_ffmpeg_stderr(self, stream_id: str, process: subprocess.Popen):
        """Monitor FFmpeg stderr output for errors and log them"""
        try:
            stderr_lines = []
            for line in iter(process.stderr.readline, b''):
                if not line:
                    break
                line_str = line.decode('utf-8', errors='ignore').strip()
                if line_str:
                    stderr_lines.append(line_str)
                    # Log errors and warnings
                    if 'error' in line_str.lower() or 'failed' in line_str.lower():
                        logger.error(f"FFmpeg error for {stream_id}: {line_str}")
                    elif 'warning' in line_str.lower():
                        logger.warning(f"FFmpeg warning for {stream_id}: {line_str}")
            
            # Store last 20 lines in stream info for debugging
            if stream_id in self.active_streams:
                self.active_streams[stream_id]['stderr_buffer'] = stderr_lines[-20:]
                
            # If process exited, log the last error lines
            if process.poll() is not None and process.returncode != 0:
                error_summary = '\n'.join(stderr_lines[-10:])  # Last 10 lines
                logger.error(f"FFmpeg process for {stream_id} exited with code {process.returncode}")
                if error_summary:
                    logger.error(f"Last FFmpeg errors for {stream_id}:\n{error_summary}")
        except Exception as e:
            logger.error(f"Error monitoring FFmpeg stderr for {stream_id}: {e}")
    
    def _stop_stream_internal(self, stream_id: str):
        """Internal method to stop stream without lock (called from within locked context)"""
        if stream_id not in self.active_streams:
            return
        
        stream_info = self.active_streams[stream_id]
        process = stream_info['process']
        
        # Terminate ffmpeg process gracefully
        try:
            # Try graceful termination first
            if hasattr(os, 'killpg'):
                try:
                    os.killpg(os.getpgid(process.pid), 15)  # SIGTERM to process group
                except:
                    process.terminate()
            else:
                process.terminate()
            
            # Wait for termination
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                logger.warning(f"Stream {stream_id} did not terminate gracefully, killing...")
                if hasattr(os, 'killpg'):
                    try:
                        os.killpg(os.getpgid(process.pid), 9)  # SIGKILL
                    except:
                        process.kill()
                else:
                    process.kill()
                process.wait()
        except ProcessLookupError:
            # Process already dead
            pass
        except Exception as e:
            logger.error(f"Error stopping stream {stream_id}: {e}")
        
        # Clean up segments
        try:
            stream_dir = self.output_dir / stream_id
            if stream_dir.exists():
                for file in stream_dir.glob("*.ts"):
                    try:
                        file.unlink()
                    except:
                        pass
                playlist = stream_dir / "stream.m3u8"
                if playlist.exists():
                    try:
                        playlist.unlink()
                    except:
                        pass
        except Exception as e:
            logger.warning(f"Error cleaning up segments for {stream_id}: {e}")
        
        # Remove from active streams
        del self.active_streams[stream_id]
    
    def stop_stream(self, stream_id: str) -> bool:
        """
        Stop a running stream
        
        Args:
            stream_id: Unique identifier of the stream to stop
            
        Returns:
            True if stream was stopped, False if stream not found
        """
        with self._lock:
            if stream_id not in self.active_streams:
                logger.warning(f"Stream {stream_id} not found")
                return False
            
            self._stop_stream_internal(stream_id)
            logger.info(f"Stopped stream {stream_id}")
            return True
    
    def is_stream_active(self, stream_id: str) -> bool:
        """
        Check if a stream is currently active
        
        Args:
            stream_id: Stream identifier to check
            
        Returns:
            True if stream is running, False otherwise
        """
        if stream_id not in self.active_streams:
            return False
        
        process = self.active_streams[stream_id]['process']
        return process.poll() is None
    
    def get_stream_info(self, stream_id: str) -> Optional[Dict]:
        """
        Get information about a stream
        
        Args:
            stream_id: Stream identifier
            
        Returns:
            Dictionary with stream info or None if not found
        """
        if stream_id not in self.active_streams:
            return None
        
        stream_info = self.active_streams[stream_id]
        
        # Check playlist freshness
        playlist_path = self.output_dir / stream_id / "stream.m3u8"
        last_segment_age = None
        if playlist_path.exists():
            last_segment_age = time.time() - playlist_path.stat().st_mtime
        
        return {
            'stream_id': stream_id,
            'uri': stream_info['uri'],
            'started_at': stream_info['started_at'],
            'uptime': time.time() - stream_info['started_at'],
            'is_active': self.is_stream_active(stream_id),
            'playlist_url': f"/{stream_info['playlist']}",
            'last_segment_age': last_segment_age,
            'health_check_count': stream_info.get('health_check_count', 0),
            'reconnect_count': stream_info.get('reconnect_count', 0),
            'quality': stream_info.get('quality', 'auto'),
            'max_bitrate': stream_info.get('max_bitrate')
        }
    
    def get_all_streams(self) -> Dict[str, Dict]:
        """
        Get information about all active streams
        
        Returns:
            Dictionary mapping stream_id to stream info
        """
        return {
            stream_id: self.get_stream_info(stream_id)
            for stream_id in self.active_streams.keys()
        }
    
    def stop_all_streams(self):
        """Stop all active streams"""
        with self._lock:
            stream_ids = list(self.active_streams.keys())
            for stream_id in stream_ids:
                self._stop_stream_internal(stream_id)
        
        logger.info(f"Stopped all {len(stream_ids)} streams")
    
    def cleanup_dead_streams(self):
        """Remove dead streams from active streams registry"""
        with self._lock:
            dead_streams = []
            for stream_id in list(self.active_streams.keys()):
                if not self.is_stream_active(stream_id):
                    dead_streams.append(stream_id)
            
            for stream_id in dead_streams:
                logger.warning(f"Cleaning up dead stream: {stream_id}")
                self._stop_stream_internal(stream_id)
            
            return len(dead_streams)
    
    def cleanup_old_segments(self, max_age_minutes: int = 5):
        """
        Clean up old HLS segments (more aggressive cleanup for performance)
        
        Args:
            max_age_minutes: Remove segments older than this many minutes (default: 5)
        """
        cutoff_time = time.time() - (max_age_minutes * 60)
        cleaned = 0
        
        for stream_dir in self.output_dir.iterdir():
            if not stream_dir.is_dir():
                continue
            
            # Check if stream is still active
            stream_id = stream_dir.name
            is_active = stream_id in self.active_streams and self.is_stream_active(stream_id)
            
            # Remove old segments
            for file in stream_dir.glob("*.ts"):
                try:
                    if file.stat().st_mtime < cutoff_time:
                        file.unlink()
                        cleaned += 1
                except Exception as e:
                    logger.debug(f"Error removing segment {file}: {e}")
            
            # Remove empty directories (only if stream is not active)
            if not is_active:
                try:
                    if not any(stream_dir.iterdir()):
                        stream_dir.rmdir()
                except:
                    pass
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old segments")
        
        return cleaned
    
    def shutdown(self):
        """Shutdown stream manager and cleanup"""
        self._health_check_running = False
        self.stop_all_streams()
        if self._health_check_thread:
            self._health_check_thread.join(timeout=5)


# Global stream manager instance
stream_manager = StreamManager()
