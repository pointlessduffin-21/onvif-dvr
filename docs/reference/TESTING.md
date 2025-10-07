# ONVIF Viewer Testing Guide

## Testing Without Physical Cameras

If you don't have physical ONVIF cameras available, here are several options for testing:

### 1. ONVIF Camera Simulators

#### Option A: ONVIF Device Tool
Download from ONVIF website (requires membership)

#### Option B: Happy Time ONVIF Server Simulator
- Free Windows-based ONVIF simulator
- Supports multiple profiles
- Simulates various camera types

#### Option C: ONVIF Camera Emulator (Python)
Create a simple test server:

```python
# test_camera_simulator.py
from onvif import ONVIFCamera
import time

# This would run on a separate machine or container
# Simulates basic ONVIF responses
```

### 2. Using Docker ONVIF Simulator

```bash
# Pull and run ONVIF simulator
docker run -d -p 8080:80 --name onvif-sim onvif/simulator

# Test connection
curl http://localhost:8080/onvif/device_service
```

### 3. Virtual Camera Software

For testing video streaming:

#### On macOS:
```bash
# Install OBS Studio
brew install --cask obs

# Or use FFmpeg to create virtual RTSP stream
ffmpeg -re -f lavfi -i testsrc=size=1280x720:rate=30 \
  -f rtsp rtsp://localhost:8554/test
```

## Manual Testing Checklist

### 1. Installation & Setup

- [ ] Clone repository
- [ ] Run `./setup.sh` successfully
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] .env file created
- [ ] Database initialized
- [ ] No errors in setup

### 2. Application Start

- [ ] Run `./start.sh` or `python app.py`
- [ ] Application starts without errors
- [ ] Port 5000 is accessible
- [ ] No import errors
- [ ] Database connection successful

### 3. Web Interface Access

- [ ] Open `http://localhost:5000`
- [ ] Dashboard loads
- [ ] Navigation menu visible
- [ ] All menu items accessible
- [ ] No console errors
- [ ] Bootstrap styles loaded
- [ ] Icons displayed correctly

### 4. Camera Management

#### Add Camera
- [ ] Click "Add Camera" button
- [ ] Modal opens correctly
- [ ] Form validation works
- [ ] Required fields enforced
- [ ] Port defaults to 80
- [ ] Profile information displayed

Test with dummy data:
```
Name: Test Camera
Host: 192.168.1.100
Port: 80
Username: admin
Password: admin123
```

#### List Cameras
- [ ] Cameras table displays
- [ ] Columns shown correctly
- [ ] Status badges visible
- [ ] Actions buttons work

#### Edit Camera
- [ ] Click edit button
- [ ] Modal opens with data
- [ ] Fields populated correctly
- [ ] Update works
- [ ] Changes reflected in list

#### Delete Camera
- [ ] Click delete button
- [ ] Confirmation dialog shows
- [ ] Camera removed after confirm
- [ ] Table updates

### 5. Video Viewer

- [ ] Navigate to viewer page
- [ ] Camera info loads
- [ ] Stream list displays
- [ ] Profile badges shown
- [ ] Video player visible
- [ ] Control buttons present
- [ ] PTZ controls (if applicable)

#### Player Controls
- [ ] Play button works
- [ ] Pause button works
- [ ] Stop button works
- [ ] Snapshot button works
- [ ] Record button toggles

#### PTZ Controls (if available)
- [ ] Up/Down buttons
- [ ] Left/Right buttons
- [ ] Zoom in/out
- [ ] Preset dropdown
- [ ] Stop button

### 6. Recordings

- [ ] Navigate to recordings page
- [ ] Table displays
- [ ] Filter buttons work
- [ ] Sort functionality
- [ ] Status badges visible
- [ ] Action buttons present

#### Recording Actions
- [ ] Start recording
- [ ] Stop recording
- [ ] Play recording
- [ ] Delete recording
- [ ] Duration formatted
- [ ] File size formatted

### 7. Access Control

- [ ] Navigate to access control page
- [ ] Access points list
- [ ] Peripherals list
- [ ] Events table
- [ ] Status indicators
- [ ] Real-time updates

#### Access Events
- [ ] Events display
- [ ] Time formatted
- [ ] Decision badges (granted/denied)
- [ ] Filtering works
- [ ] Auto-refresh working

### 8. Events & Analytics

- [ ] Navigate to events page
- [ ] Statistics cards display
- [ ] Numbers update
- [ ] Analytics list shown
- [ ] Event log table
- [ ] Filter buttons work

#### Event Filtering
- [ ] All events
- [ ] Motion events
- [ ] Alert events
- [ ] Analytics events
- [ ] Badge colors correct

### 9. API Testing

Test all endpoints using curl or Postman:

