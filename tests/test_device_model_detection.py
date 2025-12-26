"""Tests for device model detection with real-world measurement data."""

from custom_components.mobile_alerts.device import (
    find_all_matching_models,
    DEVICE_MODELS,
)


def find_model_by_id(
    result: list[tuple[str, dict]], expected_model_id: str
) -> tuple[str, dict]:
    """Helper to find a specific model in results.

    Args:
        result: List of (model_id, model_info) tuples from find_all_matching_models
        expected_model_id: The model ID to search for

    Returns:
        The (model_id, model_info) tuple for the expected model

    Raises:
        AssertionError: If expected model is not found
    """
    model = next((m for m in result if m[0] == expected_model_id), None)
    assert model is not None, (
        f"Expected model {expected_model_id} not found. "
        f"Found models: {[m[0] for m in result]}"
    )
    return model


class TestDeviceModelDetection:
    """Test device model detection from measurement data."""

    def test_ma10100_thermometer(self):
        """Test detection of MA10100 - Wireless Thermometer."""
        expected_model_id = "MA10100"
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
        assert expected_model_id in model_ids or "MA10120" in model_ids
        model_id, model_info = find_model_by_id(result, expected_model_id)
        assert model_info["measurement_keys"] == {"t1"}

    def test_ma10101_thermometer_with_cable(self):
        """Test detection of MA10101 - Thermometer with cable sensor."""
        expected_model_id = "MA10101"
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
        model_id, model_info = find_model_by_id(result, expected_model_id)
        assert model_info["measurement_keys"] == {"t1", "t2"}

    def test_ma10200_thermo_hygro(self):
        """Test detection of MA10200 - Thermo-Hygrometer."""
        expected_model_id = "MA10200"
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
        model_id, model_info = find_model_by_id(result, expected_model_id)
        assert model_info["measurement_keys"] == {"t1", "h"}

    def test_ma10238_air_pressure_monitor(self):
        """Test detection of MA10238 - Air pressure monitor."""
        expected_model_id = "MA10238"
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
        model_id, model_info = find_model_by_id(result, expected_model_id)
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

    def test_ma10230_room_climate_station_with_h_key(self):
        """Test detection of MA10230 - Room Climate Station with 'h' key.

        Real-world case where device sends t1 and h (not h1).
        Device has many additional keys (h3havg, h24havg, h7davg, h30davg)
        which are averages and should be ignored.

        Should match MA10230 (t1, h, averages), NOT MA10100 (t1 only).
        """
        expected_model_id = "MA10230"
        measurement = {
            "t1": 22.5,
            "h": 65.0,
            "h3havg": 64.5,
            "h24havg": 63.8,
            "h7davg": 64.2,
            "h30davg": 64.0,
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = find_all_matching_models(measurement)
        assert len(result) > 0
        model_id, model_info = find_model_by_id(result, expected_model_id)
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
        expected_model_id = "MA10350"
        measurement = {
            "t1": 22.5,
            "h": 65.0,
            "t2": 1,  # Water detection flag
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = find_all_matching_models(measurement)
        assert len(result) > 0
        model_id, model_info = find_model_by_id(result, expected_model_id)
        assert model_info["measurement_keys"] == {"t1", "t2", "h"}

    def test_ma10650_rain_gauge(self):
        """Test detection of MA10650 - Rain gauge."""
        expected_model_id = "MA10650"
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
        model_id, model_info = find_model_by_id(result, expected_model_id)
        assert model_info["measurement_keys"] == {"t1", "r", "rf"}

    def test_ma10660_anemometer(self):
        """Test detection of MA10660 - Anemometer."""
        expected_model_id = "MA10660"
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
        model_id, model_info = find_model_by_id(result, expected_model_id)
        assert model_info["measurement_keys"] == {"ws", "wg", "wd"}

    def test_ma10800_contact_sensor(self):
        """Test detection of MA10800 - Contact sensor."""
        expected_model_id = "MA10800"
        measurement = {
            "w": 0,
            "ts": 1704067200,
            "idx": "0E7EA4A71203",
            "c": 0,
            "lb": False,
        }
        result = find_all_matching_models(measurement)
        assert len(result) > 0
        model_id, model_info = find_model_by_id(result, expected_model_id)
        assert model_info["measurement_keys"] == {"w"}

    def test_ma10402_co2_monitor(self):
        """Test detection of MA10402 - CO2 Monitor."""
        expected_model_id = "MA10402"
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
        model_id, model_info = find_model_by_id(result, expected_model_id)
        assert model_info["measurement_keys"] == {"t1", "t2", "h", "ppm"}

    def test_ma10880_switch(self):
        """Test detection of MA10880 - Wireless switch."""
        expected_model_id = "MA10880"
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
        model_id, model_info = find_model_by_id(result, expected_model_id)
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
        expected_model_id = "TFA_30.3060.01:IT"
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
        model_id, model_info = find_model_by_id(result, expected_model_id)
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
        assert (
            model_info["display_name"]
            == "TFA Dostmann KLIMA@HOME Thermo-Hygrometer with 3 sensors"
        )

    def test_tfa_30_3303_02(self):
        """Test detection of TFA 30.3303.02 - Thermo-Hygrometer Transmitter for WEATHERHUB."""
        expected_model_id = "TFA_30.3303.02"
        measurement = {
            "ts": 1704067200,
            "idx": "123ABC556",
            "c": 0,
            "lb": False,
            "t1": 21.5,
            "h": 55.0,
        }
        result = find_all_matching_models(measurement)
        assert len(result) > 0
        # Multiple models may have the same keys (t1, h): MA10200 and TFA_30.3303.02
        # We specifically look for the TFA model
        model_id, model_info = find_model_by_id(result, expected_model_id)
        assert model_info["measurement_keys"] == {
            "t1",
            "h",
        }
        assert (
            model_info["display_name"]
            == "TFA Dostmann Thermo-Hygrometer Transmitter for WEATHERHUB"
        )

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
        required_keys = {
            "name",
            "display_name",
            "measurement_keys",
            "description",
            "manufacturer",
        }

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
            assert isinstance(model_info["manufacturer"], str)
