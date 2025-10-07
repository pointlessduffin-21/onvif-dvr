from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
import logging
from datetime import datetime, timedelta
from database import get_db_connection, init_db
from onvif_manager import ONVIFManager
from stream_manager import stream_manager
from recording_manager import recording_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
CORS(app)

# Initialize ONVIF manager
onvif_manager = ONVIFManager()

# Initialize database
init_db()

# Periodic cleanup of dead streams
import atexit
from threading import Thread, Event

cleanup_event = Event()

def periodic_cleanup():
    """Background thread to cleanup dead streams periodically"""
    while not cleanup_event.is_set():
        cleanup_event.wait(300)  # Check every 5 minutes
        if not cleanup_event.is_set():
            count = stream_manager.cleanup_dead_streams()
            if count > 0:
                logger.info(f"Periodic cleanup: removed {count} dead stream(s)")

# Start cleanup thread
cleanup_thread = Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()

def shutdown_cleanup():
    """Cleanup on shutdown"""
    cleanup_event.set()
    stream_manager.stop_all_streams()

atexit.register(shutdown_cleanup)

# ============================================================================
# Web Routes
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/cameras')
def cameras_page():
    """Cameras management page"""
    return render_template('cameras.html')

@app.route('/viewer/<int:camera_id>')
def viewer_page(camera_id):
    """Video viewer page"""
    return render_template('viewer.html', camera_id=camera_id)

@app.route('/grid')
def grid_page():
    """Multi-camera grid view"""
    return render_template('grid.html')

@app.route('/recordings')
def recordings_page():
    """Recordings page"""
    return render_template('recordings.html')

@app.route('/access-control')
def access_control_page():
    """Access control page"""
    return render_template('access_control.html')

@app.route('/events')
def events_page():
    """Events and analytics page"""
    return render_template('events.html')

# ============================================================================
# API Routes - Cameras
# ============================================================================

