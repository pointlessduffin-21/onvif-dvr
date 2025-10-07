# ONVIF Viewer - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Browser (Client)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │Dashboard │  │ Cameras  │  │  Viewer  │  │  Events  │  ...  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼──────────────┘
        │             │             │             │
        │ AJAX/REST API Calls                     │
        │             │             │             │
┌───────▼─────────────▼─────────────▼─────────────▼──────────────┐
│                    Flask Application (app.py)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     API Routes                            │  │
│  │  /api/cameras  /api/recordings  /api/events  /api/...   │  │
│  └────┬───────────────────┬───────────────┬─────────────────┘  │
│       │                   │               │                     │
│  ┌────▼──────────┐  ┌────▼───────┐  ┌───▼────────┐           │
│  │  ONVIF        │  │  Database  │  │  Business  │           │
│  │  Manager      │  │  Layer     │  │  Logic     │           │
│  └────┬──────────┘  └────┬───────┘  └────────────┘           │
└───────┼──────────────────┼──────────────────────────────────┘
        │                  │
        │                  │ SQL Queries
        │                  │
        │            ┌─────▼─────┐
        │            │  SQLite   │
        │            │  Database │
        │            └───────────┘
        │
        │ ONVIF Protocol (SOAP/XML over HTTP)
        │
┌───────▼──────────────────────────────────────────────────────┐
│                    ONVIF Cameras Network                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Camera 1 │  │ Camera 2 │  │ Camera 3 │  │ Camera N │     │
│  │ Profile  │  │ Profile  │  │ Profile  │  │ Profile  │     │
│  │ S,G,T    │  │ S,G,C,A  │  │ S,M,D    │  │ S,G,...  │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
└───────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Camera Addition Flow

```
User Browser
    │
    │ 1. POST /api/cameras {host, username, password}
    ▼
Flask API
    │
    │ 2. Create ONVIFCamera instance
    ▼
ONVIF Manager
    │
    │ 3. Connect via ONVIF protocol
    ▼
Camera Device
    │
    │ 4. Return device info, profiles, capabilities
    ▼
ONVIF Manager
    │
    │ 5. Parse and structure data
    ▼
Database Layer
    │
    │ 6. INSERT camera, profiles, streams
    ▼
SQLite Database
    │
    │ 7. Return success + camera_id
    ▼
Flask API
    │
    │ 8. JSON response
    ▼
User Browser
    │
    └─ Display success message
```

### 2. Video Streaming Flow

```
User Browser
    │
    │ 1. GET /api/cameras/1/streams
    ▼
Flask API
    │
    │ 2. Query database for camera
    ▼
Database Layer
    │
    │ 3. Return camera credentials
    ▼
ONVIF Manager
    │
    │ 4. Request stream URI
    ▼
Camera Device
    │
    │ 5. Return RTSP URL
    ▼
Flask API
    │
    │ 6. Return stream URL
    ▼
User Browser
    │
    │ 7. Connect to RTSP stream
    │    (requires additional conversion for browser)
    ▼
Camera Device
    │
    └─ Stream video data
```

### 3. Event Monitoring Flow

```
Camera Device
    │
    │ 1. Event occurs (motion, access, etc.)
    ▼
ONVIF Event Service
    │
    │ 2. Event notification (pull/subscription)
    ▼
ONVIF Manager
    │
    │ 3. Parse event data
    ▼
Database Layer
    │
    │ 4. INSERT event record
    ▼
SQLite Database
    │
    │ 5. AJAX polling or WebSocket push
    ▼
User Browser
    │
    └─ Update event list in real-time
```

## Component Details

### Frontend (Browser)

**Technologies:**
- HTML5, CSS3, JavaScript
- Bootstrap 5 (UI framework)
- jQuery (AJAX, DOM manipulation)
- Bootstrap Icons

**Pages:**
- `index.html` - Dashboard with statistics
- `cameras.html` - Camera CRUD operations
- `viewer.html` - Live video viewer with controls
- `recordings.html` - Recording management
- `access_control.html` - Access control interface
- `events.html` - Event monitoring and analytics

### Backend (Flask)

**Core Files:**
- `app.py` - Main Flask application, routes, API endpoints
- `onvif_manager.py` - ONVIF protocol communication
- `database.py` - Database utilities and initialization

**API Structure:**
```
/api/
├── cameras/
│   ├── GET, POST /
│   ├── GET, PUT, DELETE /<id>
│   ├── GET /<id>/streams
│   ├── GET /<id>/profiles
│   ├── GET /<id>/recordings
│   └── POST /<id>/recordings/start
├── recordings/
│   ├── GET /
│   └── POST /<id>/stop
├── access-control/
│   ├── GET /
│   └── GET /cameras/<id>/access-control
├── events/
│   ├── GET /
│   └── GET /cameras/<id>/events
└── peripherals/
    ├── GET /
    └── GET /cameras/<id>/peripherals
```

### Database (SQLite)

**Tables:**
1. `cameras` - Camera configurations
2. `camera_profiles` - ONVIF media profiles
3. `video_streams` - Stream URIs and configs
4. `recordings` - Recording metadata
5. `access_control` - Access points
6. `access_events` - Access event logs
7. `peripherals` - Peripheral devices
8. `events` - General event logs
9. `analytics_configs` - Analytics configurations
10. `ptz_presets` - PTZ preset positions

