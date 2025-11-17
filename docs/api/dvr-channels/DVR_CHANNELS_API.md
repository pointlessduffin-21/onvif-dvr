# DVR Channels API Documentation

## Overview
The DVR Channels API provides a simple way to retrieve detailed information about DVR/NVR systems and their connected channels (cameras). The API returns comprehensive data including RTSP feed URIs, embedded iframe URLs, channel status, and technical specifications.

## Endpoints

### 1. Get All DVR Channels
**Endpoint:** `GET /api/dvr/channels`

Retrieve channels for all DVRs or filter by specific DVR/channel.

**Query Parameters:**
- `dvr_id` (optional, integer): Get channels for a specific DVR
- `channel_id` (optional, integer): Get a specific channel by number

**Example Requests:**

Get all channels from all DVRs:
```bash
GET /api/dvr/channels
```

Get all channels from a specific DVR:
```bash
GET /api/dvr/channels?dvr_id=1
```

Get a specific channel:
```bash
GET /api/dvr/channels?dvr_id=1&channel_id=1
```

**Response Format (All DVRs):**
```json
[
  {
    "dvr_id": 1,
    "dvr_name": "Dahua DVR 1",
    "dvr_host": "192.168.1.100",
    "dvr_port": 80,
    "status": "online",
    "manufacturer": "Dahua",
    "model": "HCVR5108HE-S3",
    "serial_number": "ABC123456",
    "channels": [
      {
        "channel_id": 1,
        "channel_name": "Camera 1",
        "status": 1,
        "rtsp_feed": "rtsp://192.168.1.100:554/cam/realmonitor?channel=1&subtype=0",
        "iframe": "http://localhost:8821/embed/streams/1",
        "stream_id": 1,
        "profile_token": "Profile000",
        "codec": "H.264",
        "resolution": "1920x1080",
        "framerate": 25,
        "bitrate": 2048
      },
      {
        "channel_id": 1,
        "channel_name": "Camera 1 Sub",
        "status": 1,
        "rtsp_feed": "rtsp://192.168.1.100:554/cam/realmonitor?channel=1&subtype=1",
        "iframe": "http://localhost:8821/embed/streams/2",
        "stream_id": 2,
        "profile_token": "Profile001",
        "codec": "H.264",
        "resolution": "704x480",
        "framerate": 15,
        "bitrate": 512
      }
    ]
  }
]
```

**Response Format (Single DVR with dvr_id parameter):**
```json
{
  "dvr_id": 1,
  "dvr_name": "Dahua DVR 1",
  "dvr_host": "192.168.1.100",
  "dvr_port": 80,
  "status": "online",
  "manufacturer": "Dahua",
  "model": "HCVR5108HE-S3",
  "serial_number": "ABC123456",
  "channels": [
    {
      "channel_id": 1,
      "channel_name": "Camera 1",
      "status": 1,
      "rtsp_feed": "rtsp://192.168.1.100:554/cam/realmonitor?channel=1&subtype=0",
      "iframe": "http://localhost:8821/embed/streams/1",
      "stream_id": 1,
      "profile_token": "Profile000",
      "codec": "H.264",
      "resolution": "1920x1080",
      "framerate": 25,
      "bitrate": 2048
    }
  ]
}
```

### 2. Get DVR Channels by DVR ID (RESTful)
**Endpoint:** `GET /api/dvr/<dvr_id>/channels`

Retrieve all channels for a specific DVR using the DVR ID in the URL path.

**URL Parameters:**
- `dvr_id` (required, integer): The ID of the DVR

**Example Request:**
```bash
GET /api/dvr/1/channels
```

**Response Format:**
```json
{
  "dvr_id": 1,
  "dvr_name": "Dahua DVR 1",
  "dvr_host": "192.168.1.100",
  "dvr_port": 80,
  "status": "online",
  "manufacturer": "Dahua",
  "model": "HCVR5108HE-S3",
  "serial_number": "ABC123456",
  "channels": [
    {
      "channel_id": 1,
      "channel_name": "Camera 1",
      "status": 1,
      "rtsp_feed": "rtsp://192.168.1.100:554/cam/realmonitor?channel=1&subtype=0",
      "iframe": "http://localhost:8821/embed/streams/1",
      "stream_id": 1,
      "profile_token": "Profile000",
      "codec": "H.264",
      "resolution": "1920x1080",
      "framerate": 25,
      "bitrate": 2048
    }
  ]
}
```

## Response Fields

### DVR Object
- **dvr_id** (integer): Unique identifier for the DVR
- **dvr_name** (string): Display name of the DVR
- **dvr_host** (string): IP address or hostname of the DVR
- **dvr_port** (integer): Connection port (typically 80 or 443)
- **status** (string): Current DVR status ("online" or "offline")
- **manufacturer** (string): DVR manufacturer (e.g., "Dahua", "Hikvision")
- **model** (string): DVR model number
- **serial_number** (string): DVR serial number
- **channels** (array): Array of channel objects

