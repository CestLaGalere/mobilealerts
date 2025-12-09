# Manual Testing Guide - Mobile Alerts Integration

## Overview

This guide explains how to manually test the Mobile Alerts Home Assistant integration. You can choose between:

- **Mock API** - Test with simulated devices (no real hardware needed)
- **Real API** - Test with your actual Mobile Alerts devices

The test environment automatically sets up Home Assistant with the Mobile Alerts integration.

## Quick Start

### 1. Start the Test Environment

```bash
cd /workspaces/mobilealerts
bash scripts/start-ha.sh
```

You will be prompted to choose:

1. **Mock API** (default) - For testing without real devices
2. **Real API** - For testing with actual Mobile Alerts devices

The script will then:

- ✅ Start Mock API Server on port 8888 (if option 1 selected)
- ✅ Start Home Assistant on port 8123
- ✅ Create symlink to `custom_components/mobile_alerts` in config directory
- ✅ Configure environment variables (Mock API only)
- ✅ Display available test devices (Mock API only)

**Mock API vs Real API:**

- **Mock API** (Option 1):

  - Uses test devices with fake data
  - No internet connection required
  - Sets `MOBILE_ALERTS_API_URL` to `http://localhost:8888`
  - Perfect for development and testing

- **Real API** (Option 2):
  - Connects to actual Mobile Alerts cloud service
  - Requires real devices and internet connection
  - No `MOBILE_ALERTS_API_URL` set (uses default production API)
  - Use your real Device IDs from the Mobile Alerts app

**Important:** The script automatically creates a symlink so Home Assistant finds the Mobile Alerts integration:

```bash
ln -s /workspaces/mobilealerts/custom_components /workspaces/mobilealerts/config/custom_components
```

This is why the integration shows up in Home Assistant UI.

### 2. Open Home Assistant UI

Open your browser to: **http://localhost:8123**

Attention: port forwarding in VS Code 8123 to localhost:8123 must be active, because HA runs in dev container connected via WDSL or SSH remote extension.

### 3. Add a Device

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Mobile Alerts**
4. Enter a Device ID:
   - **Mock API**: Use test Device IDs (see table below)
   - **Real API**: Use your actual Device ID from Mobile Alerts app
5. Watch the detection and sensor creation

### 4. Stop the Test Environment

```bash
bash scripts/stop-services.sh
```

### 5. Reset Home Assistant (Clean Slate)

If you need to reset Home Assistant to a clean state (e.g., after testing, corrupted data, or onboarding issues):

```bash
bash scripts/reset-ha.sh
```

This interactive script will:

- ✅ Stop Home Assistant and Mock API Server
- ✅ Remove all runtime files (.storage, database, logs, etc.)
- ✅ Ask you how to handle configuration.yaml:
  - **Option 1:** Keep current configuration
  - **Option 2:** Restore default test configuration (from `tests/default_configuration.yaml`)
  - **Option 3:** Restore from Git (git checkout)
- ✅ Keep only `configuration.yaml` (based on your choice)

**When to use reset:**

- Home Assistant shows "Unable to connect"
- Onboarding stuck or failed
- Testing different configurations
- Starting fresh after integration changes

After reset, simply run `bash scripts/start-ha.sh` again to start with a clean environment.

## Test Device IDs (Mock API Only)

When using **Mock API** (Option 1), these test devices are available:

The mock server provides these test devices:

| Device ID      | Model   | Type                                | Test Case                        |
| -------------- | ------- | ----------------------------------- | -------------------------------- |
| `090005AC99E1` | MA10100 | Thermometer                         | t1                               |
| `090005AC99E2` | MA10300 | Thermo-Hygrometer                   | t1,t2,h                          |
| `090005AC99E3` | MA10230 | Room Climate Station                | Many keys + averages             |
| `107EEEB46F00` | MA10300 | Thermo-Hygrometer with Cable Sensor | t2 = cable temp                  |
| `107EEEB46F02` | MA10350 | Water Detector                      | **Ambiguous** - t2 = water level |
| `1200099803A1` | MA10800 | Window/Door Contact                 | Boolean sensor                   |
| `1200099803A2` | MA10880 | Wireless Switch                     | Key press events                 |

### Important: MA10300 vs MA10350 Ambiguity

**MA10300** and **MA10350** have identical measurement keys: `{t1, t2, h}`

But `t2` means different things:

- **MA10300**: t2 = Cable temperature → Creates `MobileAlertsTemperatureSensor`
- **MA10350**: t2 = Water level → Creates `MobileAlertsWaterSensor`

**Test this by:**

1. Adding device `107EEEB46F00` (MA10300) - should show Temperature sensor for t2
2. Adding device `107EEEB46F02` (MA10350) - should show Water sensor for t2
   - **First time?** You'll be asked which model you have (both options match the data)
   - **Select MA10350** → Water sensor is created ✅