### ONVIF Communication

**Protocol:** SOAP over HTTP
**Library:** onvif-zeep (Python)

**Services Used:**
- Device Management Service
- Media Service
- PTZ Service
- Event Service
- Recording Service
- Access Control Service
- Door Control Service
- Analytics Service

## Profile Implementation Map

```
┌─────────────────────────────────────────────────────────────┐
│                    ONVIF Profiles                            │
├─────────────────────────────────────────────────────────────┤
│ Profile S (Streaming)                                        │
│   ├─ Video encoder configuration                            │
│   ├─ Video source configuration                             │
│   ├─ Stream URI generation                                  │
│   └─ Real-time RTSP streaming                               │
├─────────────────────────────────────────────────────────────┤
│ Profile G (Recording)                                        │
│   ├─ Recording management                                   │
│   ├─ Recording search                                       │
│   ├─ Track management                                       │
│   └─ Storage configuration                                  │
├─────────────────────────────────────────────────────────────┤
│ Profile C (Physical Access)                                 │
│   ├─ Access point management                                │
│   ├─ Door control                                           │
│   └─ Physical access events                                 │
├─────────────────────────────────────────────────────────────┤
│ Profile A (Access Control Config)                           │
│   ├─ Credential management                                  │
│   ├─ Access policy configuration                            │
│   └─ Access control events                                  │
├─────────────────────────────────────────────────────────────┤
│ Profile T (Advanced Streaming)                              │
│   ├─ Advanced stream setup                                  │
│   ├─ Transport protocol selection                           │
│   └─ Stream type configuration                              │
├─────────────────────────────────────────────────────────────┤
│ Profile M (Metadata & Events)                               │
│   ├─ Event service                                          │
│   ├─ Metadata streaming                                     │
│   ├─ Analytics configuration                                │
│   └─ Event properties                                       │
├─────────────────────────────────────────────────────────────┤
│ Profile D (Peripherals)                                     │
│   ├─ Door control service                                   │
│   ├─ Peripheral device management                           │
│   └─ I/O device control                                     │
└─────────────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Security Layers                          │
├─────────────────────────────────────────────────────────────┤
│ 1. Application Layer                                         │
│    - Flask session management                                │
│    - CSRF protection (to be implemented)                     │
│    - Input validation                                        │
├─────────────────────────────────────────────────────────────┤
│ 2. Communication Layer                                       │
│    - HTTPS (production recommended)                          │
│    - CORS configuration                                      │
│    - Secure headers                                          │
├─────────────────────────────────────────────────────────────┤
│ 3. ONVIF Layer                                              │
│    - Username/password authentication                        │
│    - Digest authentication                                   │
│    - Encrypted communication (camera-dependent)              │
├─────────────────────────────────────────────────────────────┤
│ 4. Database Layer                                           │
│    - SQL injection prevention                                │
│    - Parameterized queries                                   │
│    - Password storage (consider encryption)                  │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

### Development
```
localhost:5000 → Flask Dev Server → SQLite
```

### Production (Recommended)
```
Internet
    ↓
Nginx (Reverse Proxy, SSL)
    ↓
Gunicorn (WSGI Server)
    ↓
Flask Application
    ↓
SQLite or PostgreSQL
```

## Network Topology

```
┌─────────────────────────────────────────────────────────────┐
│                    Corporate Network                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                 Camera Subnet                         │   │
│  │  192.168.1.0/24                                       │   │
│  │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                │   │
│  │  │Cam 1│  │Cam 2│  │Cam 3│  │Cam N│                │   │
│  │  └─────┘  └─────┘  └─────┘  └─────┘                │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                    │
│  ┌──────────────────────┼────────────────────────────────┐  │
│  │                 Network Switch                         │  │
│  └──────────────────────┼────────────────────────────────┘  │
│                          │                                    │
│  ┌──────────────────────▼────────────────────────────────┐  │
│  │            ONVIF Viewer Server                         │  │
│  │            192.168.1.100:5000                          │  │
│  └──────────────────────┬────────────────────────────────┘  │
│                          │                                    │
│  ┌──────────────────────▼────────────────────────────────┐  │
│  │                 Client Devices                         │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐               │  │
│  │  │ Desktop │  │ Laptop  │  │ Mobile  │               │  │
│  │  └─────────┘  └─────────┘  └─────────┘               │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Performance Considerations

- **Database**: SQLite is single-file, good for small deployments
- **Scalability**: Consider PostgreSQL for larger deployments
- **Caching**: Implement Redis for session/data caching
- **Load Balancing**: Use multiple Flask instances behind load balancer
- **Video Processing**: Offload RTSP conversion to separate service
- **Real-time Updates**: Implement WebSocket for live updates

## Future Enhancements

1. WebSocket integration for real-time updates
2. Video transcoding service (RTSP → HLS/DASH)
3. User authentication and authorization
4. Multi-tenant support
5. Cloud storage integration
6. Mobile application
7. Advanced analytics with AI/ML
8. Distributed deployment support
9. High availability setup
10. Monitoring and alerting system
