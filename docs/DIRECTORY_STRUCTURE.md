# Directory Structure

This document describes the organized structure of the ONVIF DVR project.

## Root Directory

The root directory contains only essential files for running the application:

```
onvif-dvr/
├── README.md                 # Main project documentation
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker container definition
├── docker-compose.yml        # Docker Compose configuration
├── setup.sh                  # Setup script
├── start.sh                  # Start script
│
├── app.py                    # Main Flask application
├── database.py               # Database utilities
├── init_db.py                # Database initialization
├── onvif_manager.py          # ONVIF protocol manager
├── recording_manager.py      # Recording management (Profile G)
├── stream_manager.py         # RTSP to HLS stream manager
│
├── camera_providers/         # Vendor-specific integrations
│   ├── __init__.py
│   ├── base.py              # Abstract base provider
│   ├── dahua.py             # Dahua camera provider
│   ├── hikvision.py         # Hikvision camera provider
│   └── axis.py              # Axis camera provider
│
├── templates/                # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── cameras.html
│   ├── viewer.html
│   ├── grid.html
│   ├── recordings.html
│   ├── access_control.html
│   ├── events.html
│   └── embed_stream.html
│
├── static/                   # Static assets
│   ├── css/
│   ├── js/
│   └── streams/             # HLS stream segments
│
├── scripts/                  # Utility scripts
│   ├── diagnose_dahua.py
│   ├── refresh_camera.py
│   ├── test_camera.py
│   └── test_stream_management.py
│
├── docs/                     # All documentation
│   ├── overview/            # Project overview documents
│   ├── guides/              # User guides
│   ├── reference/           # Reference documentation
│   ├── changelog/           # Change logs and bug fixes
│   ├── api/                 # API documentation
│   │   └── dvr-channels/   # DVR Channels API docs
│   └── stream-management/   # Streaming documentation
│
└── data/                    # Application data (database, etc.)
```

## Documentation Organization

### `/docs/overview/`
High-level project documentation:
- `ARCHITECTURE.md` - System architecture
- `PROJECT_SUMMARY.md` - Project overview
- `IMPLEMENTATION_SUMMARY.md` - Implementation details
- `QUICKSTART.md` - Quick start guide
- `PROJECT_ANALYSIS.md` - Comprehensive project analysis

### `/docs/guides/`
User and developer guides:
- `USAGE.md` - Comprehensive usage guide
- `STREAMING_GUIDE.md` - Streaming setup and usage

### `/docs/reference/`
Reference documentation:
- `PROFILES.md` - ONVIF profile details
- `TESTING.md` - Testing guide

### `/docs/changelog/`
Change logs and bug fixes:
- `BUGFIXES.md` - Bug fix history
- `IMPLEMENTATION_COMPLETE.md` - Implementation completion notes

### `/docs/api/dvr-channels/`
DVR Channels API documentation:
- `DVR_CHANNELS_API.md` - Main API documentation
- `DVR_CHANNELS_API_ARCHITECTURE.md` - API architecture
- `DVR_CHANNELS_API_IMPLEMENTATION.md` - Implementation details
- `DVR_CHANNELS_API_TESTING.md` - Testing documentation
- `DVR_CHANNELS_API_TEST_RESULTS.md` - Test results
- `DVR_CHANNELS_API_VERIFICATION_REPORT.md` - Verification report
- `DVR_CHANNELS_API_VISUAL_GUIDE.md` - Visual guide
- `DVR_CHANNELS_API_QUICK_REFERENCE.md` - Quick reference
- `DVR_CHANNELS_API_README.md` - API README
- `DVR_CHANNELS_API_INDEX.md` - API index
- `DVR_CHANNELS_API_CHECKLIST.md` - Implementation checklist

### `/docs/stream-management/`
Streaming management documentation:
- `STREAM_MANAGEMENT_IMPROVEMENTS.md` - Improvements documentation
- `STREAM_MANAGEMENT_QUICK_REFERENCE.md` - Quick reference

## Scripts Organization

### `/scripts/`
Utility and diagnostic scripts:
- `diagnose_dahua.py` - Dahua camera diagnostics
- `refresh_camera.py` - Camera refresh utility
- `test_camera.py` - Camera testing script
- `test_stream_management.py` - Stream management tests

## Key Principles

1. **Root Directory**: Contains only essential files for running the application
2. **Documentation**: All documentation organized in `/docs/` with clear categorization
3. **Scripts**: Utility scripts separated from main application code
4. **Templates & Static**: Web assets in standard Flask locations
5. **Vendor Code**: Vendor-specific integrations in dedicated `camera_providers/` directory

## File Naming Conventions

- **Python files**: snake_case (e.g., `onvif_manager.py`)
- **Documentation**: UPPER_CASE.md (e.g., `ARCHITECTURE.md`)
- **Scripts**: snake_case.py (e.g., `test_camera.py`)
- **Directories**: lowercase (e.g., `camera_providers/`)

