# Stream Management - Quick Reference

## Problem Solved
**Error**: `Stream already running` causing 500 errors when clicking Play multiple times

## Solution
✅ Streams are now automatically reused when already running  
✅ Dead streams are automatically cleaned up  
✅ No more 500 errors on rapid clicks  

---

## Key Changes

### 1. Reuse Existing Streams
- Clicking Play on an already-running stream now succeeds
- Returns `already_running: true` flag
- Faster playback (0.5s vs 2s delay)

### 2. Automatic Cleanup
- Dead streams removed every 5 minutes
- Manual cleanup: `POST /api/streams/cleanup`
- Cleanup on stream start if previous instance died

### 3. Better Feedback
- Frontend shows "Connecting to existing stream..." when reusing
- Logs show stream uptime
- Clear status messages

---

## New API Response

### `POST /api/streams/start`
```json
{
  "success": true,
  "stream_id": "camera1_MediaProfile00000",
  "playlist_url": "/static/streams/camera1_MediaProfile00000/stream.m3u8",
  "already_running": true,
  "uptime": 45.2
}
```

**Fields**:
- `already_running`: `true` if reusing existing stream, `false` if new
- `uptime`: How long stream has been running (seconds)

---

## New Endpoint

### `POST /api/streams/cleanup`
Manually clean up dead streams

**Response**:
```json
{
  "success": true,
  "cleaned_up": 2,
  "message": "Cleaned up 2 dead stream(s)"
}
```

---

## User Experience

### Before
1. Click Play → Stream starts → Video plays
2. Click Play again → ❌ 500 Error
3. Reload page → Click Play → Works

### After
1. Click Play → Stream starts → Video plays
2. Click Play again → ✅ Reuses stream → Video plays immediately
3. Click Play 10 more times → ✅ Still works

---

## Testing

Run automated tests:
```bash
python3 test_stream_management.py
```

Manual testing:
1. Open viewer page
2. Click Play button rapidly 5+ times
3. All clicks should succeed
4. Video should play smoothly

---

## Monitoring

### Check active streams:
```bash
curl http://localhost:5001/api/streams/all | jq
```

### Check stream status:
```bash
curl http://localhost:5001/api/streams/status/camera1_MediaProfile00000 | jq
```

### Trigger cleanup:
```bash
curl -X POST http://localhost:5001/api/streams/cleanup | jq
```

---

## Configuration

### Change cleanup interval
In `app.py`, line ~38:
```python
cleanup_event.wait(300)  # 300 = 5 minutes
```

Options:
- Development: `60` (1 minute)
- Production: `300-600` (5-10 minutes)
- High traffic: `120-180` (2-3 minutes)

---

## Files Modified

1. **stream_manager.py**
   - Changed: Return `True` for already-running streams
   - Added: `cleanup_dead_streams()` method
   - Added: `_stop_stream_internal()` for thread safety

2. **app.py**
   - Added: Check for existing streams before starting
   - Added: `already_running` flag in response
   - Added: `/api/streams/cleanup` endpoint
   - Added: Background cleanup thread
   - Added: Logging configuration

3. **templates/viewer.html**
   - Added: Faster playback for existing streams (0.5s vs 2s)
   - Added: Status message for reusing streams

---

## Summary

✅ **Problem**: 500 errors on double-click Play  
✅ **Solution**: Reuse existing streams automatically  
✅ **Benefit**: Better UX, no errors, faster playback  
✅ **Maintenance**: Automatic cleanup of dead streams  
✅ **Monitoring**: New endpoints to check stream status  

The stream management system is now production-ready! 🎉
