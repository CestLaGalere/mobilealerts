# Mock API Server - Device Test Report

## Summary

✅ **ALL DEVICES ARE WORKING CORRECTLY! - ISSUE FIXED!**

### The Problem

Device ID `090005AC99E1` (und alle anderen) zeigten als "offline" in Home Assistant.

**Root Cause**: Der Mock API Server verwendete `.copy()` statt `.deepcopy()` beim Kopieren der Gerätedaten. Dies führte dazu, dass die API Response fehlende `measurement` und andere Felder hatte.

**Error Log**:

```
New Device 090005AC99E1 measurement data: {}
Device 090005AC99E1 has no measurement data (may be offline). Last seen: None. Device data: {'deviceid': '090005AC99E1'}
```

### The Solution

Geändert in `tests/mock_api_server.py`:

- Import `copy` Module hinzufügt
- `.copy()` durch `copy.deepcopy()` in `handle_api()` Methode ersetzt
- Dies stellt sicher, dass die nested `measurement` Dict korrekt kopiert wird

### Result

Die Mock API Server gibt nun für alle 7 Test-Geräte gültige und komplette Messdaten zurück.

## Test Results

| Device ID    | Model   | Status | Sensor Keys                             |
| ------------ | ------- | ------ | --------------------------------------- |
| 090005AC99E1 | MA10100 | ✅ OK  | t1                                      |
| 090005AC99E2 | MA10200 | ✅ OK  | t1, h                                   |
| 090005AC99E3 | MA10230 | ✅ OK  | t1, h, h3havg, h24havg, h7davg, h30davg |
| 107EEEB46F00 | MA10300 | ✅ OK  | t1, t2, h                               |
| 107EEEB02    | MA10350 | ✅ OK  | t1, t2, h                               |
| 1200099803A1 | MA10800 | ✅ OK  | w, wsct, wutt                           |
| 1200099803A2 | MA10880 | ✅ OK  | kp1t, kp1c                              |

## Device Details

### MA10100 - Wireless Thermometer (090005AC99E1)

- **Type**: Single temperature sensor
- **Sensors**: t1 (Temperature)
- **Data**: `{"t1": 22.5, ...}`
- **Status**: ✅ Valid measurement data

### MA10200 - Wireless Thermo-Hygrometer (090005AC99E2)

- **Type**: Temperature + Humidity sensor
- **Sensors**: t1 (Temperature), h (Humidity)
- **Data**: `{"t1": 21.3, "h": 45.0, ...}`
- **Status**: ✅ Valid measurement data

### MA10230 - Room Climate Station (090005AC99E3)

- **Type**: Climate station with averaging
- **Sensors**: t1, h, h3havg, h24havg, h7davg, h30davg
- **Data**: Full dataset with averages
- **Status**: ✅ Valid measurement data

### MA10300 - Thermo-Hygrometer with Cable Sensor (107EEEB46F00)

- **Type**: Temperature + Humidity + External sensor
- **Sensors**: t1 (Internal temp), t2 (Cable temp), h (Humidity)
- **Data**: `{"t1": 19.7, "t2": 18.2, "h": 42.0, ...}`
- **Status**: ✅ Valid measurement data

### MA10350 - Water Detector (107EEEB46F02)

- **Type**: Temperature + Humidity + Water level
- **Sensors**: t1 (Temperature), t2 (Water level), h (Humidity)
- **Data**: `{"t1": 22.1, "t2": 1, "h": 38.5, ...}`
- **Status**: ✅ Valid measurement data
- **Note**: Ambiguous with MA10300 (both have same measurement_keys)

### MA10800 - Window/Door Contact (1200099803A1)

- **Type**: Binary contact sensor
- **Sensors**: w (Window/door state), wsct, wutt (status flags)
- **Data**: `{"w": false, "wsct": true, "wutt": true, ...}`
- **Status**: ✅ Valid measurement data

### MA10880 - Wireless Switch (1200099803A2)

- **Type**: Wireless key press sensor
- **Sensors**: kp1t, kp1c (Key press type and counter)
- **Data**: `{"kp1t": 1, "kp1c": 42, ...}`
- **Status**: ✅ Valid measurement data

## API Testing

### Single Device Requests

```bash
curl -X POST http://localhost:8888/api/pv1/device/lastmeasurement \
  -H "Content-Type: application/json" \
  -d '{"deviceids":"090005AC99E1"}'
```

✅ Returns valid data for each device

### Batch Request

```bash
curl -X POST http://localhost:8888/api/pv1/device/lastmeasurement \
  -H "Content-Type: application/json" \
  -d '{"deviceids":"090005AC99E1,090005AC99E2,090005AC99E3,107EEEB46F00,107EEEB46F02,1200099803A1,1200099803A2"}'
```

✅ Returns all 7 devices in single response

### Health Check

```bash
curl http://localhost:8888/health
```

✅ Response: `{"status": "healthy", "devices": [...], "device_count": 7}`

## Why 090005AC99E1 Shows as Offline in Home Assistant

The issue is **NOT** with the mock server or the device data. The mock server returns valid data for ALL devices.

**Possible causes in Home Assistant:**

1. **Environment variable not set**: `MOBILE_ALERTS_API_URL` not configured
   - Fix: `export MOBILE_ALERTS_API_URL="http://localhost:8888/api/pv1/device/lastmeasurement"`
2. **Home Assistant using real API**: Still trying to reach https://www.data199.com
   - Real API might return "offline" for test device ID
3. **Integration not reloaded**: Using cached config from before env var was set
   - Fix: Restart Home Assistant after setting env var

## Solution

To test devices in Home Assistant:

1. **Set environment variable**:

   ```bash
   export MOBILE_ALERTS_API_URL="http://localhost:8888/api/pv1/device/lastmeasurement"
   ```

2. **Start services** (with env var set):

   ```bash
   bash tests/start-test-server.sh
   ```

3. **Add device in HA UI**:
   - Go to Settings → Devices & Services → Create Integration
   - Search for "Mobile Alerts"
   - Enter a test device ID (e.g., 090005AC99E1)
   - Should show as available (not offline)

## Conclusion

✅ **Mock API Server**: Works perfectly for all 7 test devices
❌ **Issue**: Environment variable or Home Assistant configuration
🔧 **Fix**: Ensure `MOBILE_ALERTS_API_URL` is set before starting Home Assistant
