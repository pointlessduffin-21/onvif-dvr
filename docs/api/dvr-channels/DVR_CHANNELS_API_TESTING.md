# DVR Channels API - Testing Guide

## Testing the API

### 1. Using cURL

#### Get all DVRs and channels
```bash
curl -X GET http://localhost:8821/api/dvr/channels
```

#### Get specific DVR's channels
```bash
curl -X GET http://localhost:8821/api/dvr/1/channels
```

#### Get with pretty printing
```bash
curl -s http://localhost:8821/api/dvr/channels | jq .
```

#### Extract RTSP feeds
```bash
curl -s http://localhost:8821/api/dvr/channels | jq -r '.[] | .channels[] | .rtsp_feed'
```

#### Extract iframe URLs
```bash
curl -s http://localhost:8821/api/dvr/channels | jq -r '.[] | .channels[] | .iframe'
```

---

### 2. Using Python

#### Simple test
```python
import requests
import json

# Get all channels
response = requests.get('http://localhost:8821/api/dvr/channels')
print(json.dumps(response.json(), indent=2))
```

#### Get specific DVR
```python
import requests

dvr_id = 1
response = requests.get(f'http://localhost:8821/api/dvr/{dvr_id}/channels')
dvr = response.json()

print(f"DVR: {dvr['dvr_name']}")
print(f"Status: {dvr['status']}")
print(f"Channels: {len(dvr['channels'])}")

for channel in dvr['channels']:
    status_text = "Online" if channel['status'] == 1 else "Offline"
    print(f"  - {channel['channel_name']} ({status_text})")
    print(f"    RTSP: {channel['rtsp_feed']}")
```

#### Save RTSP URLs to file
```python
import requests
import json

response = requests.get('http://localhost:8821/api/dvr/channels')
data = response.json()

with open('rtsp_feeds.json', 'w') as f:
    feeds = {}
    for dvr in data:
        feeds[dvr['dvr_name']] = {
            'host': dvr['dvr_host'],
            'channels': [
                {
                    'name': ch['channel_name'],
                    'rtsp': ch['rtsp_feed']
                }
                for ch in dvr['channels']
            ]
        }
    json.dump(feeds, f, indent=2)
```

---

### 3. Using JavaScript/Node.js

#### Basic fetch
```javascript
fetch('/api/dvr/channels')
  .then(response => response.json())
  .then(data => console.log(JSON.stringify(data, null, 2)))
  .catch(error => console.error('Error:', error));
```

