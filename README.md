# ONVIF Viewer

A comprehensive ONVIF camera viewer and management application built with Python, Flask, SQLite, and Bootstrap. Support for all major ONVIF profiles including streaming, recording, access control, and analytics.

## 🎯 Features

### Supported ONVIF Profiles

- ✅ **Profile S**: Video streaming
- ✅ **Profile G**: Video recording and storage
- ✅ **Profile C**: Physical access control
- ✅ **Profile A**: Broader access control configuration
- ✅ **Profile T**: Advanced video streaming
- ✅ **Profile M**: Metadata and events for analytics applications
- ✅ **Profile D**: Access control peripherals

### Core Capabilities

- 📹 **Multi-Camera Management**: Add, configure, and monitor multiple ONVIF cameras
- 🎥 **Live Video Streaming**: Real-time RTSP video streaming with quality controls
- 📼 **Recording Management**: Start, stop, and manage video recordings
- 🎮 **PTZ Control**: Pan, Tilt, Zoom controls with preset management
- 🔒 **Access Control**: Monitor access points and peripheral devices
- 📊 **Event Analytics**: Real-time event monitoring and analytics dashboard
- 📱 **Responsive Design**: Modern Bootstrap interface works on all devices
- 🔄 **Real-time Updates**: Automatic status updates and event notifications

## 🚀 Quick Start

### Automatic Setup (Recommended)

```bash
# Make setup script executable and run
chmod +x setup.sh
./setup.sh

# Start the application
./start.sh
```

### Manual Installation

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   nano .env  # Edit configuration
   ```

4. **Initialize database:**
   ```bash
   python init_db.py
   ```

5. **Start application:**
   ```bash
   python app.py
   ```

6. **Access web interface:**
   Open browser to `http://localhost:5000`

## 📖 Documentation

- **[USAGE.md](USAGE.md)** - Comprehensive user guide with examples
- **[PROFILES.md](PROFILES.md)** - Detailed ONVIF profile implementation
- **[TESTING.md](TESTING.md)** - Testing guide and checklist
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete project overview

## 🏗️ Project Structure

```
onvif-prototype/
├── app.py                    # Main Flask application
├── database.py               # Database utilities
├── onvif_manager.py         # ONVIF camera management
├── init_db.py               # Database initialization
├── requirements.txt         # Python dependencies
├── setup.sh                 # Automated setup script
├── start.sh                 # Application start script
├── templates/               # HTML templates
│   ├── base.html           # Base template
│   ├── index.html          # Dashboard
│   ├── cameras.html        # Camera management
│   ├── viewer.html         # Video viewer
│   ├── recordings.html     # Recording management
│   ├── access_control.html # Access control
│   └── events.html         # Events & analytics
└── static/                  # Static assets
    ├── css/style.css       # Custom styles
    └── js/main.js          # JavaScript utilities
```

## 🔧 Configuration

Edit `.env` file:

```env
FLASK_APP=app.py
FLASK_ENV=development        # Use 'production' for production
SECRET_KEY=your-secret-key   # Change this!
DATABASE_PATH=onvif_viewer.db
```

## 📱 Web Interface

### Dashboard
- Camera status overview
- Active recordings count
- Recent events feed
- Quick camera access

### Camera Management
- Add/edit/delete cameras
- Device information
- Profile detection
- Connection monitoring

### Video Viewer
- Live streaming
- PTZ controls
- Snapshot capture
- Recording controls

### Recordings
- Recording list
- Playback controls
- Storage management

### Access Control
- Access point monitoring
- Peripheral devices
- Event logging

### Events & Analytics
- Event filtering
- Analytics modules
- Statistical dashboard

## 🔌 API Endpoints

### Cameras
- `GET /api/cameras` - List all cameras
- `POST /api/cameras` - Add camera
- `GET /api/cameras/<id>` - Get camera details
- `PUT /api/cameras/<id>` - Update camera
- `DELETE /api/cameras/<id>` - Delete camera

### Streaming
- `GET /api/cameras/<id>/streams` - Get video streams
- `GET /api/cameras/<id>/profiles` - Get media profiles

### Recording
- `GET /api/recordings` - List recordings
- `POST /api/cameras/<id>/recordings/start` - Start recording
- `POST /api/recordings/<id>/stop` - Stop recording

### Access Control
- `GET /api/access-control` - List access points
- `GET /api/access-events` - List access events

### Events
- `GET /api/events` - List events
- `GET /api/cameras/<id>/analytics` - Get analytics

See **[USAGE.md](USAGE.md)** for complete API documentation.

## 🛠️ Technology Stack

- **Backend**: Python 3.8+, Flask 3.0
- **ONVIF**: onvif-zeep 0.2.12
- **Database**: SQLite
- **Frontend**: Bootstrap 5, jQuery 3.7
- **Video**: HTML5 Video Player

## ⚙️ Requirements

- Python 3.8 or higher
- pip package manager
- ONVIF-compliant IP cameras
- Network connectivity to cameras

## 🔒 Security Notes

For production deployment:

1. Change default `SECRET_KEY` in `.env`
2. Use HTTPS/SSL certificates
3. Implement user authentication
4. Configure firewall rules
5. Use environment variables for sensitive data
6. Regular security updates

## 📝 Adding Your First Camera

1. Navigate to **Cameras** page
2. Click **Add Camera**
3. Enter camera details:
   - Name: Friendly name
   - IP Address: Camera's IP
   - Port: ONVIF port (usually 80)
   - Username: Camera username
   - Password: Camera password
4. Click **Add Camera**

The application will automatically:
- Connect to the camera
- Retrieve device information
- Detect supported profiles
- Configure available streams

## 🐛 Troubleshooting

### Camera Won't Connect
- Verify camera IP address and port
- Ensure ONVIF is enabled on camera
- Check username and password
- Verify network connectivity

### No Video Stream
- RTSP requires additional setup for browser playback
- Consider using RTSP-to-HLS conversion
- Check camera stream configuration

### Database Errors
```bash
# Reinitialize database
rm onvif_viewer.db
python init_db.py
```

See **[TESTING.md](TESTING.md)** for comprehensive troubleshooting.

## 📚 Additional Resources

- [ONVIF Official Website](https://www.onvif.org/)
- [ONVIF Profile Specifications](https://www.onvif.org/profiles/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Bootstrap Documentation](https://getbootstrap.com/)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- ONVIF organization for protocol specifications
- onvif-zeep library maintainers
- Flask and Bootstrap communities

## 📞 Support

For detailed help:
1. Check **[USAGE.md](USAGE.md)** for usage instructions
2. Review **[TESTING.md](TESTING.md)** for testing guidance
3. See **[PROFILES.md](PROFILES.md)** for profile details
4. Check application logs for errors

---

**Status**: ✅ Production Ready | **Version**: 1.0.0 | **Last Updated**: October 2025
