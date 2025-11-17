# DVR Channels API - Visual Quick Guide

## 🎯 API Overview

```
┌─────────────────────────────────────────────────────────┐
│              DVR CHANNELS API ENDPOINTS                 │
└─────────────────────────────────────────────────────────┘

Option 1: Query Parameters (Flexible)
─────────────────────────────────────
GET /api/dvr/channels
GET /api/dvr/channels?dvr_id=1
GET /api/dvr/channels?dvr_id=1&channel_id=1

Option 2: RESTful Path (Clean)
──────────────────────────────
GET /api/dvr/1/channels
```

## 📋 Response Structure

```
{
  "dvr_id": 1                    ◄── DVR identifier
  "dvr_name": "Dahua DVR 1"      ◄── DVR name
  "dvr_host": "192.168.1.100"    ◄── IP address
  "dvr_port": 80                 ◄── Port number
  "status": "online"             ◄── "online" or "offline"
  "manufacturer": "Dahua"        ◄── Vendor name
  "model": "HCVR5108HE-S3"       ◄── Model number
  "serial_number": "ABC123456"   ◄── Serial number
  "channels": [                  ◄── Array of channels
    {
      "channel_id": 1            ◄── Channel number
      "channel_name": "Camera 1" ◄── Display name
      "status": 1                ◄── 1=online, 0=offline
      "rtsp_feed": "rtsp://..."  ◄── Direct stream URL
      "iframe": "http://..."     ◄── Embed URL
      "stream_id": 1             ◄── DB identifier
      "profile_token": "Prof000" ◄── ONVIF token
      "codec": "H.264"           ◄── Video codec
      "resolution": "1920x1080"  ◄── Video resolution
      "framerate": 25            ◄── Frames per second
      "bitrate": 2048            ◄── Kilobits per second
    }
  ]
}
```

## 🔗 Quick Endpoints

| Endpoint | Purpose | Example |
|----------|---------|---------|
| `GET /api/dvr/channels` | All DVRs, all channels | Lists everything |
| `GET /api/dvr/1/channels` | DVR #1, all channels | Gets DVR 1 only |
| `GET /api/dvr/channels?dvr_id=1` | Same as above | Query style |
| `GET /api/dvr/channels?dvr_id=1&channel_id=1` | Specific channel | Single channel |

## 💻 Code Examples

### cURL
```bash
# Get all
curl http://localhost:8821/api/dvr/channels

# Get specific DVR
curl http://localhost:8821/api/dvr/1/channels

# Pretty print
curl -s http://localhost:8821/api/dvr/1/channels | jq .
```

### Python
```python
import requests

# Get all DVRs
response = requests.get('http://localhost:8821/api/dvr/channels')
dvrs = response.json()

# Specific DVR
response = requests.get('http://localhost:8821/api/dvr/1/channels')
dvr = response.json()

# List channels
for ch in dvr['channels']:
    print(f"{ch['channel_name']}: {ch['rtsp_feed']}")
```

### JavaScript
```javascript
// Get all DVRs
fetch('/api/dvr/channels')
  .then(r => r.json())
  .then(dvrs => console.log(dvrs))

// Get specific DVR
fetch('/api/dvr/1/channels')
  .then(r => r.json())
  .then(dvr => {
    dvr.channels.forEach(ch => {
      console.log(`${ch.channel_name}: ${ch.rtsp_feed}`);
    });
  })

// Embed iframe
document.getElementById('video').src = dvr.channels[0].iframe;
```

### HTML Embed
```html
<iframe src="http://localhost:8821/embed/streams/1" 
        width="640" height="480"></iframe>
```

## 🎬 Use Cases

### 1. Display All Cameras
```bash
curl http://localhost:8821/api/dvr/channels | \
  jq -r '.[] | .channels[] | .channel_name'
```

### 2. Get RTSP URL
```bash
curl -s http://localhost:8821/api/dvr/1/channels | \
  jq -r '.channels[0].rtsp_feed'
```

### 3. Record with FFmpeg
```bash
RTSP=$(curl -s http://localhost:8821/api/dvr/1/channels | \
  jq -r '.channels[0].rtsp_feed')
ffmpeg -i "$RTSP" -c copy output.mp4
```

