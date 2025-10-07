# 🚀 Quick Start Guide - ONVIF Viewer

Get up and running in 5 minutes!

## Prerequisites Check

Before starting, ensure you have:
- ✅ Python 3.8+ installed
- ✅ pip package manager
- ✅ Terminal/command line access
- ✅ ONVIF camera on your network (optional for initial setup)

Check Python version:
```bash
python3 --version
```

## Installation (3 steps)

### Step 1: Setup
```bash
cd /Users/yeems214/cw-prototypes/onvif-prototype
./setup.sh
```

This will:
- Create virtual environment
- Install all dependencies
- Create configuration file
- Initialize database

**Time:** ~2 minutes

### Step 2: Configure (Optional)
```bash
nano .env
```

Change if needed:
- `SECRET_KEY` - Use a random string for production
- `DATABASE_PATH` - Leave as default

**Time:** 30 seconds

### Step 3: Start
```bash
./start.sh
```

**Time:** 5 seconds

## Access Application

Open your web browser:
```
http://localhost:5000
```

You should see the dashboard! 🎉

## Add Your First Camera

1. Click **"Cameras"** in navigation
2. Click **"Add Camera"** button
3. Fill in the form:

```
Name: Front Door Camera
IP Address: 192.168.1.100
Port: 80
Username: admin
Password: your-password
```

4. Click **"Add Camera"**

The application will:
- Connect to the camera
- Retrieve device info
- Detect supported profiles
- Set up video streams

## Test Without Physical Camera

Don't have an ONVIF camera? No problem!

### Option 1: Use ONVIF Simulator
```bash
# Install Docker if not already installed
brew install docker

# Run ONVIF simulator
docker run -d -p 8080:80 --name onvif-sim artogrig/onvif-device-simulator

# Use these credentials in the app:
Host: localhost
Port: 8080
Username: admin
Password: admin
```

### Option 2: Explore the Interface
- Dashboard shows statistics (will be 0 without cameras)
- All pages are functional
- Database is working
- API endpoints are ready

## Troubleshooting

### Issue: Port 5000 already in use
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or change port in app.py
nano app.py
# Change: app.run(port=5001)
```

### Issue: Permission denied on scripts
```bash
chmod +x setup.sh start.sh
```

### Issue: Module not found
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Database error
```bash
# Reinitialize database
rm onvif_viewer.db
python init_db.py
```

## Next Steps

### 1. Explore Features
- 📊 **Dashboard** - View statistics and camera grid
- 📹 **Cameras** - Manage camera configurations
- 🎥 **Viewer** - Watch live video streams
- 📼 **Recordings** - Manage video recordings
- 🔒 **Access Control** - Monitor access points
- 📊 **Events** - View events and analytics

### 2. Add More Cameras
Repeat the "Add Camera" process for additional cameras

### 3. Configure Profiles
Each camera supports different ONVIF profiles:
- Profile S: Video streaming
- Profile G: Recording
- Profile C/A: Access control
- Profile T: Advanced streaming
- Profile M: Events & analytics
- Profile D: Peripherals

### 4. Read Documentation
- **USAGE.md** - Detailed user guide
- **PROFILES.md** - ONVIF profile details
- **ARCHITECTURE.md** - System architecture
- **TESTING.md** - Testing guide

## Common Tasks

### Stop Application
Press `Ctrl+C` in the terminal

### Restart Application
```bash
./start.sh
```

### View Logs
Logs appear in the terminal where you started the app

### Backup Database
```bash
cp onvif_viewer.db onvif_viewer.db.backup
```

### Update Configuration
```bash
nano .env
# Make changes
# Restart application
```

## Production Deployment

For production use:

1. **Set production mode:**
```bash
# In .env
FLASK_ENV=production
```

2. **Change secret key:**
```bash
# In .env
SECRET_KEY=your-random-secret-key-here
```

3. **Use production server:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

4. **Set up HTTPS** (recommended)

5. **Configure firewall**

See USAGE.md for detailed production setup.

## API Quick Reference

Test API with curl:

```bash
# Get all cameras
curl http://localhost:5000/api/cameras

# Add camera
curl -X POST http://localhost:5000/api/cameras \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","host":"192.168.1.100","port":80,"username":"admin","password":"pass"}'

# Get recordings
curl http://localhost:5000/api/recordings

# Get events
curl http://localhost:5000/api/events
```

## System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 2 GB
- Disk: 1 GB (+ recording storage)
- Network: 100 Mbps

**Recommended:**
- CPU: 4 cores
- RAM: 4 GB
- Disk: 10 GB (+ recording storage)
- Network: 1 Gbps

## Getting Help

1. **Check logs** - Terminal output shows errors
2. **Review documentation** - See USAGE.md
3. **Test API** - Use curl to test endpoints
4. **Verify network** - Ping camera IP
5. **Check camera** - Ensure ONVIF is enabled

## Success Checklist

After setup, verify:
- ✅ Application starts without errors
- ✅ Can access http://localhost:5000
- ✅ Dashboard loads properly
- ✅ All menu items accessible
- ✅ Can add/edit/delete cameras
- ✅ Database operations work
- ✅ API endpoints respond

## Summary

**Setup Time:** ~5 minutes
**Difficulty:** Easy
**Prerequisites:** Python 3.8+
**Platforms:** macOS, Linux, Windows

You're now ready to use ONVIF Viewer! 🎉

For detailed information, see:
- **USAGE.md** - Complete user guide
- **PROFILES.md** - ONVIF profiles explained
- **TESTING.md** - Testing procedures
- **ARCHITECTURE.md** - System design

Happy viewing! 📹