@app.route('/api/cameras', methods=['GET'])
def get_cameras():
    """Get all cameras"""
    conn = get_db_connection()
    cameras = conn.execute('SELECT * FROM cameras ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return jsonify([dict(camera) for camera in cameras])

@app.route('/api/cameras/<int:camera_id>', methods=['GET'])
def get_camera(camera_id):
    """Get camera by ID"""
    conn = get_db_connection()
    camera = conn.execute('SELECT * FROM cameras WHERE id = ?', (camera_id,)).fetchone()
    conn.close()
    
    if camera:
        return jsonify(dict(camera))
    return jsonify({'error': 'Camera not found'}), 404

@app.route('/api/cameras', methods=['POST'])
def add_camera():
    """Add new camera"""
    data = request.json
    
    # Connect to camera
    result = onvif_manager.connect_camera(
        data['host'],
        data.get('port', 80),
        data['username'],
        data['password']
    )
    
    if not result['success']:
        return jsonify({'error': result['error']}), 400
    
    # Save to database
    try:
        camera_id = onvif_manager.save_camera_to_db(
            {
                'name': data['name'],
                'host': data['host'],
                'port': data.get('port', 80),
                'username': data['username'],
                'password': data['password']
            },
            result['device_info'],
            result['profiles']
        )
        
        # Get stream URIs for all profiles
        camera = result['camera']
        conn = get_db_connection()
        
        for profile in result['profiles']:
            stream_uri = onvif_manager.get_stream_uri(camera, profile['token'])
            if stream_uri:
                conn.execute('''
                    INSERT INTO video_streams (camera_id, profile_token, stream_uri, 
                                              stream_type, protocol, resolution, codec)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    camera_id,
                    profile['token'],
                    stream_uri,
                    'RTP-Unicast',
                    'RTSP',
                    json.dumps(profile.get('video_encoder', {}).get('resolution', {})),
                    profile.get('video_encoder', {}).get('encoding', '')
                ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'camera_id': camera_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<int:camera_id>', methods=['PUT'])
def update_camera(camera_id):
    """Update camera"""
    data = request.json
    conn = get_db_connection()
    
    try:
        conn.execute('''
            UPDATE cameras 
            SET name = ?, host = ?, port = ?, username = ?, password = ?, updated_at = ?
            WHERE id = ?
        ''', (
            data['name'],
            data['host'],
            data.get('port', 80),
            data['username'],
            data['password'],
            datetime.now().isoformat(),
            camera_id
        ))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<int:camera_id>', methods=['DELETE'])
def delete_camera(camera_id):
    """Delete camera"""
    conn = get_db_connection()
    conn.execute('DELETE FROM cameras WHERE id = ?', (camera_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/cameras/refresh', methods=['POST'])
def refresh_cameras():
    """Refresh profiles and streams for cameras"""
    data = request.json or {}
    camera_ids = []

    if isinstance(data, dict):
        if 'camera_id' in data:
            try:
                camera_ids.append(int(data['camera_id']))
            except (TypeError, ValueError):
                pass
        if 'camera_ids' in data and isinstance(data['camera_ids'], list):
            for cid in data['camera_ids']:
                try:
                    camera_ids.append(int(cid))
                except (TypeError, ValueError):
                    continue

    camera_ids = list(dict.fromkeys(camera_ids)) if camera_ids else None

    conn = get_db_connection()

    try:
        if camera_ids:
            placeholders = ','.join('?' * len(camera_ids))
            cameras = conn.execute(
                f'SELECT * FROM cameras WHERE id IN ({placeholders}) ORDER BY id',
                tuple(camera_ids)
            ).fetchall()
        else:
            cameras = conn.execute('SELECT * FROM cameras ORDER BY id').fetchall()
    finally:
        conn.close()

    if not cameras:
        return jsonify({'refreshed': [], 'errors': ['No cameras found to refresh']}), 404

    refreshed = []
    errors = []

    for camera in cameras:
        try:
            result = onvif_manager.refresh_camera_profiles(camera)
            refreshed.append(result)
        except Exception as e:
            errors.append({
                'camera_id': camera['id'],
                'error': str(e)
            })
            logger.exception("Failed to refresh camera %s", camera['id'])

    status_code = 200 if refreshed else 500

    return jsonify({
        'refreshed': refreshed,
        'errors': errors
    }), status_code

# ============================================================================
# API Routes - Video Streaming (Profile S, T)
# ============================================================================

@app.route('/api/cameras/<int:camera_id>/streams', methods=['GET'])
def get_streams(camera_id):
    """Get video streams for camera"""
    conn = get_db_connection()
    streams = conn.execute(
        'SELECT * FROM video_streams WHERE camera_id = ?',
        (camera_id,)
    ).fetchall()
    conn.close()
    
    return jsonify([dict(stream) for stream in streams])

@app.route('/api/streams/overview', methods=['GET'])
def get_stream_overview():
    """Get first stream metadata for each camera"""
    conn = get_db_connection()
    cameras = conn.execute('SELECT id, name, host, port, status FROM cameras ORDER BY id').fetchall()

    overview = []
    for camera in cameras:
        stream = conn.execute(
            'SELECT profile_token, stream_type, protocol, resolution, framerate, bitrate, codec '
            'FROM video_streams WHERE camera_id = ? ORDER BY id ASC LIMIT 1',
            (camera['id'],)
        ).fetchone()

        stream_info = None
        if stream:
            stream_info = {
                'profile_token': stream['profile_token'],
                'stream_type': stream['stream_type'],
                'protocol': stream['protocol'],
                'resolution': stream['resolution'],
                'framerate': stream['framerate'],
                'bitrate': stream['bitrate'],
                'codec': stream['codec']
            }

        overview.append({
            'camera_id': camera['id'],
            'name': camera['name'],
            'host': camera['host'],
            'port': camera['port'],
            'status': camera['status'],
            'stream': stream_info
        })

    conn.close()

    return jsonify(overview)

@app.route('/api/cameras/<int:camera_id>/profiles', methods=['GET'])
def get_camera_profiles(camera_id):
    """Get camera profiles"""
    conn = get_db_connection()
    profiles = conn.execute(
        'SELECT * FROM camera_profiles WHERE camera_id = ?',
        (camera_id,)
    ).fetchall()
    conn.close()
    
    return jsonify([dict(profile) for profile in profiles])

# ============================================================================
# API Routes - Recordings (Profile G)
# ============================================================================

@app.route('/api/recordings', methods=['GET'])
def get_all_recordings():
    """Get all recordings"""
    conn = get_db_connection()
    recordings = conn.execute('''
        SELECT r.*, c.name as camera_name 
        FROM recordings r
        JOIN cameras c ON r.camera_id = c.id
        ORDER BY r.start_time DESC
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(recording) for recording in recordings])