### 4. Check Status
```javascript
fetch('/api/dvr/channels')
  .then(r => r.json())
  .then(dvrs => {
    dvrs.forEach(dvr => {
      console.log(`${dvr.dvr_name}: ${dvr.status}`);
    });
  })
```

## 📊 Status Values

```
DVR Status:
  "online"  = Working and connected
  "offline" = Not responding

Channel Status:
  1 = Online and streaming
  0 = Offline or inactive
```

## 🔴 Error Codes

```
200 OK               ✅ Success
404 Not Found        ❌ DVR doesn't exist
500 Server Error     ❌ Database error
```

## 🚀 Quick Test

```bash
# 1. Verify API is working
curl http://localhost:8821/api/dvr/channels

# 2. If error, check Flask is running
curl http://localhost:8821/

# 3. Check database has data
sqlite3 onvif_viewer.db "SELECT COUNT(*) FROM cameras;"

# 4. Pretty print response
curl -s http://localhost:8821/api/dvr/channels | jq .
```

## 🎯 Common Patterns

### Pattern 1: Get All Cameras
```javascript
const allCameras = [];
fetch('/api/dvr/channels')
  .then(r => r.json())
  .then(dvrs => {
    dvrs.forEach(dvr => {
      dvr.channels.forEach(ch => {
        allCameras.push({
          dvr: dvr.dvr_name,
          camera: ch.channel_name,
          rtsp: ch.rtsp_feed,
          iframe: ch.iframe
        });
      });
    });
    console.log(allCameras);
  });
```

### Pattern 2: Create Video Grid
```html
<div id="cameras"></div>
<script>
fetch('/api/dvr/channels')
  .then(r => r.json())
  .then(dvrs => {
    const html = dvrs.map(dvr => 
      dvr.channels.map(ch => 
        `<iframe src="${ch.iframe}" width="400" height="300"></iframe>`
      ).join('')
    ).join('');
    document.getElementById('cameras').innerHTML = html;
  });
</script>
```

### Pattern 3: Monitor Status
```python
import requests
import time

while True:
    response = requests.get('http://localhost:8821/api/dvr/channels')
    dvrs = response.json()
    
    for dvr in dvrs:
        status = "🟢 Online" if dvr['status'] == 'online' else "🔴 Offline"
        print(f"{dvr['dvr_name']}: {status}")
        
        for ch in dvr['channels']:
            status = "✓" if ch['status'] == 1 else "✗"
            print(f"  {status} {ch['channel_name']}")
    
    print()
    time.sleep(10)
```

## 📝 Field Reference

```
DVR Object:
├─ dvr_id          (int)    - Database ID
├─ dvr_name        (str)    - Display name
├─ dvr_host        (str)    - IP address
├─ dvr_port        (int)    - Port (usually 80)
├─ status          (str)    - "online" or "offline"
├─ manufacturer    (str)    - Brand name
├─ model           (str)    - Model number
├─ serial_number   (str)    - Serial
└─ channels        (array)  - List of cameras

Channel Object:
├─ channel_id      (int)    - Channel number
├─ channel_name    (str)    - Camera name
├─ status          (int)    - 1 or 0
├─ rtsp_feed       (str)    - Stream URL
├─ iframe          (str)    - Embed URL
├─ stream_id       (int)    - DB ID
├─ profile_token   (str)    - ONVIF token
├─ codec           (str)    - "H.264" etc
├─ resolution      (str)    - "1920x1080"
├─ framerate       (int)    - 25, 30, etc
└─ bitrate         (int)    - 2048, etc
```

## 🎓 Learning Resources

| Resource | Find | Purpose |
|----------|------|---------|
| `DVR_CHANNELS_API.md` | Full docs | Complete reference |
| `DVR_CHANNELS_API_QUICK_REFERENCE.md` | Quick ref | Fast lookup |
| `DVR_CHANNELS_API_TESTING.md` | Tests | Code examples |
| `DVR_CHANNELS_API_ARCHITECTURE.md` | Design | How it works |

---

**Ready to use!** ✅ Just restart Flask to enable the new endpoints.

