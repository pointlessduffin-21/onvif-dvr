# ONVIF Profile Support Configuration

This document describes the ONVIF profiles supported by this viewer and their implementation status.

## Profile S - Video Streaming

**Status:** ✅ Implemented

**Features:**
- Video encoder configuration
- Video source configuration
- Real-time video streaming via RTSP
- Multiple video profiles support
- Resolution and framerate configuration
- Codec support (H.264, H.265, MJPEG)

**Implementation:**
- `onvif_manager.py`: `get_stream_uri()`, `get_profiles()`
- `app.py`: `/api/cameras/<id>/streams` endpoint
- `viewer.html`: Video player with stream selection

## Profile G - Video Recording and Storage

**Status:** ✅ Implemented

**Features:**
- Recording management
- Recording search and playback
- Storage configuration
- Track information

**Implementation:**
- `database.py`: `recordings` table
- `onvif_manager.py`: `get_recordings()`
- `app.py`: `/api/recordings` endpoints
- `recordings.html`: Recording management interface

## Profile C - Physical Access Control

**Status:** ✅ Implemented

**Features:**
- Access point management
- Physical access control
- Door control
- Access decision handling

**Implementation:**
- `database.py`: `access_control`, `access_events` tables
- `onvif_manager.py`: `get_access_control_info()`
- `app.py`: `/api/access-control` endpoints
- `access_control.html`: Access control interface

## Profile A - Access Control Configuration

**Status:** ✅ Implemented

**Features:**
- Broader access control configuration
- Credential management
- Access point configuration
- Event handling for access control

**Implementation:**
- Integrated with Profile C implementation
- Extended access control capabilities
- Configuration management

## Profile T - Advanced Video Streaming

**Status:** ✅ Implemented

**Features:**
- Advanced streaming configurations
- Multiple stream types (RTP-Unicast, RTP-Multicast)
- Transport protocol selection
- Stream setup configuration

**Implementation:**
- `onvif_manager.py`: `get_stream_uri()` with protocol selection
- Support for various streaming protocols
- Advanced encoder settings

## Profile M - Metadata and Events

**Status:** ✅ Implemented

**Features:**
- Event handling and subscription
- Metadata streaming
- Analytics configuration
- Event properties and topics

**Implementation:**
- `database.py`: `events`, `analytics_configs` tables
- `onvif_manager.py`: `get_events()`, `get_analytics_configs()`
- `app.py`: `/api/events`, `/api/analytics` endpoints
- `events.html`: Events and analytics interface

## Profile D - Access Control Peripherals

**Status:** ✅ Implemented

**Features:**
- Door control
- Input/Output device management
- Peripheral device configuration
- Status monitoring

**Implementation:**
- `database.py`: `peripherals` table
- `onvif_manager.py`: `get_peripherals()`
- `app.py`: `/api/peripherals` endpoints
- `access_control.html`: Peripherals section

## Additional Features

### PTZ Control
- Pan, Tilt, Zoom controls
- Preset management
- Continuous and absolute movements

### Multi-Camera Support
- Simultaneous camera connections
- Camera discovery
- Device information retrieval

### Web Interface
- Responsive Bootstrap design
- Real-time updates
- Dashboard with statistics
- Camera management
- Event monitoring

## Technical Stack

- **Backend:** Python 3.x, Flask
- **ONVIF Library:** onvif-zeep
- **Database:** SQLite
- **Frontend:** Bootstrap 5, jQuery
- **Video:** HTML5 Video Player

## Notes

1. **RTSP Streaming:** Direct RTSP streaming in browsers requires additional setup (e.g., ffmpeg for HLS/DASH conversion)
2. **WebRTC:** For lower latency, consider implementing WebRTC gateway
3. **Recording:** Server-side recording requires additional video processing libraries
4. **Events:** Real-time event subscriptions use ONVIF event service
5. **Discovery:** WS-Discovery for automatic camera detection may require additional network configuration
