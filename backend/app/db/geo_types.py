"""
Portable geometry column type.

In PostgreSQL (production): delegates to GeoAlchemy2.Geometry for full PostGIS support.
In SQLite (tests): stores geometry as plain TEXT — no spatial operations.

Import PointGeometry / PolygonGeometry from here in all ORM models.
"""
import os
import sqlalchemy as sa
from sqlalchemy import types as sqla_types


class _PortableGeometry(sqla_types.TypeDecorator):
    """
    A TypeDecorator that uses GeoAlchemy2.Geometry on PostgreSQL
    and falls back to TEXT on all other backends (SQLite for tests).
    """
    impl = sqla_types.Text
    cache_ok = True

    def __init__(self, geometry_type: str = "GEOMETRY", srid: int = 4326):
        super().__init__()
        self._geometry_type = geometry_type
        self._srid = srid
        self._postgis_type = None  # resolved lazily

    def _get_postgis_type(self):
        if self._postgis_type is None:
            try:
                from geoalchemy2 import Geometry
                self._postgis_type = Geometry(
                    geometry_type=self._geometry_type, srid=self._srid
                )
            except ImportError:
                self._postgis_type = sqla_types.Text()
        return self._postgis_type

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(self._get_postgis_type())
        return dialect.type_descriptor(sqla_types.Text())

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        return value


# Instances used directly in mapped_column() declarations
PointGeometry = _PortableGeometry(geometry_type="POINT", srid=4326)
PolygonGeometry = _PortableGeometry(geometry_type="POLYGON", srid=4326)