---

## File Structure

```
tests/
├── mock_api_server.py         # Mock API server (provides fake device data)
└── default_configuration.yaml # Default test configuration for HA


scripts/
├── start-ha.sh                # Start Home Assistant with mock server
├── stop-services.sh           # Stop all services
├── reset-ha.sh                # Reset HA to clean state (interactive)
├── setup.sh                   # Initial project setup
└── Manual Testing Scripts.md  # This file
```

---

## How the Mock API Server Works

### Test Data

The mock server simulates real Mobile Alerts devices:

```python
TEST_DEVICES = {
    "107EEEB46F02": {
        "name": "MA10350 - Water Detector",
        "model": "MA10350",
        "measurement": {
            "t1": 22.1,      # Temperature
            "t2": 1,         # Water detected (0=no, 1=yes)
            "h": 38.5,       # Humidity
        }
    }
}
```

### API Endpoints

The mock server provides these endpoints:

| Endpoint                          | Method | Purpose                      |
| --------------------------------- | ------ | ---------------------------- |
| `/api/pv1/device/lastmeasurement` | POST   | Fetch device data (main API) |
| `/api/pv1/device/register`        | POST   | Register a device            |
| `/health`                         | GET    | Health check                 |

### Health Check

Verify the mock server is running:

```bash
curl http://localhost:8888/health
```

Response:

```json
{
  "status": "healthy",
  "devices": ["090005AC99E1", "090005AC99E2", ...],
  "device_count": 7
}
```

---

## Troubleshooting

### Port Already in Use

**Problem:** `Address already in use`

**Solution:**

```bash
# Kill existing processes
bash scripts/stop-ha.sh

# Or manually specify different ports
export MOCK_API_PORT=9999
bash scripts/start-ha.sh
```

### Home Assistant Not Starting

**Problem:** Stuck on "Waiting for Home Assistant to start"

**Solution:**

1. Check if port 8123 is in use: `lsof -i :8123`
2. Kill existing process: `bash tests/stop-test-server.sh`
3. Check Home Assistant logs: `~/.homeassistant/home-assistant.log`

### Device Not Found

**Problem:** "Device not found" error when adding device

**Solution:**

1. Make sure you're using a valid test Device ID (see table above)
2. Check mock server is running: `curl http://localhost:8888/health`
3. Verify Device ID in logs: `docker logs <container>`

### API Connection Failed

**Problem:** Home Assistant can't connect to API

**Solution:**

1. Verify environment variable is set:

   ```bash
   echo $MOBILE_ALERTS_API_URL
   # Should output: http://localhost:8888/api/pv1/device/lastmeasurement
   ```

2. Test API manually:
   ```bash
   curl -X POST http://localhost:8888/api/pv1/device/lastmeasurement \
     -H "Content-Type: application/json" \
     -d '{"deviceids":"107EEEB46F02"}'
   ```

---

## Testing Specific Features

### Test 1: Device Detection

**Goal:** Verify automatic device model detection

1. Add `090005AC99E1` (MA10100 - only t1)

   - ✅ Should be detected as MA10100
   - ✅ Creates Temperature sensor for t1

2. Add `090005AC99E3` (MA10230 - t1, h, h3havg, h24havg, h7davg, h30davg)
   - ✅ Should be detected as MA10230
   - ✅ Creates sensors for all keys

### Test 2: Ambiguous Device Detection

**Goal:** Verify disambiguation dialog for MA10300 vs MA10350

1. Add `107EEEB46F00` (MA10300)

   - ✅ Should be detected automatically (no dialog)
   - ✅ t2 creates Temperature sensor

2. Add `107EEEB46F02` (MA10350)
   - ⚠️ May show dialog asking "Which device is this?"
   - ✅ Select "MA10350"
   - ✅ t2 creates Water sensor

### Test 3: Boolean Sensors

**Goal:** Verify window/door contact sensor (MA10800)

1. Add `1200099803A1` (MA10800)
   - ✅ Should be detected as MA10800
   - ✅ Creates Binary Sensor (Contact) for `w` key
   - ✅ Shows as "Open/Closed" in UI

### Test 4: Sensor Type Override

**Goal:** Verify MA10350 uses WaterSensor for t2 (not TemperatureSensor)

1. Compare sensors:
   - MA10300 `t2`: Shows as "Cable Temperature" (°C)
   - MA10350 `t2`: Shows as "Water" (0/1 or on/off)

---

## Environment Variables

### `MOBILE_ALERTS_API_URL`

This environment variable controls which API Home Assistant uses:

- **Not set** (default): Uses production Mobile Alerts API
- **Set to mock URL**: Uses local test server

The `start-ha.sh` script automatically manages this:

- **Option 1 (Mock API)**: Sets `MOBILE_ALERTS_API_URL=http://localhost:8888/api/pv1/device/lastmeasurement`
- **Option 2 (Real API)**: Variable is unset (uses production API)