@app.route('/api/cameras/<int:camera_id>/recordings', methods=['GET'])
def get_camera_recordings(camera_id):
    """Get recordings for specific camera"""
    conn = get_db_connection()
    recordings = conn.execute(
        'SELECT * FROM recordings WHERE camera_id = ? ORDER BY start_time DESC',
        (camera_id,)
    ).fetchall()
    conn.close()
    
    return jsonify([dict(recording) for recording in recordings])

@app.route('/api/cameras/<int:camera_id>/recordings/start', methods=['POST'])
def start_recording(camera_id):
    """Start recording"""
    # This would interact with the camera's recording service
    # Placeholder implementation
    return jsonify({'success': True, 'message': 'Recording started'})

@app.route('/api/recordings/<int:recording_id>/stop', methods=['POST'])
def stop_recording(recording_id):
    """Stop recording"""
    # This would interact with the camera's recording service
    # Placeholder implementation
    return jsonify({'success': True, 'message': 'Recording stopped'})

@app.route('/api/cameras/<int:camera_id>/recordings/search', methods=['POST'])
def search_camera_recordings(camera_id):
    """Search for recordings on camera's DVR/NVR (Profile G)"""
    data = request.json
    
    # Get camera info
    conn = get_db_connection()
    camera = conn.execute(
        'SELECT * FROM cameras WHERE id = ?',
        (camera_id,)
    ).fetchone()
    conn.close()
    
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    # Parse time range
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')
    
    try:
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        else:
            start_time = datetime.now() - timedelta(days=1)
        
        if end_time_str:
            end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
        else:
            end_time = datetime.now()
    except Exception as e:
        return jsonify({'error': f'Invalid time format: {e}'}), 400
    
    # Search recordings on device
    recordings = recording_manager.search_recordings(
        host=camera['host'],
        port=camera['port'],
        username=camera['username'],
        password=camera['password'],
        start_time=start_time,
        end_time=end_time,
        recording_token=data.get('recording_token')
    )
    
    return jsonify({
        'camera_id': camera_id,
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'total_results': len(recordings),
        'recordings': recordings
    })

@app.route('/api/cameras/<int:camera_id>/recordings/summary', methods=['GET'])
def get_camera_recording_summary(camera_id):
    """Get recording summary from camera's DVR/NVR"""
    # Get camera info
    conn = get_db_connection()
    camera = conn.execute(
        'SELECT * FROM cameras WHERE id = ?',
        (camera_id,)
    ).fetchone()
    conn.close()
    
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    # Get recording summary
    summary = recording_manager.get_recording_summary(
        host=camera['host'],
        port=camera['port'],
        username=camera['username'],
        password=camera['password']
    )
    
    return jsonify(summary)

