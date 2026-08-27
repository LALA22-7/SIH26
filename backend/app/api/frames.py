"""GET /api/ps70/frames/{frame_id} — satellite frame metadata and optional image serving."""
import os
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.satellite_frame import SatelliteFrame
from app.schemas.frames import FrameMetadata, FrameResolution

router = APIRouter(prefix="/api/ps70", tags=["frames"])


@router.get("/frames/{frame_id}", response_model=FrameMetadata)
async def get_frame(
    frame_id: str,
    format: str = Query(default="json", description="Response format: 'json' or 'image'"),
    db: AsyncSession = Depends(get_db),
):
    """
    Return satellite frame metadata (default) or stream the raw image file.

    - **frame_id**: The unique frame identifier stored in satellite_frames table.
    - **format**: `json` returns FrameMetadata. `image` streams the file from disk.
    """
    result = await db.execute(
        select(SatelliteFrame).where(SatelliteFrame.frame_id == frame_id)
    )
    frame: SatelliteFrame | None = result.scalar_one_or_none()

    if frame is None:
        raise HTTPException(status_code=404, detail=f"Frame '{frame_id}' not found")

    if format == "image":
        # Stream the actual file from disk
        if not frame.local_path:
            raise HTTPException(
                status_code=404,
                detail=f"Frame '{frame_id}' has no local file path recorded",
            )
        if not os.path.isfile(frame.local_path):
            raise HTTPException(
                status_code=404,
                detail=f"File not found on disk: {frame.local_path}",
            )
        # Infer media type from extension
        ext = os.path.splitext(frame.local_path)[1].lower()
        media_type_map = {
            ".tif": "image/tiff",
            ".tiff": "image/tiff",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }
        media_type = media_type_map.get(ext, "application/octet-stream")
        return FileResponse(frame.local_path, media_type=media_type)

    # Default: return JSON metadata
    channels = list((frame.channels or {}).keys()) if frame.channels else []
    bbox = frame.bbox or []
    resolution = None
    if frame.resolution:
        resolution = FrameResolution(
            width=frame.resolution.get("width", 0),
            height=frame.resolution.get("height", 0),
        )

    return FrameMetadata(
        frame_id=frame.frame_id,
        event_id=frame.event_id,
        timestamp=frame.timestamp,
        channels=channels,
        crs=frame.crs or "EPSG:4326",
        bbox=bbox,
        resolution=resolution,
        source=frame.source,
        local_path=frame.local_path,
    )
