# Stream Management Improvements

## Problem
Users were encountering 500 errors when clicking "Play" multiple times on the same stream:
```
WARNING:stream_manager:Stream camera1_MediaProfile00000 is already running
INFO:werkzeug:127.0.0.1 - - [06/Oct/2025 17:54:31] "POST /api/streams/start HTTP/1.1" 500 -
```

This happened because:
1. Stream was already running but Flask returned 500 error
2. No way to reuse existing streams
3. Dead streams weren't being cleaned up
4. Race conditions when clicking Play rapidly

---

## Solutions Implemented

### 1. Graceful Handling of Already-Running Streams ✅

**Changed**: When a stream is already running, return success with existing stream info instead of error

**Before**:
```python
if stream_id in self.active_streams:
    if self.is_stream_active(stream_id):
        logger.warning(f"Stream {stream_id} is already running")
        return False  # ❌ Returns error
```

**After**:
```python
if stream_id in self.active_streams:
    if self.is_stream_active(stream_id):
        logger.info(f"Stream {stream_id} is already running, reusing existing stream")
        return True  # ✅ Returns success, reuses stream
```

**Result**: No more 500 errors, stream just plays immediately

---

### 2. API Response Enhancement ✅

**Added `already_running` flag** to API response:

```python
# Check if stream is already running
existing_stream = stream_manager.get_stream_info(stream_id)
if existing_stream and existing_stream['is_active']:
    return jsonify({
        'success': True,
        'stream_id': stream_id,
        'playlist_url': existing_stream['playlist_url'],
        'already_running': True,  # ✅ Tell frontend it's reusing stream
        'uptime': existing_stream['uptime']
    })
```

**Benefits**:
- Frontend knows if it's a new or existing stream
- Can optimize playback startup time
- Better user feedback

---

### 3. Frontend Optimization ✅

**Viewer.html now handles existing streams differently**:

```javascript
if (response.already_running) {
    // Stream already running, start playback immediately
    console.log('Stream already running for', response.uptime, 'seconds');
    updateStreamStatus('Connecting to existing stream...');
    setTimeout(() => {
        initHLSPlayer(playlistUrl);
    }, 500); // ✅ Only 0.5s delay
} else {
    // New stream, wait for ffmpeg to generate segments
    updateStreamStatus('Waiting for stream initialization...');
    setTimeout(() => {
        initHLSPlayer(playlistUrl);
    }, 2000); // 2s delay for ffmpeg startup
}
```

**Result**: Faster playback when reusing streams (0.5s vs 2s)

---

### 4. Dead Stream Cleanup ✅

**Added automatic cleanup** for streams where ffmpeg has died:

```python
def cleanup_dead_streams(self):
    """Remove dead streams from active streams registry"""
    with self._lock:
        dead_streams = []
        for stream_id in list(self.active_streams.keys()):
            if not self.is_stream_active(stream_id):
                dead_streams.append(stream_id)
        
        for stream_id in dead_streams:
            logger.warning(f"Cleaning up dead stream: {stream_id}")
            self._stop_stream_internal(stream_id)
        
        return len(dead_streams)
```

**Trigger methods**:
1. **On-demand**: `POST /api/streams/cleanup`
2. **Automatic**: Every 5 minutes via background thread
3. **On-start**: Cleans dead streams when starting a new one

---

### 5. Background Cleanup Thread ✅

**Added periodic cleanup** in app.py:

```python
def periodic_cleanup():
    """Background thread to cleanup dead streams periodically"""
    while not cleanup_event.is_set():
        cleanup_event.wait(300)  # Check every 5 minutes
        if not cleanup_event.is_set():
            count = stream_manager.cleanup_dead_streams()
            if count > 0:
                logger.info(f"Periodic cleanup: removed {count} dead stream(s)")

cleanup_thread = Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()
```

**Benefits**:
- Automatic cleanup without user intervention
- Prevents stream registry from growing indefinitely
- Handles ffmpeg crashes gracefully

---

### 6. Thread-Safe Operations ✅

**Separated internal cleanup** to avoid deadlocks:

```python
def _stop_stream_internal(self, stream_id: str):
    """Internal method to stop stream without lock"""
    # Called from within locked context
    # Safely terminates ffmpeg and removes from registry

def stop_stream(self, stream_id: str) -> bool:
    """Public method to stop stream with lock"""
    with self._lock:
        self._stop_stream_internal(stream_id)
```

**Why**: Prevents deadlock when cleanup is called from within locked context

---

## New API Endpoints

### `POST /api/streams/cleanup`
Manually trigger cleanup of dead streams

**Request**: No body required

**Response**:
```json
{
  "success": true,
  "cleaned_up": 2,
  "message": "Cleaned up 2 dead stream(s)"
}
```

