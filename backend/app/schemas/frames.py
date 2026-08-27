"""Schemas for GET /api/ps70/frames/{frame_id}."""
from datetime import datetime
from pydantic import BaseModel


class FrameResolution(BaseModel):
    width: int
    height: int


class FrameMetadata(BaseModel):
    frame_id: str
    event_id: str
    timestamp: datetime
    # Available channel names: ["ir", "water_vapor", "visible"]
    channels: list[str] = []
    crs: str = "EPSG:4326"
    # [min_lon, min_lat, max_lon, max_lat]
    bbox: list[float] = []
    resolution: FrameResolution | None = None
    source: str | None = None
    local_path: str | None = None

    model_config = {"from_attributes": True}
