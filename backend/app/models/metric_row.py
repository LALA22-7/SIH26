"""ORM model for per-forecast metric rows used to compute MAE and coverage."""
import uuid
from datetime import datetime

from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MetricRow(Base):
    __tablename__ = "metrics"

    metric_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False, index=True
    )
    base_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    # Forecast horizon in hours (12 or 24)
    horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    pred_lat: Mapped[float] = mapped_column(Float, nullable=False)
    pred_lon: Mapped[float] = mapped_column(Float, nullable=False)
    actual_lat: Mapped[float] = mapped_column(Float, nullable=False)
    actual_lon: Mapped[float] = mapped_column(Float, nullable=False)
    # Pre-computed Haversine distance in km
    error_km: Mapped[float] = mapped_column(Float, nullable=False)
    # Ground-truth pattern label for classification accuracy computation
    ground_truth_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Predicted pattern label (stored for accuracy cross-reference)
    predicted_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="metrics")  # noqa: F821
