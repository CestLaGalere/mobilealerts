# Mobile Alerts Integration - Testing

This directory contains tests and testing utilities for the Mobile Alerts Home Assistant integration.

## Quick Start

### Automatic Testing (Unit Tests)

```bash
# Run all unit tests
python -m pytest tests --timeout=10

# Run specific test file
python -m pytest tests/test_device_model_detection.py -v

# Run with coverage
python -m pytest tests --cov=custom_components.mobile_alerts --cov-report=term-missing
```

### Manual Testing with Mock Server

```bash
# Start mock API server + Home Assistant
bash tests/start-test-server.sh

# In another terminal, verify it's running
curl http://localhost:8888/health

# Stop all servers when done
bash tests/stop-test-server.sh
```

Then open **http://localhost:8123** in your browser.

## Files

### Test Runners

- **`start-test-server.sh`** - Start Mock API Server + Home Assistant for manual testing
- **`stop-test-server.sh`** - Stop all test servers
- **`mock_api_server.py`** - Mock Mobile Alerts API server with test devices

### Test Cases

- **`test_api.py`** - API communication tests
- **`test_device_model_detection.py`** - Device model detection logic
- **`test_config_flow.py`** - Configuration flow / UI integration
- **`test_init.py`** - Integration initialization
- **`test_sensor.py`** - Sensor entity creation

### Documentation

- **`MANUAL_TESTING.md`** - Comprehensive manual testing guide
- **`conftest.py`** - Pytest fixtures and configuration
- **`test_source.json`** - Sample API response data

## Environment Variables

### For Testing with Mock Server

```bash
# URL of the mock API server (set automatically by start-test-server.sh)
export MOBILE_ALERTS_API_URL="http://localhost:8888/api/pv1/device/lastmeasurement"

# Port for mock API server (default: 8888)
export MOCK_API_PORT=8888
```

## Test Devices

The mock server provides these test devices:

| Device ID      | Model   | Measurement Keys                               |
| -------------- | ------- | ---------------------------------------------- |
| `090005AC99E1` | MA10100 | `{t1}`                                         |
| `090005AC99E2` | MA10200 | `{t1, h}`                                      |
| `090005AC99E3` | MA10230 | `{t1, h, h3havg, h24havg, h7davg, h30davg}`    |
| `107EEEB46F00` | MA10300 | `{t1, t2, h}` (t2 = cable temp)                |
| `107EEEB46F02` | MA10350 | `{t1, t2, h}` (t2 = water level) **ambiguous** |
| `1200099803A1` | MA10800 | `{w}`                                          |
| `1200099803A2` | MA10880 | `{kp1t, kp1c}`                                 |

## Important: MA10300 vs MA10350

These two devices have **identical measurement keys** but different meanings:

- **MA10300**: `t2` = Cable temperature
- **MA10350**: `t2` = Water level

When adding device `107EEEB46F02`, you may be asked to disambiguate:

1. Select "MA10350 - Wireless Thermo-Hygrometer with Water Detector"
2. Verify that `t2` creates a Water sensor (not Temperature)

## Workflow

### For Development

1. **Make code changes** to `custom_components/mobile_alerts/`
2. **Run unit tests** to verify logic:
   ```bash
   python -m pytest tests -q
   ```
3. **Test manually** with mock server:
   ```bash
   bash tests/start-test-server.sh
   # Open http://localhost:8123 and add test devices
   bash tests/stop-test-server.sh
   ```

### For CI/CD

The `pytest` command runs automatically and must pass:

```bash
python -m pytest --timeout=10 tests -q
```

## Troubleshooting

### Tests Failing

1. Check Python version: `python --version` (should be 3.13+)
2. Install test dependencies:
   ```bash
   pip install -r requirements.test.txt
   ```
3. Run with verbose output:
   ```bash
   python -m pytest tests -vv
   ```

### Mock Server Issues

See [MANUAL_TESTING.md](MANUAL_TESTING.md#troubleshooting) for detailed troubleshooting.

## References

- [MANUAL_TESTING.md](MANUAL_TESTING.md) - Complete manual testing guide
- [Home Assistant Testing Docs](https://developers.home-assistant.io/docs/testing/)
- [pytest Documentation](https://docs.pytest.org/)
