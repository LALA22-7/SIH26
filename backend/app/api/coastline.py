import json
import os
from typing import List, Tuple
from fastapi import APIRouter, HTTPException, Query
from app.services.geo import haversine_km

router = APIRouter(prefix="/api/coastline", tags=["Coastline"])

# Load geojson once
DATA_ROOT = os.getenv("DATA_ROOT", "/app/data")
COASTLINE_PATH = os.path.join(DATA_ROOT, "india_coastline.geojson")
if not os.path.exists(COASTLINE_PATH):
    # Fallback to local relative path if not in docker
    COASTLINE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/india_coastline.geojson"))

coastal_points: List[Tuple[float, float]] = []

def load_coastline():
    global coastal_points
    if coastal_points:
        return
    try:
        with open(COASTLINE_PATH, "r") as f:
            data = json.load(f)
            # GeoJSON coordinates are [lon, lat]
            # haversine_km expects (lat, lon)
            for feature in data.get("features", []):
                geom = feature.get("geometry", {})
                if geom.get("type") == "LineString":
                    for coord in geom.get("coordinates", []):
                        if len(coord) >= 2:
                            lon, lat = coord[0], coord[1]
                            coastal_points.append((lat, lon))
    except Exception as e:
        print(f"Error loading coastline geojson: {e}")

@router.on_event("startup")
async def startup_event():
    load_coastline()

@router.get("/distance")
async def get_distance_to_coast(
    lat: float = Query(..., description="Latitude of the storm center"),
    lon: float = Query(..., description="Longitude of the storm center")
):
    """Calculate the minimum Haversine distance to the Indian coastline."""
    if not coastal_points:
        load_coastline()
        if not coastal_points:
             raise HTTPException(status_code=500, detail="Coastline data unavailable")
    
    min_dist = min(haversine_km(lat, lon, c_lat, c_lon) for c_lat, c_lon in coastal_points)
    
    return {"distance_km": round(min_dist, 2)}
