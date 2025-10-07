# ONVIF Viewer - Streaming & Recording Guide

## Video Streaming (ffmpeg + HLS)

### How It Works

The application now supports live RTSP stream playback in your browser using:

1. **RTSP to HLS Conversion**: Python service uses ffmpeg to convert RTSP streams to HLS format
2. **Browser Playback**: HLS.js library plays the converted streams in any modern browser
3. **Low Latency**: 2-second segments for near real-time viewing

### Using Live Streams

1. Go to **Cameras** page
2. Click **View** on any camera
3. Select a stream from the right sidebar (MainStream or SubStream)
4. Click the **Play** button
5. Wait 2-3 seconds for ffmpeg to generate initial segments
6. Video will start playing automatically

### Stream Quality Options

Each camera channel has two stream types:

- **MainStream** (subtype=0): High resolution, higher bandwidth
- **SubStream** (subtype=1): Lower resolution, optimized for remote viewing

### Stopping Streams

Click the **Stop** button to:
- Stop the ffmpeg process
- Clean up HLS segments
- Free server resources

**Important**: Always stop streams when done to prevent resource exhaustion

---

## ONVIF Recordings (Profile G)

### How DVR/NVR Recording Works

Your Dahua XVR records video to its internal hard drives. The ONVIF Profile G standard allows us to:

1. **Search Recordings**: Query the DVR for recorded footage by time range
2. **Get Recording Info**: Retrieve metadata about available recordings
3. **Playback**: Get RTSP URLs to play back recorded footage

### Searching DVR Recordings

1. Go to **Recordings** page
2. Select your camera from the dropdown
3. Choose a date/time range
4. Click **Search**
5. Results show all available recordings on the DVR

### Quick Search Buttons

- **Today**: Search recordings from today
- **Yesterday**: Search yesterday's recordings  
- **Last 7 Days**: Search past week
- **Last 30 Days**: Search past month

### Recording Summary

The right sidebar shows:
- Total number of recordings on the device
- Recording sources (channels)
- Available tracks (video/audio)

### Playing Back Recordings

1. Search for recordings
2. Click **Play** on any result
3. The system retrieves an RTSP URL for that recording
4. **Note**: Recording playback currently shows the RTSP URL
5. **Future**: Will convert to HLS for browser playback (same as live streams)

---

## Technical Details

### ffmpeg Command Used

```bash
ffmpeg -rtsp_transport tcp \
  -i rtsp://camera-url \
  -c:v copy \
  -c:a aac \
  -f hls \
  -hls_time 2 \
  -hls_list_size 10 \
  -hls_flags delete_segments+append_list \
  stream.m3u8
```

**Flags Explained**:
- `-rtsp_transport tcp`: Use TCP for reliable streaming
- `-c:v copy`: Copy video codec (no re-encoding = faster, less CPU)
- `-c:a aac`: Convert audio to AAC (browser compatible)
- `-hls_time 2`: 2-second segments for low latency
- `-hls_list_size 10`: Keep last 10 segments (20 seconds of video)
- `-hls_flags delete_segments`: Auto-cleanup old segments

### HLS Output Structure

```
static/streams/
  ├── camera1_MediaProfile00000/
  │   ├── stream.m3u8        # Playlist file
  │   ├── segment_000.ts     # Video segment 1
  │   ├── segment_001.ts     # Video segment 2
  │   └── segment_002.ts     # Video segment 3
  └── camera1_MediaProfile00001/
      └── ...
```

### API Endpoints

#### Streaming
- `POST /api/streams/start` - Start HLS conversion
- `POST /api/streams/stop` - Stop conversion
- `GET /api/streams/status/<stream_id>` - Get stream status
- `GET /api/streams/all` - List all active streams

#### Recordings
- `POST /api/cameras/<id>/recordings/search` - Search DVR recordings
- `GET /api/cameras/<id>/recordings/summary` - Get recording summary
- `POST /api/recordings/playback-uri` - Get playback RTSP URL

---

## System Requirements

### Required Software

1. **ffmpeg**: Must be installed on your system
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # Check installation
   ffmpeg -version
   ```

2. **Python Packages**: Already in requirements.txt
   - flask
   - onvif-zeep
   - opencv-python (optional, for snapshot features)

### Browser Requirements

- **Modern Browser**: Chrome, Firefox, Safari, Edge
- **JavaScript Enabled**: Required for HLS.js
- **No Plugins**: Works without Flash or other plugins

---

## Performance Considerations

### Server Resources

- **CPU**: Each ffmpeg process uses ~5-10% CPU per stream
- **Memory**: ~50-100MB per active stream
- **Disk**: HLS segments use ~1-2MB per second per stream
- **Recommendation**: Limit concurrent streams based on server capacity

### Network Bandwidth

- **MainStream**: ~2-4 Mbps per viewer
- **SubStream**: ~512 Kbps - 1 Mbps per viewer
- **Recommendation**: Use SubStream for remote viewing

### Storage (for local recording)

If implementing client-side recording:
- **1080p**: ~1-2 GB per hour
- **720p**: ~500 MB - 1 GB per hour
- **Recommendation**: Set up automatic cleanup for old recordings

---

## Troubleshooting

### Stream Won't Start

1. Check ffmpeg is installed: `ffmpeg -version`
2. Check RTSP URL is accessible: `ffmpeg -i rtsp://url -t 1 test.mp4`
3. Check server logs for errors
4. Verify camera credentials are correct

### Playback Stutters or Buffers

1. Try SubStream instead of MainStream
2. Check network bandwidth
3. Reduce number of concurrent viewers
4. Increase HLS segment size (in stream_manager.py)

### Recording Search Returns Nothing

1. Verify camera has ONVIF Profile G support
2. Check DVR has recordings in the time range
3. Verify hard drive is installed and working
4. Check ONVIF recording service is enabled on camera

### Recording Playback Fails

1. Verify recording token is correct
2. Check time range is within recording bounds
3. Try using ONVIF Device Manager to test recording playback
4. Some cameras require specific ONVIF services to be enabled

---

## Next Steps / Future Enhancements

### Planned Features

1. **Recording HLS Conversion**: Convert DVR playback to HLS (currently shows RTSP URL)
2. **Snapshot Capture**: Take still images from live streams
3. **Client-Side Recording**: Record streams directly on your server
4. **Multi-View**: Watch multiple streams simultaneously
5. **Motion Detection**: Detect motion in streams using OpenCV
6. **Smart Search**: Find recordings with specific events
7. **Export**: Download recordings in standard formats

### Contributing

Feel free to enhance the application with additional features!

---

## Support

For issues or questions:
1. Check logs in Flask console
2. Test camera with ONVIF Device Manager
3. Verify ffmpeg installation
4. Review ONVIF Profile G documentation for your camera model
