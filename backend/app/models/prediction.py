"""ORM model for temporal predictions with PostGIS uncertainty polygon."""
import uuid
from datetime import datetime

from sqlalchemy import String, Float, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.geo_types import PolygonGeometry
from app.models.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Analysis time (input time used to generate this prediction)
    base_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    # Forecast valid time (base_time + 12h or + 24h)
    valid_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    pred_lat: Mapped[float] = mapped_column(Float, nullable=False)
    pred_lon: Mapped[float] = mapped_column(Float, nullable=False)
    pattern_label: Mapped[str] = mapped_column(String(64), nullable=False)
    pattern_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    # "provisional" until Day-6 calibration; then "calibrated"
    uncertainty_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="provisional"
    )
    # PostGIS Polygon — uncertainty ellipse.
    # In tests (SQLite) this column is plain Text — no spatial operations performed.
    uncertainty_geom = mapped_column(PolygonGeometry, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="predictions")  # noqa: F821