#### Get channels for display
```javascript
async function getDVRChannels() {
  const response = await fetch('/api/dvr/channels');
  const dvrs = await response.json();
  
  const html = dvrs.map(dvr => `
    <div class="dvr">
      <h3>${dvr.dvr_name}</h3>
      <p>Status: ${dvr.status}</p>
      <div class="channels">
        ${dvr.channels.map(ch => `
          <div class="channel">
            <h4>${ch.channel_name}</h4>
            <p>Status: ${ch.status === 1 ? 'Online' : 'Offline'}</p>
            <p>Resolution: ${ch.resolution} @ ${ch.framerate}fps</p>
            <p>RTSP: <code>${ch.rtsp_feed}</code></p>
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
  
  document.getElementById('dvr-list').innerHTML = html;
}

getDVRChannels();
```

#### Create video player
```javascript
async function createVideoPlayer(dvrId, containerId) {
  const response = await fetch(`/api/dvr/${dvrId}/channels`);
  const dvr = await response.json();
  
  if (dvr.error) {
    console.error('Error:', dvr.error);
    return;
  }
  
  const container = document.getElementById(containerId);
  
  dvr.channels.forEach((channel, index) => {
    const player = document.createElement('div');
    player.className = 'video-player';
    
    const iframe = document.createElement('iframe');
    iframe.src = channel.iframe;
    iframe.width = '640';
    iframe.height = '480';
    iframe.frameborder = '0';
    
    const title = document.createElement('h4');
    title.textContent = channel.channel_name;
    
    player.appendChild(title);
    player.appendChild(iframe);
    container.appendChild(player);
  });
}

// Usage
createVideoPlayer(1, 'video-container');
```

---

### 4. Using Postman

1. **Create new GET request**
   - URL: `http://localhost:8821/api/dvr/channels`

2. **Test with parameters**
   - URL: `http://localhost:8821/api/dvr/channels?dvr_id=1`
   - Params tab: Add `dvr_id` = `1`

3. **Save response**
   - Click "Tests" tab
   - Add test script:
   ```javascript
   pm.environment.set("dvr_response", JSON.stringify(pm.response.json()));
   ```

4. **Extract values**
   - Tests tab:
   ```javascript
   pm.test("Check DVR online", function() {
     pm.expect(pm.response.json().status).to.equal("online");
   });
   ```

---

### 5. Using HTTPie

```bash
# Simple request
http http://localhost:8821/api/dvr/channels

# Pretty print
http --pretty=all http://localhost:8821/api/dvr/channels

# Save response
http http://localhost:8821/api/dvr/channels > dvr_data.json

# Extract specific fields
http http://localhost:8821/api/dvr/channels | grep -o '"rtsp_feed":"[^"]*"'

# With query parameters
http http://localhost:8821/api/dvr/channels dvr_id==1
```

---

### 6. Integration Testing Script

```python
#!/usr/bin/env python3

import requests
import sys
from datetime import datetime

BASE_URL = "http://localhost:8821"

def test_get_all_channels():
    """Test getting all channels"""
    print("[TEST] Getting all channels...")
    try:
        response = requests.get(f"{BASE_URL}/api/dvr/channels")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Found {len(data)} DVRs")
        return data
    except Exception as e:
        print(f"✗ Failed: {e}")
        return None

def test_get_specific_dvr(dvr_id=1):
    """Test getting specific DVR"""
    print(f"[TEST] Getting DVR {dvr_id}...")
    try:
        response = requests.get(f"{BASE_URL}/api/dvr/{dvr_id}/channels")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert 'dvr_id' in data, "Response missing dvr_id"
        assert 'channels' in data, "Response missing channels"
        print(f"✓ DVR: {data['dvr_name']}, Channels: {len(data['channels'])}")
        return data
    except Exception as e:
        print(f"✗ Failed: {e}")
        return None

def test_channel_structure(dvr):
    """Test channel data structure"""
    print("[TEST] Validating channel structure...")
    required_fields = [
        'channel_id', 'channel_name', 'status',
        'rtsp_feed', 'iframe', 'codec', 'resolution'
    ]
    
    for channel in dvr['channels']:
        for field in required_fields:
            assert field in channel, f"Channel missing {field}"
        
        # Validate types
        assert isinstance(channel['status'], int), "status should be int"
        assert channel['status'] in [0, 1], "status should be 0 or 1"
        assert channel['rtsp_feed'].startswith('rtsp://'), "Invalid RTSP URL"
        assert 'iframe' in channel['iframe'], "Invalid iframe URL"
    
    print(f"✓ All {len(dvr['channels'])} channels valid")

def run_tests():
    """Run all tests"""
    print(f"Starting DVR Channels API Tests - {datetime.now().isoformat()}\n")
    
    # Test 1: Get all channels
    all_dvrs = test_get_all_channels()
    if not all_dvrs:
        print("\n✗ Tests failed!")
        sys.exit(1)
    
    print()
    
    # Test 2: Get specific DVR
    if all_dvrs:
        dvr_id = all_dvrs[0]['dvr_id'] if all_dvrs else 1
        specific_dvr = test_get_specific_dvr(dvr_id)
        if specific_dvr:
            print()
            # Test 3: Validate structure
            test_channel_structure(specific_dvr)
    
    print(f"\n✓ All tests passed! - {datetime.now().isoformat()}")

if __name__ == "__main__":
    run_tests()
```

Save as `test_dvr_api.py` and run:
```bash
python3 test_dvr_api.py
```

---

### 7. Load Testing with Apache Bench

```bash
# Simple load test
ab -n 100 -c 10 http://localhost:8821/api/dvr/channels

# With URL encoding
ab -n 1000 -c 50 'http://localhost:8821/api/dvr/channels?dvr_id=1'
```

---

### 8. Docker Testing

If running in Docker:

```bash
# Execute curl inside container
docker exec onvif-dvr curl http://localhost:8821/api/dvr/channels

# Pretty print inside container
docker exec onvif-dvr sh -c 'curl -s http://localhost:8821/api/dvr/channels | python3 -m json.tool'
```

---

## Troubleshooting

### API not responding
```bash
# Check if service is running
curl http://localhost:8821/

# Check logs
docker logs onvif-dvr

# Verify database
sqlite3 onvif_viewer.db ".tables"
```

### Invalid JSON response
```bash
# Validate response format
curl -s http://localhost:8821/api/dvr/channels | python3 -m json.tool

# Check for errors
curl -v http://localhost:8821/api/dvr/channels
```

### No channels returned
```bash
# Check database has data
sqlite3 onvif_viewer.db "SELECT COUNT(*) FROM cameras;"
sqlite3 onvif_viewer.db "SELECT COUNT(*) FROM video_streams;"

# Refresh camera profiles
curl -X POST http://localhost:8821/api/cameras/refresh
```

