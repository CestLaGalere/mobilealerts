"""Tests for device model detection with real-world measurement data."""

from custom_components.mobile_alerts.device import (
    find_all_matching_models,
    DEVICE_MODELS,
)


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
        result = find_all_matching_models(measurement)
        assert len(result) > 0, "Should find at least one matching model"
        # Could match MA10100, MA10120 (both have only t1)
        model_ids = [model_id for model_id, _ in result]
        assert "MA10100" in model_ids or "MA10120" in model_ids
        model_id, model_info = result[0]
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
        result = find_all_matching_models(measurement)
        assert len(result) > 0
        model_id, model_info = result[0]
        # Could match MA10101 - exact match
        assert model_id == "MA10101"

    def test_ma10200_thermo_hygro(self):
        """Test detection of MA10200 - Thermo-Hygrometer."""
        measurement = {
            "t1": 22.5,
            "h": 65.0,
            "ts": 1704067200,
            "idx": "09265A8A3503",
            "c": 0,
            "lb": False,
        }
        result = find_all_matching_models(measurement)
        assert len(result) > 0
        # Could match MA10200, MA10241 (both have t1, h)
        model_ids = [model_id for model_id, _ in result]
        assert any(m in model_ids for m in ["MA10200", "MA10241"])

    def test_ma10238_air_pressure_monitor(self):
        """Test detection of MA10238 - Air pressure monitor."""
        measurement = {
            "t1": 22.5,
            "h": 65.0,
            "ap": 1013.25,
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = find_all_matching_models(measurement)
        assert len(result) > 0
        model_id, model_info = result[0]
        assert model_id == "MA10238"
        assert model_info["measurement_keys"] == {"t1", "h", "ap"}

    def test_ma10230_room_climate_station_with_h_key(self):
        """Test detection of MA10230 - Room Climate Station with 'h' key.

        Real-world case where device sends t1 and h (not h1).
        Device has many additional keys (h3havg, h24havg, h7davg, h30davg)
        which are averages and should be ignored.

        Should match MA10230 (t1, h, averages), NOT MA10100 (t1 only).
        This tests the scoring system that prefers models with more matches.
        """
        measurement = {
            "idx": 239621,
            "ts": 1742682553,
            "c": 1742682558,
            "lb": True,
            "t1": 19.7,
            "h": 36.0,
            "h3havg": 36.0,
            "h24havg": 37.0,
            "h7davg": 35.0,
            "h30davg": 40.0,
        }
        result = find_all_matching_models(measurement)
        assert len(result) > 0
        model_id, model_info = result[0]
        # Should match MA10230 (t1, h, averages), not MA10100 (t1 only)
        assert model_id == "MA10230", f"Expected MA10230 but got {model_id}"
        assert model_info["measurement_keys"] == {
            "t1",
            "h",
            "h3havg",
            "h24havg",
            "h7davg",
            "h30davg",
        }

    def test_ma10300_thermo_hygro_with_cable(self):
        """Test detection of MA10300/MA10320 - Thermo-Hygrometer with cable.

        Note: MA10300 and MA10350 both have identical measurement keys {t1, t2, h}.
        The difference is that MA10300's t2 is cable temperature while MA10350's t2 is water level.
        When both match, the function returns both in a list.
        """
        measurement = {
            "t1": 22.5,
            "t2": 18.3,
            "h": 65.0,
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = find_all_matching_models(measurement)
        assert len(result) >= 2, "Should find both MA10300 and MA10350"
        # Ambiguous - both MA10300 and MA10350 match
        model_ids = [model_id for model_id, _ in result]
        assert "MA10300" in model_ids
        assert "MA10350" in model_ids

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
        result = find_all_matching_models(measurement)
        assert len(result) > 0
        model_id, model_info = result[0]
        # Could match MA10700 which has t1, h1, t2
        assert model_id == "MA10700"
        assert model_info["measurement_keys"] == {"t1", "t2", "h1"}

    def test_ma10650_rain_gauge(self):
        """Test detection of MA10650 - Rain gauge."""
        measurement = {
            "t1": 22.5,
            "r": 12.5,
            "rf": 0.5,
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = find_all_matching_models(measurement)
        assert len(result) > 0
        model_id, model_info = result[0]
        assert model_id == "MA10650"
        assert model_info["measurement_keys"] == {"t1", "r", "rf"}

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
        result = find_all_matching_models(measurement)
        assert len(result) > 0
        model_id, model_info = result[0]
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
        result = find_all_matching_models(measurement)
        assert len(result) > 0
        model_id, model_info = result[0]
        assert model_id == "MA10800"
        assert model_info["measurement_keys"] == {"w"}

    def test_ma10402_co2_monitor(self):
        """Test detection of MA10402 - CO2 Monitor."""
        measurement = {
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "t1": 22.0,
            "t2": 5.5,
            "h": 51.0,
            "ppm": 450,
            "lb": False,
        }
        result = find_all_matching_models(measurement)
        assert len(result) > 0
        model_id, model_info = result[0]
        assert model_id == "MA10402"
        assert model_info["measurement_keys"] == {"t1", "t2", "h", "ppm"}

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
        result = find_all_matching_models(measurement)
        assert len(result) > 0
        model_id, model_info = result[0]
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

    def test_tfa_30_3060_01_klima_home(self):
        """Test detection of TFA KLIMA@HOME 30.3060.01 - Thermo-Hygrometer with 3 sensors."""
        measurement = {
            "ts": 1704067200,
            "idx": "123ABC456",
            "c": 0,
            "lb": False,
            "t1": 21.5,
            "t2": 18.3,
            "t3": 22.1,
            "t4": 19.8,
            "h1": 55.0,
            "h2": 48.5,
            "h3": 52.3,
            "h4": 60.1,
        }
        result = find_all_matching_models(measurement)
        assert len(result) > 0
        model_id, model_info = result[0]
        assert model_id == "TFA_30.3060.01:IT"
        assert model_info["measurement_keys"] == {
            "t1",
            "t2",
            "t3",
            "t4",
            "h1",
            "h2",
            "h3",
            "h4",
        }
        assert model_info["display_name"] == "Wireless Thermo-Hygrometer with 3 sensors"

    def test_empty_measurement(self):
        """Test that empty measurement returns empty list."""
        result = find_all_matching_models({})
        assert result == []

    def test_none_measurement(self):
        """Test that None measurement returns empty list."""
        result = find_all_matching_models(None)
        assert result == []

    def test_metadata_only_measurement(self):
        """Test that measurement with only metadata returns empty list."""
        measurement = {
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = find_all_matching_models(measurement)
        assert result == []

    def test_unknown_measurement_keys(self):
        """Test that measurement keys not in any device return empty list."""
        measurement = {
            "xyz": 123,  # Unknown measurement key
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = find_all_matching_models(measurement)
        assert result == []

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