#### Get All Cameras
```bash
curl http://localhost:5000/api/cameras
```

#### Add Camera
```bash
curl -X POST http://localhost:5000/api/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Camera",
    "host": "192.168.1.100",
    "port": 80,
    "username": "admin",
    "password": "password"
  }'
```

#### Get Camera Details
```bash
curl http://localhost:5000/api/cameras/1
```

#### Get Streams
```bash
curl http://localhost:5000/api/cameras/1/streams
```

#### Get Recordings
```bash
curl http://localhost:5000/api/recordings
```

#### Get Events
```bash
curl http://localhost:5000/api/events
```

### 10. Database Testing

Verify database structure:

```bash
sqlite3 onvif_viewer.db

# Check tables
.tables

# Check cameras table
SELECT * FROM cameras;

# Check profiles
SELECT * FROM camera_profiles;

# Check streams
SELECT * FROM video_streams;

# Exit
.quit
```

### 11. Error Handling

Test error scenarios:

- [ ] Invalid camera credentials
- [ ] Unreachable camera IP
- [ ] Invalid port number
- [ ] Duplicate camera names
- [ ] Empty form submission
- [ ] Invalid API requests
- [ ] Database connection errors

### 12. Responsive Design

Test on different screen sizes:

- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)
- [ ] Navigation collapses on mobile
- [ ] Tables scroll horizontally
- [ ] Modals responsive
- [ ] Buttons properly sized

### 13. Browser Compatibility

Test in different browsers:

- [ ] Chrome/Chromium
- [ ] Safari
- [ ] Firefox
- [ ] Edge
- [ ] Mobile Safari
- [ ] Mobile Chrome

### 14. Performance Testing

- [ ] Dashboard loads in < 2s
- [ ] Camera list loads quickly
- [ ] No memory leaks
- [ ] AJAX requests complete
- [ ] No console errors
- [ ] Images load properly

### 15. Security Testing

- [ ] SQL injection attempts blocked
- [ ] XSS attempts sanitized
- [ ] CSRF protection (if implemented)
- [ ] Password not visible in network
- [ ] API endpoints secured

## Automated Testing

### Unit Tests (Future Implementation)

```python
# tests/test_onvif_manager.py
import unittest
from onvif_manager import ONVIFManager

class TestONVIFManager(unittest.TestCase):
    def test_connection(self):
        manager = ONVIFManager()
        # Test connection logic
        
    def test_get_profiles(self):
        # Test profile retrieval
        pass
```

### Integration Tests

```python
# tests/test_api.py
import unittest
from app import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        
    def test_get_cameras(self):
        response = self.app.get('/api/cameras')
        self.assertEqual(response.status_code, 200)
```

## Load Testing

Using Apache Bench:

```bash
# Test dashboard
ab -n 1000 -c 10 http://localhost:5000/

# Test API endpoint
ab -n 1000 -c 10 http://localhost:5000/api/cameras
```

## Test Data

### Sample Camera Configurations

```json
{
  "cameras": [
    {
      "name": "Front Door",
      "host": "192.168.1.100",
      "port": 80,
      "username": "admin",
      "password": "admin123"
    },
    {
      "name": "Back Yard",
      "host": "192.168.1.101",
      "port": 80,
      "username": "admin",
      "password": "admin123"
    },
    {
      "name": "Garage",
      "host": "192.168.1.102",
      "port": 8080,
      "username": "viewer",
      "password": "view123"
    }
  ]
}
```

## Known Limitations to Test

1. **RTSP Streaming**: Direct browser playback not supported
2. **Real-time Events**: Requires camera event support
3. **Recording**: Server-side recording needs additional setup
4. **Discovery**: Auto-discovery may require network configuration
5. **Authentication**: No user authentication implemented yet

## Reporting Issues

When reporting issues, include:

1. **Environment**:
   - OS version
   - Python version
   - Browser version

2. **Steps to reproduce**:
   - Exact actions taken
   - Expected result
   - Actual result

3. **Logs**:
   - Console output
   - Browser console errors
   - Network requests

4. **Screenshots**:
   - Error messages
   - UI issues

## Success Criteria

The application passes testing if:

- ✅ Installation completes without errors
- ✅ Application starts successfully
- ✅ All pages load without errors
- ✅ Camera CRUD operations work
- ✅ API endpoints return expected data
- ✅ Database operations succeed
- ✅ UI is responsive
- ✅ No console errors
- ✅ Basic security measures in place
- ✅ Documentation is clear

## Next Steps After Testing

1. Deploy to production server
2. Configure with real ONVIF cameras
3. Set up HTTPS
4. Implement authentication
5. Configure monitoring
6. Set up backups
7. Document camera configurations
8. Train users
9. Monitor performance
10. Gather feedback
