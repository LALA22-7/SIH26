"""ORM model for satellite frames."""
from datetime import datetime

from sqlalchemy import String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SatelliteFrame(Base):
    __tablename__ = "satellite_frames"

    frame_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    event_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    # JSONB columns stored as JSON — {"ir": "path", "water_vapor": "path", "visible": "path"}
    channels: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # {"ir": "/data/...", "water_vapor": "/data/..."}
    file_paths: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    crs: Mapped[str | None] = mapped_column(String(32), nullable=True, default="EPSG:4326")
    # [min_lon, min_lat, max_lon, max_lat]
    bbox: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # {"width": 512, "height": 512}
    resolution: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    local_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="frames")  # noqa: F821
    classifications: Mapped[list["Classification"]] = relationship(  # noqa: F821
        back_populates="frame"
    )
