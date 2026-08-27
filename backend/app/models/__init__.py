"""Import all ORM models so Alembic autogenerate can detect them."""
from app.models.base import Base
from app.models.event import Event
from app.models.satellite_frame import SatelliteFrame
from app.models.classification import Classification
from app.models.prediction import Prediction
from app.models.metric_row import MetricRow

__all__ = [
    "Base",
    "Event",
    "SatelliteFrame",
    "Classification",
    "Prediction",
    "MetricRow",
]
