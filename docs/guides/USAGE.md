# ONVIF Viewer - User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Adding Cameras](#adding-cameras)
5. [Features](#features)
6. [Troubleshooting](#troubleshooting)

## Introduction

ONVIF Viewer is a comprehensive web-based application for managing and viewing IP cameras. In addition to full ONVIF profile coverage (streaming, recording, access control, analytics), it includes first-class connectors for industry-leading vendors like Hikvision (ISAPI), Dahua (CGI), and Axis (VAPIX).

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- ONVIF-compliant IP cameras on your network

### Setup Steps

1. **Clone or download the project**

2. **Run the setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Configure the application:**
   ```bash
   cp .env.example .env
   nano .env  # Edit configuration
   ```

4. **Start the application:**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

   Or manually:
   ```bash
   source venv/bin/activate
   python app.py
   ```

5. **Access the web interface:**
   - Open browser: `http://localhost:5000`

## Configuration

### Environment Variables (.env)

```
FLASK_APP=app.py
FLASK_ENV=development          # Use 'production' for production
SECRET_KEY=your-secret-key     # Change this to a random string
DATABASE_PATH=onvif_viewer.db  # SQLite database path
```

### Camera Requirements

Your cameras should:
- Be on the same network as the server
- Have ONVIF protocol enabled **or** expose one of the supported vendor APIs (Hikvision ISAPI, Dahua CGI, Axis VAPIX)
- Have valid credentials (username/password)
- Support at least Profile S (Streaming) or equivalent vendor RTSP endpoints

## Adding Cameras

### Method 1: Web Interface

1. Navigate to **Cameras** page
2. Click **Add Camera** button
3. Fill in camera details:
   - **Vendor:** Choose ONVIF, Hikvision, Dahua, or Axis
   - **Name:** Friendly name for the camera
   - **IP Address:** Camera's IP address
   - **Port:** ONVIF or vendor API port (defaults provided for each vendor)
   - **Username:** Camera username
   - **Password:** Camera password
4. Click **Add Camera**

The application will:
- Connect to the camera
- Retrieve device information
- Detect supported profiles
- Configure available streams

### Method 2: API

```bash
curl -X POST http://localhost:5000/api/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Front Door Camera",
    "host": "192.168.1.100",
    "port": 80,
    "username": "admin",
    "password": "password123",
    "vendor": "hikvision"
  }'
```

## Features

### Dashboard

The main dashboard displays:
- Total cameras and their status
- Active recordings count
- Recent events (24 hours)
- Camera grid with quick access

**Key Metrics:**
- 🎥 Total Cameras
- ✅ Online Cameras
- 🔴 Active Recordings
- 🔔 Recent Events

### Camera Management

**Features:**
- Add/Edit/Delete cameras
- View camera details
- Monitor connection status
- View supported profiles

**Supported Information:**
- Manufacturer and model
- Firmware version
- Serial number
- Available profiles

### Video Viewer (Profile S & T)

**Features:**
- Live video streaming
- Multiple stream selection
- Video quality control
- PTZ controls (if supported)
- Snapshot capture
- Recording control

**Controls:**
- ▶️ Play/Pause/Stop
- 📸 Take Snapshot
- 🔴 Start/Stop Recording
- 🎮 PTZ Controls (Pan/Tilt/Zoom)

**Stream Options:**
- Resolution selection
- Framerate control
- Bitrate adjustment
- Codec selection

### Recordings (Profile G)

**Features:**
- View all recordings
- Filter by status (Active/Completed)
- Recording playback
- Delete recordings
- Storage management

**Recording Information:**
- Start/End time
- Duration
- File size
- Camera name
- Status

### Access Control (Profile C & A)

**Features:**
- Access point management
- Physical access control
- Access event logging
- Real-time monitoring

**Access Points:**
- View access points
- Monitor status
- Configure settings
- Event history

**Access Events:**
- Event time
- Access point
- Decision (Granted/Denied)
- Credential information
- Reason logging

### Peripherals (Profile D)

**Features:**
- Door control devices
- Input/Output devices
- Status monitoring
- Configuration management

**Supported Devices:**
- 🚪 Doors
- 🔒 Locks
- 🔔 Readers
- ⚡ Relays

### Events & Analytics (Profile M)

**Features:**
- Real-time event monitoring
- Analytics configuration
- Event filtering
- Statistical dashboard

**Event Types:**
- Motion detection
- Analytics triggers
- System alerts
- Custom events

**Statistics:**
- Total events (24h)
- Motion events
- Alert events
- Analytics events

## Troubleshooting

### Camera Won't Connect

**Problem:** "Failed to connect to camera"

**Solutions:**
1. Verify camera IP address and port
2. Check network connectivity:
   ```bash
   ping <camera-ip>
   ```
3. Verify ONVIF is enabled on camera
4. Check credentials
5. Ensure camera and server are on same network

### No Video Stream

**Problem:** Video player shows no content

**Solutions:**
1. RTSP streams require additional setup
2. Use browser-compatible stream format
3. Consider using RTSP-to-HLS converter:
   ```bash
   ffmpeg -i rtsp://camera-url -c copy -f hls stream.m3u8
   ```
4. Check camera stream configuration
5. Verify profile support

### Database Errors

**Problem:** "Database is locked" or connection errors

**Solutions:**
1. Stop the application
2. Remove database file:
   ```bash
   rm onvif_viewer.db
   ```
3. Reinitialize:
   ```bash
   python init_db.py
   ```
4. Restart application

### Port Already in Use

**Problem:** "Address already in use"

**Solutions:**
1. Change port in app.py:
   ```python
   app.run(debug=True, host='0.0.0.0', port=5001)
   ```
2. Or kill existing process:
   ```bash
   lsof -ti:5000 | xargs kill -9
   ```

### Import Errors

**Problem:** "ModuleNotFoundError"

**Solutions:**
1. Activate virtual environment:
   ```bash
   source venv/bin/activate
   ```
2. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Advanced Configuration

### HTTPS Setup

For production, use HTTPS:

```python
# In app.py
if __name__ == '__main__':
    app.run(
        debug=False,
        host='0.0.0.0',
        port=5000,
        ssl_context=('cert.pem', 'key.pem')
    )
```

### Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name onvif-viewer.local;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Database Backup

```bash
# Backup
cp onvif_viewer.db onvif_viewer.db.backup

# Restore
cp onvif_viewer.db.backup onvif_viewer.db
```

## API Reference

### Cameras
- `GET /api/cameras` - List all cameras
- `POST /api/cameras` - Add camera
- `GET /api/cameras/<id>` - Get camera details
- `PUT /api/cameras/<id>` - Update camera
- `DELETE /api/cameras/<id>` - Delete camera

### Streams
- `GET /api/cameras/<id>/streams` - Get camera streams
- `GET /api/cameras/<id>/profiles` - Get camera profiles

### Recordings
- `GET /api/recordings` - List all recordings
- `GET /api/cameras/<id>/recordings` - Get camera recordings
- `POST /api/cameras/<id>/recordings/start` - Start recording
- `POST /api/recordings/<id>/stop` - Stop recording

### Access Control
- `GET /api/access-control` - List access points
- `GET /api/access-events` - List access events
- `GET /api/cameras/<id>/access-control` - Get camera access points

### Events
- `GET /api/events` - List events
- `GET /api/cameras/<id>/events` - Get camera events
- `GET /api/cameras/<id>/analytics` - Get analytics configs

### Peripherals
- `GET /api/peripherals` - List all peripherals
- `GET /api/cameras/<id>/peripherals` - Get camera peripherals

## Support

For issues and questions:
1. Check this guide
2. Review PROFILES.md for feature details
3. Check console logs for errors
4. Verify camera compatibility

## License

MIT License - See LICENSE file for details
