from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models.ground_report import GroundReport
from app.schemas.reports import GroundReportCreate, GroundReportResponse

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.post("", response_model=GroundReportResponse, status_code=201)
async def submit_report(
    report_in: GroundReportCreate,
    db: AsyncSession = Depends(get_db)
):
    """Submit a new ground destruction report from the field."""
    new_report = GroundReport(
        event_id=report_in.event_id,
        lat=report_in.lat,
        lon=report_in.lon,
        damage_type=report_in.damage_type,
        severity=report_in.severity,
        reporter_id=report_in.reporter_id,
        timestamp=report_in.timestamp
        # verified defaults to False
    )
    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)
    return new_report

@router.get("/{event_id}", response_model=List[GroundReportResponse])
async def get_reports_for_event(
    event_id: str,
    verified_only: bool = Query(False, description="Filter only verified reports"),
    db: AsyncSession = Depends(get_db)
):
    """Get ground reports for a specific cyclone event."""
    stmt = select(GroundReport).where(GroundReport.event_id == event_id)
    if verified_only:
        stmt = stmt.where(GroundReport.verified == True)
    
    stmt = stmt.order_by(GroundReport.timestamp.desc())
    result = await db.execute(stmt)
    reports = result.scalars().all()
    return reports
