from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import ReportRequest, ReportResponse
from app.services import ledger, privacy

router = APIRouter()


@router.post("/report", response_model=ReportResponse)
def report(req: ReportRequest, db: Session = Depends(get_db)):
    limpio = privacy.anonymize(req.payload)
    limpio["upz"] = req.upz
    rid, _, _, current = ledger.register_incident(db, limpio, req.upz, prefix="REP")
    return {"status": "registrado", "hash": current, "id": rid}
