# Real-Time Streaming Configuration

## Overview

The streaming system has been optimized for **ultra-low latency real-time viewing** to eliminate delays and inconsistencies in playback.

## Key Real-Time Optimizations

### 1. Ultra-Short Segments

**Before**: 1-second segments  
**After**: 0.5-second segments

- **Segment Duration**: 0.5 seconds (500ms)
- **Playlist Size**: Only 3 segments (1.5 seconds total)
- **Result**: Minimal delay between camera and viewer

### 2. Aggressive Buffer Management

**HLS.js Buffer Settings**:
- `maxBufferLength: 2` - Only 2 seconds buffer
- `backBufferLength: 0.5` - Minimal back buffer (0.5 seconds)
- `maxBufferSize: 3MB` - Ultra low memory usage
- `liveSyncDurationCount: 1` - Stay only 1 segment behind live
- `liveMaxLatencyDurationCount: 2` - Maximum 1 second behind (2 × 0.5s)

### 3. Continuous Live Edge Sync

**Automatic Live Edge Seeking**:
- Checks every 500ms for live edge position
- Automatically jumps to live edge if more than 1 second behind
- Ensures viewer always stays current with camera feed

### 4. Fast Timeouts and Retries

**Network Optimizations**:
- Fragment timeout: 1 second (ultra fast)
- Manifest timeout: 1 second
- Retry delay: 500ms
- Total timeout: 1.5 seconds

### 5. No-Cache Headers

**Server-Side**:
- All playlists and segments served with `no-cache` headers
- Prevents browser caching that causes delays
- Ensures always fetching latest segments

### 6. Event Playlist Mode

**FFmpeg Settings**:
- `-hls_playlist_type event` - Continuous playlist (no endlist)
- `-hls_flags omit_endlist` - Never mark stream as complete
- `-hls_flags temp_file` - Faster writes using temp files

## Performance Characteristics

### Latency Breakdown

```
Camera → RTSP → FFmpeg → Segment (0.5s) → Playlist Update → Browser → Playback
         ~0.1s      ~0.1s       0.5s            ~0.1s         ~0.2s      ~0.1s
                                                                    └─ Total: ~1.1s
```

**Typical End-to-End Latency**: 0.8-1.5 seconds

### Memory Usage

- **Browser Buffer**: ~3MB (down from 10MB+)
- **Server Segments**: ~1.5 seconds worth (3 × 0.5s segments)
- **Total Memory**: ~70% reduction from previous version

### CPU Usage

- **Segment Generation**: Minimal (0.5s segments = more frequent but smaller)
- **Playlist Updates**: Every 0.5 seconds
- **Overall**: Slightly higher CPU due to more frequent operations, but still optimized

## Real-Time Features

### 1. Automatic Live Edge Sync

The player continuously monitors and adjusts to stay at the live edge:

```javascript
// Checks every 500ms
setInterval(function() {
    const liveEdge = video.seekable.end(video.seekable.length - 1);
    const delay = liveEdge - video.currentTime;
    
    // Jump to live if more than 1 second behind
    if (delay > 1.0) {
        video.currentTime = liveEdge;
    }
}, 500);
```

### 2. Immediate Playback

- Starts playing as soon as first segment is available
- Doesn't wait for full buffer
- Seeks to live edge immediately on load

### 3. Fast Recovery

- 1-second timeouts for fast failure detection
- 500ms retry delays for quick recovery
- Automatic reconnection on errors

## Configuration

### FFmpeg Command (Real-Time Optimized)

```bash
ffmpeg \
  -rtsp_transport tcp \
  -fflags nobuffer+flush_packets \
  -flags low_delay \
  -i rtsp://camera-url \
  -c:v copy \
  -c:a aac -b:a 64k \
  -f hls \
  -hls_time 0.5 \              # 0.5-second segments
  -hls_list_size 3 \           # 3 segments only
  -hls_flags delete_segments+independent_segments+omit_endlist+temp_file \
  -hls_playlist_type event \    # Event mode (continuous)
  -movflags +faststart+empty_moov \
  -g 15 \                       # Keyframe every 15 frames
  output.m3u8
```

### HLS.js Configuration (Real-Time)

```javascript
{
    lowLatencyMode: true,
    maxBufferLength: 2,              // 2 seconds
    backBufferLength: 0.5,            // 0.5 seconds
    liveSyncDurationCount: 1,          // 1 segment behind
    liveMaxLatencyDurationCount: 2,   // Max 2 segments (1 second)
    fragLoadingTimeOut: 1,            // 1 second timeout
    manifestLoadingTimeOut: 1,        // 1 second timeout
    startPosition: -1,                 // Live edge
    maxLiveSyncPlaybackRate: 1.5      // Allow speedup to catch up
}
```

## Troubleshooting Real-Time Issues

### Stream Still Delayed

1. **Check Network**: High latency network will add delay
2. **Check Camera**: Camera encoding delay affects total latency
3. **Check Browser**: Some browsers have inherent HLS delays
4. **Check CPU**: High CPU usage can cause segment generation delays

### Inconsistent Playback

1. **Network Issues**: Packet loss causes buffering
2. **Camera Issues**: Camera may have encoding delays
3. **Browser Cache**: Clear browser cache (should be prevented by headers)
4. **Multiple Streams**: Too many streams can cause resource contention

### Stream Freezing

1. **Check Health Monitor**: Auto-recovery should handle this
2. **Check Logs**: Look for FFmpeg errors
3. **Restart Stream**: Manual restart if auto-recovery fails
4. **Check Camera Connection**: Verify RTSP stream is stable

## Monitoring

### Stream Health Endpoint

Check stream health:
```bash
GET /api/streams/status/<stream_id>
```

Response includes:
- `last_segment_age` - Age of last segment (should be < 1 second)
- `is_active` - Stream process status
- `reconnect_count` - Number of reconnections

### Expected Values

- **last_segment_age**: < 1 second (ideal: 0.5-0.8 seconds)
- **is_active**: `true`
- **reconnect_count**: 0 (should be 0 for stable streams)

## Best Practices

1. **Network**: Use wired connection for lowest latency
2. **Browser**: Chrome/Edge typically have best HLS.js performance
3. **Camera**: Use sub-stream for lower bandwidth/latency
4. **Quality**: Use 'auto' or 'low' for fastest processing
5. **Monitoring**: Monitor `last_segment_age` to detect issues early

## Limitations

### Physical Limits

- **Network Latency**: Cannot be eliminated (typically 50-200ms)
- **Camera Encoding**: Camera processing adds delay (typically 100-300ms)
- **Segment Generation**: 0.5s minimum (segment duration)
- **Browser Processing**: Browser HLS processing adds delay (typically 100-200ms)

### Total Minimum Latency

**Theoretical Minimum**: ~0.8-1.0 seconds  
**Typical Real-World**: ~1.0-1.5 seconds  
**Maximum (with issues)**: ~2-3 seconds

## Comparison

| Setting | Previous | Real-Time | Improvement |
|---------|----------|-----------|-------------|
| Segment Duration | 1s | 0.5s | 50% faster |
| Playlist Size | 6 segments | 3 segments | 50% less memory |
| Buffer Length | 10s | 2s | 80% reduction |
| Live Sync | 3 segments | 1 segment | 67% closer to live |
| Max Latency | 5 segments (5s) | 2 segments (1s) | 80% reduction |
| Timeout | 2-4s | 1s | 50-75% faster |

---

**Last Updated**: 2025-01-27  
**Version**: 3.0 (Real-Time Optimized)

