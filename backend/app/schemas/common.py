"""Shared Pydantic building blocks used across all endpoint schemas."""
from typing import Annotated, Any
from pydantic import BaseModel, field_validator


class CenterPoint(BaseModel):
    """Cyclone centre position. Validated lat/lon ranges."""

    lat: Annotated[float, "Latitude, -90 to 90"]
    lon: Annotated[float, "Longitude, -180 to 180"]

    @field_validator("lat")
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not -90.0 <= v <= 90.0:
            raise ValueError(f"lat must be between -90 and 90, got {v}")
        return v

    @field_validator("lon")
    @classmethod
    def validate_lon(cls, v: float) -> float:
        if not -180.0 <= v <= 180.0:
            raise ValueError(f"lon must be between -180 and 180, got {v}")
        return v


class PatternResult(BaseModel):
    """Structural pattern classification output."""

    label: str
    confidence: float

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"confidence must be between 0 and 1, got {v}")
        return v


class ModelMeta(BaseModel):
    """Model provenance metadata attached to every prediction."""

    name: str
    version: str


class GeoJSONPolygon(BaseModel):
    """Minimal GeoJSON Polygon. Coordinates follow [lon, lat] order."""

    type: str = "Polygon"
    # [[[lon, lat], [lon, lat], ...]]  — outer ring only for our use-case
    coordinates: list[list[list[float]]] = []


class UncertaintyBlock(BaseModel):
    """Uncertainty geometry block attached to prediction responses.

    status is "provisional" until Day-6 calibration; then "calibrated".
    coverage_target is only included after calibration.
    """

    status: str = "provisional"
    geometry: GeoJSONPolygon = GeoJSONPolygon()
    coverage_target: float | None = None


class SourceRef(BaseModel):
    """Reference to the source frame used for a classification."""

    frame_id: str
