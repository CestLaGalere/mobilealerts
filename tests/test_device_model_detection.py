"""Tests for device model detection with real-world measurement data."""

from custom_components.mobile_alerts.device import detect_device_model, DEVICE_MODELS


class TestDeviceModelDetection:
    """Test device model detection from measurement data."""

    def test_ma10100_thermometer(self):
        """Test detection of MA10100 - Wireless Thermometer."""
        measurement = {
            "t1": 22.5,
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = detect_device_model(measurement)
        assert result is not None
        model_id, model_info = result
        assert model_id == "MA10100"
        assert model_info["measurement_keys"] == {"t1"}

    def test_ma10101_thermometer_with_cable(self):
        """Test detection of MA10101 - Thermometer with cable sensor."""
        measurement = {
            "t1": 22.5,
            "t2": 18.3,
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = detect_device_model(measurement)
        assert result is not None
        model_id, model_info = result
        # Could match MA10101 or MA10700 - both have t1, t2
        # Should prefer exact match if available
        assert model_id in ["MA10101", "MA10700"]

    def test_ma10200_thermo_hygro(self):
        """Test detection of MA10200 - Thermo-Hygrometer."""
        measurement = {
            "t1": 22.5,
            "h1": 65.0,
            "ts": 1704067200,
            "idx": "09265A8A3503",
            "c": 0,
            "lb": False,
        }
        result = detect_device_model(measurement)
        assert result is not None
        model_id, model_info = result
        # Could match MA10200, MA10230, MA10241 - all have t1, h1
        assert model_id in ["MA10200", "MA10230", "MA10241"]

    def test_ma10238_air_pressure_monitor(self):
        """Test detection of MA10238 - Air pressure monitor."""
        measurement = {
            "t1": 22.5,
            "h1": 65.0,
            "ap": 1013.25,
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = detect_device_model(measurement)
        assert result is not None
        model_id, model_info = result
        assert model_id == "MA10238"
        assert model_info["measurement_keys"] == {"t1", "h1", "ap"}

    def test_ma10300_thermo_hygro_with_cable(self):
        """Test detection of MA10300/MA10320 - Thermo-Hygrometer with cable."""
        measurement = {
            "t1": 22.5,
            "t2": 18.3,
            "h1": 65.0,
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = detect_device_model(measurement)
        assert result is not None
        model_id, model_info = result
        assert model_id == "MA10300"
        assert model_info["measurement_keys"] == {"t1", "t2", "h1"}

    def test_ma10350_thermo_hygro_water(self):
        """Test detection of MA10350 - Thermo-Hygrometer with water detector."""
        measurement = {
            "t1": 22.5,
            "h1": 65.0,
            "t2": 1,  # Water detection flag
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = detect_device_model(measurement)
        assert result is not None
        model_id, model_info = result
        # Could match MA10300, MA10350, or MA10700 - all have t1, h1, t2
        assert model_id in ["MA10300", "MA10350", "MA10700"]
        assert model_info["measurement_keys"] == {"t1", "t2", "h1"}

    def test_ma10650_rain_gauge(self):
        """Test detection of MA10650 - Rain gauge."""
        measurement = {
            "r": 12.5,
            "rf": 0.5,
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = detect_device_model(measurement)
        assert result is not None
        model_id, model_info = result
        assert model_id == "MA10650"
        assert model_info["measurement_keys"] == {"r", "rf"}

    def test_ma10660_anemometer(self):
        """Test detection of MA10660 - Anemometer."""
        measurement = {
            "ws": 5.2,
            "wg": 8.5,
            "wd": 180,
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = detect_device_model(measurement)
        assert result is not None
        model_id, model_info = result
        assert model_id == "MA10660"
        assert model_info["measurement_keys"] == {"ws", "wg", "wd"}

    def test_ma10800_contact_sensor(self):
        """Test detection of MA10800 - Contact sensor."""
        measurement = {
            "w": 0,
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = detect_device_model(measurement)
        assert result is not None
        model_id, model_info = result
        assert model_id == "MA10800"
        assert model_info["measurement_keys"] == {"w"}

    def test_ma10880_switch(self):
        """Test detection of MA10880 - Wireless switch."""
        measurement = {
            "kp1t": 1,
            "kp1c": 5,
            "kp2t": 0,
            "kp2c": 3,
            "kp3t": 0,
            "kp3c": 2,
            "kp4t": 0,
            "kp4c": 1,
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = detect_device_model(measurement)
        assert result is not None
        model_id, model_info = result
        assert model_id == "MA10880"
        assert model_info["measurement_keys"] == {
            "kp1t",
            "kp1c",
            "kp2t",
            "kp2c",
            "kp3t",
            "kp3c",
            "kp4t",
            "kp4c",
        }

    def test_empty_measurement(self):
        """Test that empty measurement returns None."""
        result = detect_device_model({})
        assert result is None

    def test_none_measurement(self):
        """Test that None measurement returns None."""
        result = detect_device_model(None)
        assert result is None

    def test_metadata_only_measurement(self):
        """Test that measurement with only metadata returns None."""
        measurement = {
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = detect_device_model(measurement)
        assert result is None

    def test_unknown_measurement_keys(self):
        """Test that measurement keys not in any device return None."""
        measurement = {
            "xyz": 123,  # Unknown measurement key
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = detect_device_model(measurement)
        assert result is None

    def test_device_models_structure(self):
        """Test that all device models have required keys."""
        required_keys = {"name", "display_name", "measurement_keys", "description"}

        for model_id, model_info in DEVICE_MODELS.items():
            assert isinstance(model_id, str), (
                f"Model ID should be string for {model_id}"
            )
            assert isinstance(model_info, dict), (
                f"Model info should be dict for {model_id}"
            )

            info_keys = set(model_info.keys())
            assert required_keys.issubset(info_keys), (
                f"Model {model_id} missing keys: {required_keys - info_keys}"
            )

            assert isinstance(model_info["name"], str)
            assert isinstance(model_info["display_name"], str)
            assert isinstance(model_info["measurement_keys"], set)
            assert isinstance(model_info["description"], str)
