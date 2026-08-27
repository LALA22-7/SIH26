"""Initial schema: enable PostGIS, create all tables.

Revision ID: 0001
Revises:
Create Date: 2026-08-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
import geoalchemy2
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enable PostGIS ────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # ── events ────────────────────────────────────────────────
    op.create_table(
        "events",
        sa.Column("event_id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("basin", sa.String(16), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    # ── satellite_frames ──────────────────────────────────────
    op.create_table(
        "satellite_frames",
        sa.Column("frame_id", sa.String(128), primary_key=True),
        sa.Column(
            "event_id",
            sa.String(64),
            sa.ForeignKey("events.event_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("channels", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("file_paths", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("crs", sa.String(32), nullable=True, server_default="EPSG:4326"),
        sa.Column("bbox", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("resolution", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("source", sa.String(128), nullable=True),
        sa.Column("local_path", sa.Text(), nullable=True),
    )
    op.create_index("ix_satellite_frames_event_id", "satellite_frames", ["event_id"])
    op.create_index("ix_satellite_frames_timestamp", "satellite_frames", ["timestamp"])

    # ── classifications ───────────────────────────────────────
    op.create_table(
        "classifications",
        sa.Column(
            "classification_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "event_id",
            sa.String(64),
            sa.ForeignKey("events.event_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "frame_id",
            sa.String(128),
            sa.ForeignKey("satellite_frames.frame_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("pattern", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("model_version", sa.String(32), nullable=False),
        sa.Column(
            "geometry",
            geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_classifications_event_id", "classifications", ["event_id"])
    op.create_index("ix_classifications_timestamp", "classifications", ["timestamp"])
    op.create_index(
        "ix_classifications_event_timestamp",
        "classifications",
        ["event_id", "timestamp"],
    )

    # ── predictions ───────────────────────────────────────────
    op.create_table(
        "predictions",
        sa.Column(
            "prediction_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "event_id",
            sa.String(64),
            sa.ForeignKey("events.event_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("base_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pred_lat", sa.Float(), nullable=False),
        sa.Column("pred_lon", sa.Float(), nullable=False),
        sa.Column("pattern_label", sa.String(64), nullable=False),
        sa.Column("pattern_confidence", sa.Float(), nullable=False),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("model_version", sa.String(32), nullable=False),
        sa.Column(
            "uncertainty_status",
            sa.String(32),
            nullable=False,
            server_default="provisional",
        ),
        sa.Column(
            "uncertainty_geom",
            geoalchemy2.types.Geometry(geometry_type="POLYGON", srid=4326),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_predictions_event_id", "predictions", ["event_id"])
    op.create_index("ix_predictions_base_time", "predictions", ["base_time"])
    op.create_index(
        "ix_predictions_event_base_time",
        "predictions",
        ["event_id", "base_time"],
    )

    # ── metrics ───────────────────────────────────────────────
    op.create_table(
        "metrics",
        sa.Column(
            "metric_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "event_id",
            sa.String(64),
            sa.ForeignKey("events.event_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("base_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("horizon_hours", sa.Integer(), nullable=False),
        sa.Column("pred_lat", sa.Float(), nullable=False),
        sa.Column("pred_lon", sa.Float(), nullable=False),
        sa.Column("actual_lat", sa.Float(), nullable=False),
        sa.Column("actual_lon", sa.Float(), nullable=False),
        sa.Column("error_km", sa.Float(), nullable=False),
        sa.Column("ground_truth_label", sa.String(64), nullable=True),
        sa.Column("predicted_label", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_metrics_event_id", "metrics", ["event_id"])
    op.create_index("ix_metrics_base_time", "metrics", ["base_time"])


def downgrade() -> None:
    op.drop_table("metrics")
    op.drop_table("predictions")
    op.drop_table("classifications")
    op.drop_table("satellite_frames")
    op.drop_table("events")
    op.execute("DROP EXTENSION IF EXISTS postgis;")
