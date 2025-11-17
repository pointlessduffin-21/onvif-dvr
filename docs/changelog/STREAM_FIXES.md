# Stream Issues - Fixes Applied

## Date: 2025-01-27

## Issues Fixed

### 1. RTSP URI Credential Duplication ✅

**Problem**: 
Streams were failing with malformed RTSP URIs like:
```
rtsp://admin:pass@admin:pass@host:554/...
rtsp://admin:pass@admin:pass@admin:pass@host:554/...
```

**Root Cause**:
- When recovering failed streams, the system was passing RTSP URIs that already had credentials embedded
- `start_stream()` was adding credentials again without checking if they already existed
- This caused exponential credential duplication on each recovery attempt

**Solution**:
- Added credential detection in `start_stream()` - checks if `@` exists in URI before adding credentials
- If credentials exist, extracts host part and replaces with fresh credentials
- Fixed `_recover_stream()` to extract clean URI before recovery

**Files Modified**:
- `stream_manager.py` - Lines 182-197, 128-137

### 2. Stream Detection - Only Channel 1 ✅

**Problem**:
Dahua provider was only creating streams for channel 1, missing all other channels on multi-channel DVRs.

**Root Cause**:
- `_build_default_streams()` was hardcoded to only create streams for channel 1
- No channel detection logic

**Solution**:
- Added `_detect_channels()` method with 3 detection strategies:
  1. Config API: `configManager.cgi?action=getConfig&name=ChannelCount`
  2. Channel probing: Tests channels 1-32 to find active ones
  3. Video input enumeration: `configManager.cgi?action=getConfig&name=VideoInput`
- Renamed `_build_default_streams()` to `_build_streams()` to support multiple channels
- Creates main and sub streams for each detected channel

**Files Modified**:
- `camera_providers/dahua.py` - Added channel detection and multi-channel stream building

### 3. Stream Labeling Improvements ✅

**Problem**:
Stream labels were inconsistent or missing, making it hard to identify streams.

**Solution**:
- Improved stream label generation in `save_camera_to_db_vendor()`
- Properly detects "Main Stream" vs "Sub Stream" from profile tokens
- Creates labels like "Channel 1 - Main Stream", "Channel 2 - Sub Stream"
- Added proper ordering in `get_streams()` endpoint

**Files Modified**:
- `onvif_manager.py` - Lines 503-537
- `app.py` - Lines 583-608

## Testing

After these fixes:
1. **Delete existing DVR** and re-add it to get all channels detected
2. **Check streams** - Should see all channels (not just channel 1)
3. **Test streaming** - Streams should start without credential duplication errors
4. **Check logs** - No more `@admin:pass@admin:pass@` patterns

## Expected Behavior

### Before Fix
- Only 2 streams (channel 1 main/sub)
- Credential duplication on recovery
- Streams dying and failing to recover
- Wrong streams displayed

### After Fix
- All channels detected (e.g., channels 1-8 for 8-channel DVR)
- 2 streams per channel (main + sub)
- Clean RTSP URIs without duplication
- Proper stream recovery
- Correct stream labels and ordering

## Manual Channel Detection

If automatic detection fails, you can manually specify channels when adding DVR:

```javascript
// In the add camera form, you could add a channels field
// Or use the refresh endpoint with channel options
```

For now, the system will:
1. Try to auto-detect channels
2. Fall back to channel 1 if detection fails
3. You can refresh the camera later to re-detect channels

---

**Status**: ✅ Fixed  
**Version**: 2.1