You can also set it manually:

```bash
# Use real API
unset MOBILE_ALERTS_API_URL

# Use mock server
export MOBILE_ALERTS_API_URL="http://localhost:8888/api/pv1/device/lastmeasurement"
```

### `MOCK_API_PORT`

Change the mock server port:

```bash
export MOCK_API_PORT=9999
bash scripts/start-ha.sh
```

---

## Common Test Scenarios

### Scenario 1: New Device Setup (MA10350)

```
1. Run: bash tests/start-test-server.sh
2. Open: http://localhost:8123
3. Settings → Devices & Services → Create Integration
4. Search: Mobile Alerts
5. Device ID: 107EEEB46F02
6. Name: My Water Sensor (optional)
7. Submit
   → Dialog appears: "Select Device Model"
   → Choose: MA10350 - Wireless Thermo-Hygrometer with Water Detector
8. ✅ Device created with Water, Temperature, Humidity sensors
```

### Scenario 2: Testing All Devices

```bash
# Run all test devices in sequence
for DEVICE in 090005AC99E1 090005AC99E2 090005AC99E3 107EEEB46F00 107EEEB46F02 1200099803A1 1200099803A2; do
    echo "Adding $DEVICE"
    # Use HA API or UI to add device
done
```

### Scenario 3: Verify Sensor Types

```
1. Add all devices from "Test Device IDs" table
2. Go to Settings → Devices & Services → Entities
3. Verify sensor types:
   - t1, t3, t4, h, h1-h4: Sensor (temperature/humidity)
   - t2 (MA10300): Sensor (temperature)
   - t2 (MA10350): Sensor (water/binary)
   - w (MA10800): Binary Sensor (contact)
```

---

## Advanced: Modify Test Data

To change what the mock server returns, edit `tests/mock_api_server.py`:

```python
TEST_DEVICES["107EEEB46F02"] = {
    "name": "MA10350 - Water Detector",
    "measurement": {
        "t1": 22.1,      # Modify temperature
        "t2": 1,         # 0 = no water, 1 = water detected
        "h": 38.5,       # Modify humidity
    }
}
```

Then restart the server for changes to take effect.

---

## Troubleshooting

### "Mobile Alerts integration not found in Home Assistant"

**Problem:** The integration doesn't appear in the "Create Integration" list.

**Solution:**

1. Check if symlink was created:

   ```bash
   ls -la ~/.homeassistant/custom_components/
   ```

2. If missing, create it manually:

   ```bash
   mkdir -p ~/.homeassistant/custom_components
   ln -s /workspaces/mobilealerts/custom_components/mobile_alerts ~/.homeassistant/custom_components/
   ```

3. Restart Home Assistant:
   ```bash
   bash tests/stop-test-server.sh
   bash tests/start-test-server.sh
   ```

### "Mock API Server is already running"

**Problem:** Script says server is already running.

**Solution:**

```bash
bash scripts/stop-ha.sh
# Wait 2 seconds
bash scripts/start-ha.sh
```

Or manually stop:

```bash
kill $(lsof -t -i:8888)
kill $(lsof -t -i:8123)
```

### "Device not found" error when adding a device

**Problem:** The device ID you entered doesn't exist in the mock server.

**Solution:**
Use one of the test Device IDs from the table above. Check your spelling (case-sensitive).

### Home Assistant shows "Recovery Mode"

**Problem:** Home Assistant couldn't start properly or shows "Unable to connect" after user creation.

**Solution:**

Use the reset script to clean everything:

```bash
bash scripts/reset-ha.sh
```

When prompted, choose:

- **Option 2** to restore default test configuration
- Or **Option 3** to restore from Git

Then start fresh:

```bash
bash scripts/start-ha.sh
```

**What the reset script does:**

- Stops all running services
- Removes `.storage/`, `home-assistant.log*`, `home-assistant_v2.db*`
- Removes `.HA_VERSION`, `.uuid`, `.ha_run.lock`
- Removes `deps/`, `blueprints/`, `custom_components/` (will be recreated by symlink)
- Restores `configuration.yaml` based on your choice

**Alternative (manual):**

```bash
bash scripts/stop-services.sh
rm -rf config/.storage config/home-assistant* config/.HA_VERSION config/deps
bash scripts/start-ha.sh
```

### "Ambiguous device" prompt on every device add

**Problem:** When adding MA10300 or MA10350, you see a model selection prompt each time.

**This is expected behavior!** Since both devices have identical measurement keys, the system asks you to clarify which one you have. This is by design to handle the disambiguation correctly.

---

## References

- [Mobile Alerts API Documentation](https://docs.mobilealerts.eu)
- [Home Assistant Developer Docs](https://developers.home-assistant.io)
- [Integration Testing Guide](../../docs/)

---

## Questions?

See the main README or open an issue on GitHub.
