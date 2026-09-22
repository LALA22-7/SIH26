"""ORM model for cyclone classifications stored with PostGIS geometry."""
import uuid
from datetime import datetime

from sqlalchemy import String, Float, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.geo_types import PointGeometry
from app.models.base import Base


class Classification(Base):
    __tablename__ = "classifications"

    classification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False, index=True
    )
    frame_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("satellite_frames.frame_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    pattern: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    
    # Phase 3 Expansion: Multi-task ML predictions
    damage_class: Mapped[str | None] = mapped_column(String(64), nullable=True)
    severity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    t12_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    t12_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    t24_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    t24_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # PostGIS Point — always inserted as ST_SetSRID(ST_MakePoint(lon, lat), 4326)
    # In tests (SQLite) this column is plain Text — no spatial operations performed.
    geometry = mapped_column(PointGeometry, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="classifications")  # noqa: F821
    frame: Mapped["SatelliteFrame | None"] = relationship(  # noqa: F821
        back_populates="classifications"
    )