@app.route('/api/recordings/playback-uri', methods=['POST'])
def get_recording_playback_uri():
    """Get RTSP URI for playing back a recording"""
    data = request.json
    
    camera_id = data.get('camera_id')
    recording_token = data.get('recording_token')
    
    if not camera_id or not recording_token:
        return jsonify({'error': 'camera_id and recording_token required'}), 400
    
    # Get camera info
    conn = get_db_connection()
    camera = conn.execute(
        'SELECT * FROM cameras WHERE id = ?',
        (camera_id,)
    ).fetchone()
    conn.close()
    
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    # Parse optional time range
    start_time = None
    end_time = None
    
    if data.get('start_time'):
        try:
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        except:
            pass
    
    if data.get('end_time'):
        try:
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        except:
            pass
    
    # Get playback URI
    uri = recording_manager.get_recording_uri(
        host=camera['host'],
        port=camera['port'],
        username=camera['username'],
        password=camera['password'],
        recording_token=recording_token,
        start_time=start_time,
        end_time=end_time
    )
    
    if uri:
        return jsonify({
            'success': True,
            'uri': uri,
            'recording_token': recording_token
        })
    else:
        return jsonify({'error': 'Failed to get recording URI'}), 500

# ============================================================================
# API Routes - Access Control (Profile C, A)
# ============================================================================

@app.route('/api/access-control', methods=['GET'])
def get_access_control():
    """Get all access control points"""
    conn = get_db_connection()
    access_points = conn.execute('''
        SELECT ac.*, c.name as camera_name 
        FROM access_control ac
        JOIN cameras c ON ac.camera_id = c.id
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(ap) for ap in access_points])

@app.route('/api/cameras/<int:camera_id>/access-control', methods=['GET'])
def get_camera_access_control(camera_id):
    """Get access control for specific camera"""
    conn = get_db_connection()
    access_points = conn.execute(
        'SELECT * FROM access_control WHERE camera_id = ?',
        (camera_id,)
    ).fetchall()
    conn.close()
    
    return jsonify([dict(ap) for ap in access_points])

@app.route('/api/access-events', methods=['GET'])
def get_access_events():
    """Get access control events"""
    conn = get_db_connection()
    events = conn.execute('''
        SELECT ae.*, c.name as camera_name 
        FROM access_events ae
        JOIN cameras c ON ae.camera_id = c.id
        ORDER BY ae.event_time DESC
        LIMIT 100
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(event) for event in events])

# ============================================================================
# API Routes - Events and Analytics (Profile M)
# ============================================================================

@app.route('/api/events', methods=['GET'])
def get_events():
    """Get events"""
    conn = get_db_connection()
    events = conn.execute('''
        SELECT e.*, c.name as camera_name 
        FROM events e
        JOIN cameras c ON e.camera_id = c.id
        ORDER BY e.event_time DESC
        LIMIT 100
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(event) for event in events])

@app.route('/api/cameras/<int:camera_id>/events', methods=['GET'])
def get_camera_events(camera_id):
    """Get events for specific camera"""
    conn = get_db_connection()
    events = conn.execute(
        'SELECT * FROM events WHERE camera_id = ? ORDER BY event_time DESC LIMIT 100',
        (camera_id,)
    ).fetchall()
    conn.close()
    
    return jsonify([dict(event) for event in events])

@app.route('/api/cameras/<int:camera_id>/analytics', methods=['GET'])
def get_camera_analytics(camera_id):
    """Get analytics configurations for camera"""
    conn = get_db_connection()
    analytics = conn.execute(
        'SELECT * FROM analytics_configs WHERE camera_id = ?',
        (camera_id,)
    ).fetchall()
    conn.close()
    
    return jsonify([dict(config) for config in analytics])

# ============================================================================
# API Routes - Peripherals (Profile D)
# ============================================================================

@app.route('/api/peripherals', methods=['GET'])
def get_all_peripherals():
    """Get all peripherals"""
    conn = get_db_connection()
    peripherals = conn.execute('''
        SELECT p.*, c.name as camera_name 
        FROM peripherals p
        JOIN cameras c ON p.camera_id = c.id
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(peripheral) for peripheral in peripherals])

@app.route('/api/cameras/<int:camera_id>/peripherals', methods=['GET'])
def get_camera_peripherals(camera_id):
    """Get peripherals for specific camera"""
    conn = get_db_connection()
    peripherals = conn.execute(
        'SELECT * FROM peripherals WHERE camera_id = ?',
        (camera_id,)
    ).fetchall()
    conn.close()
    
    return jsonify([dict(peripheral) for peripheral in peripherals])

