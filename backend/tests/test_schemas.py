"""Unit tests for Pydantic schemas — validation rules, coordinate bounds, UTC enforcement."""
import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from app.schemas.common import CenterPoint, PatternResult, UncertaintyBlock
from app.schemas.classify import ClassifyRequest, ClassifyResponse
from app.schemas.predict import PredictRequest, PredictResponse, PredictionStep
from app.schemas.metrics import MetricsResponse
from app.schemas.frames import FrameMetadata


# ── CenterPoint ───────────────────────────────────────────────────────────────

class TestCenterPoint:
    def test_valid(self):
        c = CenterPoint(lat=15.2, lon=68.4)
        assert c.lat == 15.2
        assert c.lon == 68.4

    def test_lat_too_high(self):
        with pytest.raises(ValidationError, match="lat must be between"):
            CenterPoint(lat=91.0, lon=68.4)

    def test_lat_too_low(self):
        with pytest.raises(ValidationError, match="lat must be between"):
            CenterPoint(lat=-91.0, lon=68.4)

    def test_lon_too_high(self):
        with pytest.raises(ValidationError, match="lon must be between"):
            CenterPoint(lat=15.2, lon=181.0)

    def test_lon_too_low(self):
        with pytest.raises(ValidationError, match="lon must be between"):
            CenterPoint(lat=15.2, lon=-181.0)

    def test_boundary_values(self):
        c = CenterPoint(lat=90.0, lon=180.0)
        assert c.lat == 90.0
        c2 = CenterPoint(lat=-90.0, lon=-180.0)
        assert c2.lat == -90.0


# ── PatternResult ─────────────────────────────────────────────────────────────

class TestPatternResult:
    def test_valid(self):
        p = PatternResult(label="banding", confidence=0.72)
        assert p.label == "banding"

    def test_confidence_above_one(self):
        with pytest.raises(ValidationError, match="confidence must be between"):
            PatternResult(label="eye", confidence=1.1)

    def test_confidence_below_zero(self):
        with pytest.raises(ValidationError, match="confidence must be between"):
            PatternResult(label="eye", confidence=-0.1)

    def test_confidence_boundary(self):
        p = PatternResult(label="eye", confidence=0.0)
        assert p.confidence == 0.0
        p2 = PatternResult(label="eye", confidence=1.0)
        assert p2.confidence == 1.0


# ── UncertaintyBlock ──────────────────────────────────────────────────────────

class TestUncertaintyBlock:
    def test_defaults_provisional(self):
        u = UncertaintyBlock()
        assert u.status == "provisional"
        assert u.coverage_target is None

    def test_calibrated(self):
        u = UncertaintyBlock(status="calibrated", coverage_target=0.90)
        assert u.coverage_target == 0.90


# ── ClassifyRequest ───────────────────────────────────────────────────────────

class TestClassifyRequest:
    def test_valid(self):
        r = ClassifyRequest(
            event_id="biparjoy_2023",
            timestamp=datetime(2023, 6, 14, 12, 0, tzinfo=timezone.utc),
            frame_id="frame_001",
        )
        assert r.event_id == "biparjoy_2023"

    def test_missing_timezone_raises(self):
        with pytest.raises(ValidationError, match="timezone"):
            ClassifyRequest(
                event_id="biparjoy_2023",
                timestamp=datetime(2023, 6, 14, 12, 0),  # no tz
                frame_id="frame_001",
            )

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            ClassifyRequest(event_id="biparjoy_2023")  # type: ignore


# ── PredictRequest ────────────────────────────────────────────────────────────

class TestPredictRequest:
    def test_valid(self):
        r = PredictRequest(
            event_id="biparjoy_2023",
            start_timestamp=datetime(2023, 6, 14, 0, 0, tzinfo=timezone.utc),
        )
        assert r.event_id == "biparjoy_2023"

    def test_naive_datetime_raises(self):
        with pytest.raises(ValidationError, match="timezone"):
            PredictRequest(
                event_id="biparjoy_2023",
                start_timestamp=datetime(2023, 6, 14, 0, 0),
            )


# ── MetricsResponse ───────────────────────────────────────────────────────────

class TestMetricsResponse:
    def test_empty_defaults(self):
        m = MetricsResponse()
        assert m.dataset.events == 0
        assert m.track.mae_km_t12 is None
        assert m.note is None

    def test_with_data(self):
        m = MetricsResponse(
            event_id="biparjoy_2023",
            dataset={"events": 1, "forecasts": 10},
            track={"mae_km_t12": 54.2, "mae_km_t24": 91.8},
        )
        assert m.track.mae_km_t12 == 54.2


# ── FrameMetadata ─────────────────────────────────────────────────────────────

class TestFrameMetadata:
    def test_valid(self):
        f = FrameMetadata(
            frame_id="frame_001",
            event_id="biparjoy_2023",
            timestamp=datetime(2023, 6, 14, 12, 0, tzinfo=timezone.utc),
            channels=["ir", "water_vapor"],
            crs="EPSG:4326",
            bbox=[60.0, 5.0, 80.0, 25.0],
        )
        assert f.channels == ["ir", "water_vapor"]
        assert len(f.bbox) == 4
