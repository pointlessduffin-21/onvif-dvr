# DVR Channels API - Quick Reference

## Quick Start

### Get All Channels from All DVRs
```
GET /api/dvr/channels
```

### Get All Channels from DVR #1
```
GET /api/dvr/1/channels
```
or
```
GET /api/dvr/channels?dvr_id=1
```

### Get Specific Channel
```
GET /api/dvr/channels?dvr_id=1&channel_id=1
```

## Response Structure

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

## Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `dvr_id` | int | DVR identifier |
| `dvr_name` | string | DVR display name |
| `status` | string | "online" or "offline" |
| `channel_id` | int | Channel number |
| `channel_name` | string | Channel display name |
| `status` (channel) | int | 1=online, 0=offline |
| `rtsp_feed` | string | Direct RTSP stream URL |
| `iframe` | string | Embeddable iframe URL |
| `codec` | string | Video codec (H.264, H.265) |
| `resolution` | string | Video resolution |
| `framerate` | int | Frames per second |
| `bitrate` | int | Bitrate in Kbps |

## Common Use Cases

### 1. List All Cameras
```javascript
fetch('/api/dvr/channels')
  .then(r => r.json())
  .then(dvrs => {
    dvrs.forEach(dvr => {
      dvr.channels.forEach(ch => {
        console.log(`${dvr.dvr_name} > ${ch.channel_name}`);
      });
    });
  });
```

### 2. Embed Camera in Page
```html
<iframe src="http://localhost:8821/embed/streams/1" width="640" height="480"></iframe>
```

### 3. Get RTSP URL for Streaming
```javascript
fetch('/api/dvr/1/channels')
  .then(r => r.json())
  .then(dvr => {
    const rtspUrl = dvr.channels[0].rtsp_feed;
    // Use with ffmpeg, VLC, or HLS converter
  });
```

### 4. Check DVR Status
```javascript
fetch('/api/dvr/channels')
  .then(r => r.json())
  .then(dvrs => {
    dvrs.forEach(dvr => {
      console.log(`${dvr.dvr_name}: ${dvr.status}`);
    });
  });
```

### 5. Record Stream with FFmpeg
```bash
curl http://localhost:8821/api/dvr/1/channels -s | \
  jq -r '.channels[0].rtsp_feed' | \
  xargs -I {} ffmpeg -i {} -c copy output.mp4
```

## Status Values

- **DVR Status**: "online" | "offline"
- **Channel Status**: 1 (active) | 0 (inactive)

## Error Codes

- **200 OK**: Request successful
- **404 Not Found**: DVR or channel not found
- **500 Internal Error**: Server error

## Testing with cURL

```bash
# Get all DVRs
curl http://localhost:8821/api/dvr/channels

# Get specific DVR
curl http://localhost:8821/api/dvr/1/channels

# Pretty print
curl -s http://localhost:8821/api/dvr/channels | jq .

# Get first camera RTSP URL
curl -s http://localhost:8821/api/dvr/1/channels | jq -r '.channels[0].rtsp_feed'

# Get all camera names
curl -s http://localhost:8821/api/dvr/channels | jq -r '.[] | .channels[].channel_name'
```

## Notes

- Status 1 = online/active
- Status 0 = offline/inactive
- RTSP URLs can be used with any RTSP player
- Iframe URLs are auto-generated based on request protocol
- All channels inherit DVR status