# ============================================================================
# API Routes - PTZ Control
# ============================================================================

@app.route('/api/cameras/<int:camera_id>/ptz/presets', methods=['GET'])
def get_ptz_presets(camera_id):
    """Get PTZ presets"""
    conn = get_db_connection()
    presets = conn.execute(
        'SELECT * FROM ptz_presets WHERE camera_id = ?',
        (camera_id,)
    ).fetchall()
    conn.close()
    
    return jsonify([dict(preset) for preset in presets])

# ============================================================================
# Streaming Endpoints
# ============================================================================

@app.route('/api/streams/start', methods=['POST'])
def start_stream():
    """Start streaming an RTSP feed to HLS"""
    data = request.json
    
    camera_id = data.get('camera_id')
    profile_token = data.get('profile_token')
    
    if not camera_id or not profile_token:
        return jsonify({'error': 'camera_id and profile_token required'}), 400
    
    # Get camera and stream info from database
    conn = get_db_connection()
    
    # Get camera credentials
    camera = conn.execute(
        'SELECT * FROM cameras WHERE id = ?',
        (camera_id,)
    ).fetchone()
    
    if not camera:
        conn.close()
        return jsonify({'error': 'Camera not found'}), 404
    
    # Get stream URI
    stream = conn.execute(
        'SELECT * FROM video_streams WHERE camera_id = ? AND profile_token = ?',
        (camera_id, profile_token)
    ).fetchone()
    
    conn.close()
    
    if not stream:
        return jsonify({'error': 'Stream not found'}), 404
    
    # Create unique stream ID
    stream_id = f"camera{camera_id}_{profile_token}"
    
    # Check if stream is already running
    existing_stream = stream_manager.get_stream_info(stream_id)
    if existing_stream and existing_stream['is_active']:
        # Stream already running, return existing info
        return jsonify({
            'success': True,
            'stream_id': stream_id,
            'playlist_url': existing_stream['playlist_url'],
            'already_running': True,
            'uptime': existing_stream['uptime']
        })
    
    # Start the stream
    success = stream_manager.start_stream(
        stream_id=stream_id,
        rtsp_uri=stream['stream_uri'],
        username=camera['username'],
        password=camera['password']
    )
    
    if success:
        stream_info = stream_manager.get_stream_info(stream_id)
        return jsonify({
            'success': True,
            'stream_id': stream_id,
            'playlist_url': stream_info['playlist_url'],
            'already_running': False
        })
    else:
        return jsonify({'error': 'Failed to start stream'}), 500

@app.route('/api/streams/stop', methods=['POST'])
def stop_stream():
    """Stop a streaming session"""
    data = request.json
    stream_id = data.get('stream_id')
    
    if not stream_id:
        return jsonify({'error': 'stream_id required'}), 400
    
    success = stream_manager.stop_stream(stream_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Stream not found'}), 404

@app.route('/api/streams/status/<stream_id>')
def stream_status(stream_id):
    """Get status of a stream"""
    stream_info = stream_manager.get_stream_info(stream_id)
    
    if stream_info:
        return jsonify(stream_info)
    else:
        return jsonify({'error': 'Stream not found'}), 404

@app.route('/api/streams/all')
def all_streams():
    """Get all active streams"""
    streams = stream_manager.get_all_streams()
    return jsonify(streams)

@app.route('/api/streams/cleanup', methods=['POST'])
def cleanup_streams():
    """Clean up dead streams"""
    count = stream_manager.cleanup_dead_streams()
    return jsonify({
        'success': True,
        'cleaned_up': count,
        'message': f'Cleaned up {count} dead stream(s)'
    })

# Serve HLS playlist and segments
@app.route('/static/streams/<path:filename>')
def serve_stream(filename):
    """Serve HLS playlists and segments"""
    return send_from_directory('static/streams', filename)

# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=8821)
    finally:
        # Cleanup streams on shutdown
        stream_manager.stop_all_streams()
