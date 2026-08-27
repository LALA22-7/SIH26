"""Tests for services/ml_adapter.py — stub mode behaviour and schema compliance."""
import pytest
import numpy as np
import os


# Force stub mode for all tests in this module
os.environ["ML_FORCE_STUB"] = "true"


@pytest.fixture(autouse=True)
def reset_adapter():
    """Reset ML adapter mode detection before each test."""
    from app.services import ml_adapter
    ml_adapter.reset_mode()
    yield
    ml_adapter.reset_mode()


class TestClassifyStub:
    def test_returns_dict(self):
        from app.services.ml_adapter import run_classify
        result = run_classify()
        assert isinstance(result, dict)

    def test_has_center(self):
        from app.services.ml_adapter import run_classify
        result = run_classify()
        assert "center" in result
        assert "lat" in result["center"]
        assert "lon" in result["center"]

    def test_center_in_valid_range(self):
        from app.services.ml_adapter import run_classify
        result = run_classify()
        assert -90 <= result["center"]["lat"] <= 90
        assert -180 <= result["center"]["lon"] <= 180

    def test_has_pattern(self):
        from app.services.ml_adapter import run_classify
        result = run_classify()
        assert "pattern" in result
        assert "label" in result["pattern"]
        assert "confidence" in result["pattern"]

    def test_confidence_in_range(self):
        from app.services.ml_adapter import run_classify
        result = run_classify()
        assert 0.0 <= result["pattern"]["confidence"] <= 1.0

    def test_has_model_meta(self):
        from app.services.ml_adapter import run_classify
        result = run_classify()
        assert "model" in result
        assert "name" in result["model"]
        assert "version" in result["model"]

    def test_stub_model_name_labeled(self):
        from app.services.ml_adapter import run_classify
        result = run_classify()
        # Stub responses must be clearly labeled as stub
        assert "stub" in result["model"]["name"].lower()

    def test_accepts_numpy_array(self):
        from app.services.ml_adapter import run_classify
        frame = np.zeros((3, 256, 256), dtype=np.float32)
        result = run_classify(frame)
        assert isinstance(result, dict)


class TestPredictStub:
    def test_returns_dict(self):
        from app.services.ml_adapter import run_predict
        result = run_predict()
        assert isinstance(result, dict)

    def test_has_predictions_list(self):
        from app.services.ml_adapter import run_predict
        result = run_predict()
        assert "predictions" in result
        assert isinstance(result["predictions"], list)
        assert len(result["predictions"]) > 0

    def test_predictions_have_required_keys(self):
        from app.services.ml_adapter import run_predict
        result = run_predict()
        for pred in result["predictions"]:
            assert "horizon_hours" in pred
            assert "center" in pred
            assert "pattern" in pred

    def test_has_two_horizons(self):
        from app.services.ml_adapter import run_predict
        result = run_predict()
        horizons = {p["horizon_hours"] for p in result["predictions"]}
        assert 12 in horizons
        assert 24 in horizons

    def test_stub_model_name_labeled(self):
        from app.services.ml_adapter import run_predict
        result = run_predict()
        assert "stub" in result["model"]["name"].lower()

    def test_accepts_sequence_array(self):
        from app.services.ml_adapter import run_predict
        seq = np.zeros((5, 3, 256, 256), dtype=np.float32)
        result = run_predict(seq)
        assert isinstance(result, dict)


class TestClassifyService:
    def test_returns_correct_schema(self):
        from app.services.classify_service import run_classification
        from datetime import datetime, timezone
        result = run_classification(
            frame_id="frame_001",
            event_id="biparjoy_2023",
            timestamp=datetime(2023, 6, 14, 12, 0, tzinfo=timezone.utc),
            file_paths=None,
            channels=None,
        )
        assert result["event_id"] == "biparjoy_2023"
        assert result["source"]["frame_id"] == "frame_001"
        assert "center" in result
        assert "pattern" in result
        assert "model" in result

    def test_timestamp_preserved(self):
        from app.services.classify_service import run_classification
        from datetime import datetime, timezone
        ts = datetime(2023, 6, 14, 12, 0, tzinfo=timezone.utc)
        result = run_classification("f001", "ev001", ts, None, None)
        assert result["timestamp"] == ts


class TestPredictService:
    def test_returns_two_predictions(self):
        from app.services.predict_service import run_prediction
        from datetime import datetime, timezone
        result = run_prediction(
            event_id="biparjoy_2023",
            base_time=datetime(2023, 6, 14, 0, 0, tzinfo=timezone.utc),
            frames=[],
        )
        assert len(result["predictions"]) == 2

    def test_valid_times_are_offset_correctly(self):
        from app.services.predict_service import run_prediction
        from datetime import datetime, timezone, timedelta
        base = datetime(2023, 6, 14, 0, 0, tzinfo=timezone.utc)
        result = run_prediction("biparjoy_2023", base, [])
        valid_times = {p["valid_time"] for p in result["predictions"]}
        assert base + timedelta(hours=12) in valid_times
        assert base + timedelta(hours=24) in valid_times

    def test_uncertainty_polygon_is_geojson(self):
        from app.services.predict_service import run_prediction
        from datetime import datetime, timezone
        result = run_prediction(
            "biparjoy_2023",
            datetime(2023, 6, 14, 0, 0, tzinfo=timezone.utc),
            [],
        )
        for pred in result["predictions"]:
            poly = pred["uncertainty_polygon"]
            assert poly["type"] == "Polygon"
            assert "coordinates" in poly
            # Outer ring must have at least 4 points (closed polygon)
            assert len(poly["coordinates"][0]) >= 4

    def test_uncertainty_wkt_not_none(self):
        from app.services.predict_service import run_prediction
        from datetime import datetime, timezone
        result = run_prediction(
            "biparjoy_2023",
            datetime(2023, 6, 14, 0, 0, tzinfo=timezone.utc),
            [],
        )
        for pred in result["predictions"]:
            assert pred["uncertainty_wkt"] is not None
            assert pred["uncertainty_wkt"].startswith("POLYGON")

    def test_uncertainty_status_is_provisional(self):
        from app.services.predict_service import run_prediction
        from datetime import datetime, timezone
        result = run_prediction(
            "biparjoy_2023",
            datetime(2023, 6, 14, 0, 0, tzinfo=timezone.utc),
            [],
        )
        for pred in result["predictions"]:
            assert pred["uncertainty_status"] == "provisional"
