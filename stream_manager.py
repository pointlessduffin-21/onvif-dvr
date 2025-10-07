"""
RTSP to HLS Stream Manager using ffmpeg
Converts RTSP streams to HLS format for browser playback
"""
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamManager:
    def __init__(self, output_dir: str = "static/streams"):
        """
        Initialize the Stream Manager
        
        Args:
            output_dir: Directory to store HLS segments and playlists
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Dictionary to track active streams
        # Format: {stream_id: {'process': subprocess.Popen, 'uri': str, 'started_at': float}}
        self.active_streams: Dict[str, Dict] = {}
        
        # Lock for thread-safe operations
        self._lock = threading.Lock()
    
    def start_stream(self, stream_id: str, rtsp_uri: str, username: str = None, password: str = None) -> bool:
        """
        Start converting an RTSP stream to HLS
        
        Args:
            stream_id: Unique identifier for this stream
            rtsp_uri: RTSP URL to convert
            username: Optional RTSP username
            password: Optional RTSP password
            
        Returns:
            True if stream started successfully, False otherwise
        """
        with self._lock:
            # Check if stream already running
            if stream_id in self.active_streams:
                if self.is_stream_active(stream_id):
                    logger.info(f"Stream {stream_id} is already running, reusing existing stream")
                    # Return True with existing stream info instead of error
                    return True
                else:
                    # Clean up dead stream
                    logger.info(f"Cleaning up dead stream {stream_id}")
                    self._stop_stream_internal(stream_id)
            
            # Create output directory for this stream
            stream_dir = self.output_dir / stream_id
            stream_dir.mkdir(parents=True, exist_ok=True)
            
            # Build RTSP URI with authentication if provided
            if username and password:
                # Parse and inject credentials
                if '://' in rtsp_uri:
                    protocol, rest = rtsp_uri.split('://', 1)
                    rtsp_uri = f"{protocol}://{username}:{password}@{rest}"
            
            # Output playlist and segment pattern
            playlist_path = stream_dir / "stream.m3u8"
            segment_pattern = stream_dir / "segment_%03d.ts"
            
            # ffmpeg command for RTSP to HLS conversion
            # Optimized for low latency and browser compatibility
            cmd = [
                'ffmpeg',
                '-rtsp_transport', 'tcp',  # Use TCP for reliability
                '-i', rtsp_uri,
                '-c:v', 'copy',  # Copy video codec (no re-encoding for speed)
                '-c:a', 'aac',   # Convert audio to AAC for browser compatibility
                '-f', 'hls',     # HLS format
                '-hls_time', '2',  # 2-second segments
                '-hls_list_size', '10',  # Keep last 10 segments in playlist
                '-hls_flags', 'delete_segments+append_list',  # Clean up old segments
                '-hls_segment_filename', str(segment_pattern),
                '-start_number', '0',
                str(playlist_path)
            ]
            
            try:
                # Start ffmpeg process
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE
                )
                
                # Store stream info
                # Playlist path relative to project root for URL construction
                relative_playlist = f"static/streams/{stream_id}/stream.m3u8"
                
                self.active_streams[stream_id] = {
                    'process': process,
                    'uri': rtsp_uri,
                    'started_at': time.time(),
                    'playlist': relative_playlist
                }
                
                logger.info(f"Started stream {stream_id} from {rtsp_uri}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to start stream {stream_id}: {e}")
                return False
    
    def _stop_stream_internal(self, stream_id: str):
        """Internal method to stop stream without lock (called from within locked context)"""
        if stream_id not in self.active_streams:
            return
        
        stream_info = self.active_streams[stream_id]
        process = stream_info['process']
        
        # Terminate ffmpeg process
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning(f"Stream {stream_id} did not terminate, killing...")
            process.kill()
            process.wait()
        except Exception as e:
            logger.error(f"Error stopping stream {stream_id}: {e}")
        
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
        return {
            'stream_id': stream_id,
            'uri': stream_info['uri'],
            'started_at': stream_info['started_at'],
            'uptime': time.time() - stream_info['started_at'],
            'is_active': self.is_stream_active(stream_id),
            'playlist_url': f"/{stream_info['playlist']}"
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
        stream_ids = list(self.active_streams.keys())
        for stream_id in stream_ids:
            self.stop_stream(stream_id)
        
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
    
    def cleanup_old_segments(self, max_age_hours: int = 24):
        """
        Clean up old HLS segments
        
        Args:
            max_age_hours: Remove segments older than this many hours
        """
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        for stream_dir in self.output_dir.iterdir():
            if not stream_dir.is_dir():
                continue
            
            # Check if stream is still active
            if stream_dir.name in self.active_streams:
                continue
            
            # Remove old segments
            for file in stream_dir.iterdir():
                if file.stat().st_mtime < cutoff_time:
                    file.unlink()
                    logger.debug(f"Removed old segment: {file}")
            
            # Remove empty directories
            if not any(stream_dir.iterdir()):
                stream_dir.rmdir()
                logger.debug(f"Removed empty stream directory: {stream_dir}")


# Global stream manager instance
stream_manager = StreamManager()