### Channel Object
- **channel_id** (integer): Unique identifier for the channel
- **channel_name** (string): Display name of the channel/camera
- **status** (integer): Channel status (1 = online/active, 0 = offline/inactive)
- **rtsp_feed** (string): Complete RTSP URI for direct streaming
- **iframe** (string): Embedded iframe URL for web integration
- **stream_id** (integer): Internal stream database ID
- **profile_token** (string): ONVIF profile token
- **codec** (string): Video codec (e.g., "H.264", "H.265")
- **resolution** (string): Video resolution (e.g., "1920x1080")
- **framerate** (integer): Frames per second
- **bitrate** (integer): Bitrate in Kbps

## Error Responses

### 404 Not Found
```json
{
  "error": "DVR not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Error message describing what went wrong"
}
```

## Usage Examples

### cURL Examples

Get all DVRs and their channels:
```bash
curl -X GET http://localhost:8821/api/dvr/channels
```

Get channels for DVR with ID 1:
```bash
curl -X GET http://localhost:8821/api/dvr/1/channels
```

Get specific channel via query parameter:
```bash
curl -X GET "http://localhost:8821/api/dvr/channels?dvr_id=1&channel_id=1"
```

### JavaScript Examples

Fetch all DVR channels:
```javascript
fetch('/api/dvr/channels')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
```

Fetch channels for a specific DVR:
```javascript
const dvrId = 1;
fetch(`/api/dvr/${dvrId}/channels`)
  .then(response => response.json())
  .then(dvr => {
    console.log(`DVR: ${dvr.dvr_name}`);
    dvr.channels.forEach(channel => {
      console.log(`  - ${channel.channel_name}: ${channel.rtsp_feed}`);
    });
  })
  .catch(error => console.error('Error:', error));
```

Embed a camera stream in HTML:
```html
<iframe 
  src="http://localhost:8821/embed/streams/1" 
  width="640" 
  height="480" 
  frameborder="0">
</iframe>
```

### Python Examples

Get all DVR channels:
```python
import requests

response = requests.get('http://localhost:8821/api/dvr/channels')
dvrs = response.json()

for dvr in dvrs:
    print(f"DVR: {dvr['dvr_name']} ({dvr['status']})")
    for channel in dvr['channels']:
        print(f"  - {channel['channel_name']}: {channel['rtsp_feed']}")
```

Get a specific DVR's channels:
```python
import requests

dvr_id = 1
response = requests.get(f'http://localhost:8821/api/dvr/{dvr_id}/channels')
dvr = response.json()

if 'error' in dvr:
    print(f"Error: {dvr['error']}")
else:
    print(f"DVR: {dvr['dvr_name']}")
    print(f"Status: {dvr['status']}")
    print(f"Channels: {len(dvr['channels'])}")
```

## Integration Patterns

### Web Dashboard Integration
Use the `iframe` URL to embed camera feeds directly into your web application:

```html
<div class="camera-grid">
  <div class="camera-tile" id="camera-1">
    <iframe src="" width="100%" height="100%"></iframe>
  </div>
</div>

<script>
fetch('/api/dvr/1/channels')
  .then(r => r.json())
  .then(dvr => {
    dvr.channels.forEach(ch => {
      const tile = document.querySelector(`#camera-${ch.channel_id}`);
      if (tile) {
        tile.querySelector('iframe').src = ch.iframe;
      }
    });
  });
</script>
```

### RTSP Stream Recording
Use the `rtsp_feed` URL with ffmpeg or other video tools:

```bash
# Record an RTSP stream
ffmpeg -i "rtsp://192.168.1.100:554/cam/realmonitor?channel=1&subtype=0" \
  -c copy output.mp4
```

### External System Integration
Query the API to dynamically configure external systems:

```python
import requests
from datetime import datetime

# Get all cameras
response = requests.get('http://localhost:8821/api/dvr/channels')
cameras = []

for dvr in response.json():
    for channel in dvr['channels']:
        cameras.append({
            'name': f"{dvr['dvr_name']} - {channel['channel_name']}",
            'rtsp_uri': channel['rtsp_feed'],
            'status': 'active' if channel['status'] == 1 else 'inactive'
        })

# Use this data to configure other systems
print(f"Found {len(cameras)} cameras")
for camera in cameras:
    print(f"  {camera['name']}: {camera['rtsp_uri']}")
```

## Status Codes

- **1** = Channel is online/active
- **0** = Channel is offline/inactive

The channel status is derived from the DVR's overall status. If the DVR is offline, all its channels will report status 0.

## Notes

- The API automatically generates iframe URLs based on the request protocol and host
- All timestamps are in ISO 8601 format
- The RTSP feed URLs can be used directly with VLC, ffmpeg, or any RTSP-compatible player
- Channel data is fetched from the database and reflects the last refresh
- For real-time status, consider implementing a polling mechanism

