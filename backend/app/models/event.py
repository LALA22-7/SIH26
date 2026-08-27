"""ORM model for cyclone events."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Event(Base):
    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    basin: Mapped[str] = mapped_column(String(16), nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    frames: Mapped[list["SatelliteFrame"]] = relationship(  # noqa: F821
        back_populates="event", cascade="all, delete-orphan"
    )
    classifications: Mapped[list["Classification"]] = relationship(  # noqa: F821
        back_populates="event", cascade="all, delete-orphan"
    )
    predictions: Mapped[list["Prediction"]] = relationship(  # noqa: F821
        back_populates="event", cascade="all, delete-orphan"
    )
    metrics: Mapped[list["MetricRow"]] = relationship(  # noqa: F821
        back_populates="event", cascade="all, delete-orphan"
    )
