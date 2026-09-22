from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class GroundReportCreate(BaseModel):
    event_id: str = Field(..., max_length=64)
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    damage_type: str = Field(..., max_length=64, description="NDRF damage category (e.g. G1, G2)")
    severity: float = Field(..., ge=0.0, le=4.0, description="Severity 0.0 to 4.0")
    reporter_id: str = Field(..., max_length=128)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
class GroundReportResponse(GroundReportCreate):
    report_id: UUID
    verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