---

## Benefits Summary

| Issue | Before | After |
|-------|--------|-------|
| **Double-click Play** | 500 Error | Works, reuses stream |
| **Stream reuse** | Not possible | Automatic |
| **Dead streams** | Accumulate forever | Auto-cleaned every 5min |
| **Startup time** | Always 2s | 0.5s for existing, 2s for new |
| **Error messages** | "Stream already running" warning | Informative "reusing stream" |
| **Thread safety** | Potential deadlocks | Safe with internal methods |

---

## Testing

### Test 1: Rapid Play Clicks
```
1. Go to viewer page
2. Click Play button 5 times rapidly
3. Expected: No errors, video plays once
4. Check logs: Should see "already running, reusing existing stream"
```

### Test 2: Stream Recovery
```
1. Start a stream
2. Kill ffmpeg manually: kill -9 $(pgrep ffmpeg)
3. Try to play again
4. Expected: Dead stream cleaned up, new stream starts
```

### Test 3: Manual Cleanup
```bash
# Start some streams
curl -X POST http://localhost:5001/api/streams/start \
  -H "Content-Type: application/json" \
  -d '{"camera_id": 1, "profile_token": "MediaProfile00000"}'

# Kill ffmpeg
killall ffmpeg

# Trigger cleanup
curl -X POST http://localhost:5001/api/streams/cleanup

# Response should show cleaned_up > 0
```

### Test 4: Automatic Cleanup
```
1. Start a stream
2. Wait for it to initialize
3. Kill ffmpeg process
4. Wait 5 minutes
5. Check logs: Should see "Periodic cleanup: removed 1 dead stream(s)"
```

---

## Monitoring

### Check Active Streams
```bash
curl http://localhost:5001/api/streams/all
```

### Check ffmpeg Processes
```bash
ps aux | grep ffmpeg | grep -v grep
```

### Watch Stream Directory
```bash
watch -n 1 'ls -lh static/streams/*/stream.m3u8'
```

---

## Configuration

### Cleanup Interval
Change in `app.py`:
```python
cleanup_event.wait(300)  # 300 seconds = 5 minutes
```

Adjust based on your needs:
- **Production**: 300-600s (5-10 min)
- **Development**: 60-120s (1-2 min)
- **High traffic**: 120-180s (2-3 min)

### Stream Timeout
Streams don't timeout automatically. They run until:
1. User clicks Stop
2. ffmpeg crashes/dies
3. Application shuts down
4. Manual cleanup is triggered

To add timeout, you could add:
```python
def cleanup_inactive_streams(self, max_idle_time: int = 3600):
    """Stop streams that haven't been accessed in X seconds"""
    # Track last access time per stream
    # Stop if current_time - last_access > max_idle_time
```

---

## Error Handling

All operations now handle errors gracefully:

```python
try:
    process.terminate()
    process.wait(timeout=5)
except subprocess.TimeoutExpired:
    logger.warning(f"Stream {stream_id} did not terminate, killing...")
    process.kill()
    process.wait()
except Exception as e:
    logger.error(f"Error stopping stream {stream_id}: {e}")
```

No more unhandled exceptions that crash the stream manager.

---

## Future Enhancements

### 1. Stream Health Monitoring
Add periodic health checks:
```python
def check_stream_health(self, stream_id: str) -> bool:
    """Verify stream is generating segments"""
    # Check if new segments are being created
    # Check if ffmpeg stderr has errors
    # Return False if unhealthy
```

### 2. Automatic Recovery
Restart failed streams:
```python
def auto_recover_stream(self, stream_id: str):
    """Attempt to restart a failed stream"""
    if not self.is_stream_active(stream_id):
        # Extract original parameters
        # Restart stream automatically
```

### 3. Stream Limits
Prevent resource exhaustion:
```python
MAX_CONCURRENT_STREAMS = 10

def start_stream(self, ...):
    if len(self.active_streams) >= MAX_CONCURRENT_STREAMS:
        return False, "Maximum concurrent streams reached"
```

### 4. Stream Analytics
Track usage metrics:
```python
def get_stream_metrics(self):
    return {
        'total_started': self.total_started,
        'total_stopped': self.total_stopped,
        'average_uptime': self.avg_uptime,
        'failure_rate': self.failures / self.total_started
    }
```

---

## Summary

The improved stream management system now:
- ✅ Handles rapid Play button clicks gracefully
- ✅ Reuses existing streams automatically
- ✅ Cleans up dead streams automatically
- ✅ Provides better user feedback
- ✅ Is thread-safe and deadlock-free
- ✅ Optimizes playback startup time
- ✅ Logs all operations clearly

No more 500 errors when clicking Play multiple times! 🎉
