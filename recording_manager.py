"""
ONVIF Recording Manager - Profile G Support
Handles recording search and playback from ONVIF devices with DVR/NVR storage
"""
from onvif import ONVIFCamera
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecordingManager:
    def __init__(self):
        """Initialize the Recording Manager"""
        self.cameras = {}  # Cache of ONVIF camera connections
    
    def get_camera(self, host: str, port: int, username: str, password: str) -> ONVIFCamera:
        """
        Get or create ONVIF camera connection
        
        Args:
            host: Camera IP address
            port: ONVIF port
            username: Username
            password: Password
            
        Returns:
            ONVIFCamera instance
        """
        cache_key = f"{host}:{port}"
        
        if cache_key not in self.cameras:
            try:
                # Auto-detect WSDL path
                import os
                import sys
                
                # Try common WSDL locations
                possible_paths = [
                    '/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/wsdl/',
                    '/usr/local/lib/python3.13/site-packages/wsdl/',
                    os.path.join(sys.prefix, 'lib', f'python{sys.version_info.major}.{sys.version_info.minor}', 'site-packages', 'wsdl'),
                ]
                
                wsdl_path = None
                for path in possible_paths:
                    if os.path.exists(os.path.join(path, 'devicemgmt.wsdl')):
                        wsdl_path = path
                        break
                
                if not wsdl_path:
                    raise Exception("Could not find WSDL files")
                
                camera = ONVIFCamera(
                    host, port, username, password,
                    wsdl_path
                )
                self.cameras[cache_key] = camera
            except Exception as e:
                logger.error(f"Failed to connect to camera {cache_key}: {e}")
                raise
        
        return self.cameras[cache_key]
    
    def search_recordings(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        start_time: datetime,
        end_time: datetime,
        recording_token: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for recordings in a time range
        
        Args:
            host: Camera IP
            port: ONVIF port
            username: Username
            password: Password
            start_time: Search start time
            end_time: Search end time
            recording_token: Optional specific recording to search
            
        Returns:
            List of recording segments with metadata
        """
        try:
            camera = self.get_camera(host, port, username, password)
            
            # Create search service
            search_service = camera.create_search_service()
            
            # Get recording search parameters
            search_params = {
                'StartPoint': start_time.isoformat(),
                'EndPoint': end_time.isoformat(),
                'MaxMatches': 100,
                'KeepAliveTime': timedelta(seconds=30)
            }
            
            if recording_token:
                search_params['RecordingSourceFilter'] = {
                    'Token': recording_token
                }
            
            # Start search
            search_result = search_service.FindRecordings(
                Scope={'RecordingInformationFilter': search_params}
            )
            
            search_token = search_result.SearchToken
            
            # Get search results
            results = []
            while True:
                search_state = search_service.GetRecordingSearchResults(
                    SearchToken=search_token,
                    MinResults=1,
                    MaxResults=50,
                    WaitTime=timedelta(seconds=5)
                )
                
                if hasattr(search_state, 'RecordingInformation'):
                    for rec_info in search_state.RecordingInformation:
                        results.append({
                            'recording_token': rec_info.RecordingToken,
                            'source': rec_info.Source.Name if hasattr(rec_info, 'Source') else None,
                            'earliest_recording': rec_info.EarliestRecording,
                            'latest_recording': rec_info.LatestRecording,
                            'content': rec_info.Content if hasattr(rec_info, 'Content') else None
                        })
                
                # Check if search is complete
                if search_state.SearchState == 'Completed':
                    break
            
            # End search
            search_service.EndSearch(SearchToken=search_token)
            
            return results
            
        except Exception as e:
            logger.error(f"Recording search failed: {e}")
            return []
    
    def get_recording_summary(
        self,
        host: str,
        port: int,
        username: str,
        password: str
    ) -> Dict:
        """
        Get summary of available recordings
        
        Args:
            host: Camera IP
            port: ONVIF port
            username: Username
            password: Password
            
        Returns:
            Recording summary information
        """
        try:
            camera = self.get_camera(host, port, username, password)
            
            # Create recording service
            recording_service = camera.create_recording_service()
            
            # Get recordings
            recordings = recording_service.GetRecordings()
            
            summary = {
                'total_recordings': len(recordings) if recordings else 0,
                'recordings': []
            }
            
            if recordings:
                for recording in recordings:
                    rec_info = {
                        'token': recording.RecordingToken,
                        'name': recording.Configuration.Name if hasattr(recording, 'Configuration') else None,
                        'source': recording.Configuration.Source.SourceId if hasattr(recording, 'Configuration') else None,
                        'content': recording.Configuration.Content if hasattr(recording, 'Configuration') else None
                    }
                    
                    # Get track information if available
                    if hasattr(recording, 'Tracks') and recording.Tracks:
                        rec_info['tracks'] = []
                        for track in recording.Tracks:
                            track_info = {
                                'token': track.TrackToken,
                                'type': track.TrackType,
                                'description': track.Description if hasattr(track, 'Description') else None
                            }
                            rec_info['tracks'].append(track_info)
                    
                    summary['recordings'].append(rec_info)
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get recording summary: {e}")
            return {'total_recordings': 0, 'recordings': [], 'error': str(e)}
    
    def get_recording_uri(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        recording_token: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Optional[str]:
        """
        Get URI for playback of a recording
        
        Args:
            host: Camera IP
            port: ONVIF port
            username: Username
            password: Password
            recording_token: Recording identifier
            start_time: Optional playback start time
            end_time: Optional playback end time
            
        Returns:
            RTSP URI for recording playback
        """
        try:
            camera = self.get_camera(host, port, username, password)
            
            # Create replay service
            replay_service = camera.create_replay_service()
            
            # Build stream setup request
            stream_setup = {
                'Stream': 'RTP-Unicast',
                'Transport': {
                    'Protocol': 'RTSP'
                }
            }
            
            # Get replay URI
            replay_config = {
                'RecordingToken': recording_token
            }
            
            if start_time:
                replay_config['StartTime'] = start_time.isoformat()
            if end_time:
                replay_config['EndTime'] = end_time.isoformat()
            
            response = replay_service.GetReplayUri(
                StreamSetup=stream_setup,
                RecordingToken=recording_token
            )
            
            return response.Uri
            
        except Exception as e:
            logger.error(f"Failed to get recording URI: {e}")
            return None
    
    def get_available_recordings_by_channel(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        days_back: int = 7
    ) -> Dict[str, List[Dict]]:
        """
        Get available recordings organized by channel
        
        Args:
            host: Camera IP
            port: ONVIF port
            username: Username
            password: Password
            days_back: Number of days to look back
            
        Returns:
            Dictionary mapping channel names to recording segments
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)
        
        recordings = self.search_recordings(
            host, port, username, password,
            start_time, end_time
        )
        
        # Organize by channel/source
        by_channel = {}
        for recording in recordings:
            source = recording.get('source', 'Unknown')
            if source not in by_channel:
                by_channel[source] = []
            by_channel[source].append(recording)
        
        return by_channel


# Global recording manager instance
recording_manager = RecordingManager()
