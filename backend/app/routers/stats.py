import json
from collections import Counter
from typing import Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import Incident
from app.models.schemas import StatsResponse
from app.services import open_data_service

router = APIRouter()


@router.get("/stats", response_model=StatsResponse)
def stats(dias: Optional[int] = Query(None, ge=1), db: Session = Depends(get_db)):
    q = db.query(Incident)
    if dias:
        desde = (datetime.now(timezone.utc) - timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%SZ")
        q = q.filter(Incident.timestamp >= desde)
    por_mod, por_upz = Counter(), Counter()
    for r in q.all():
        p = json.loads(r.payload_json)
        por_mod[p.get("modalidad_detectada") or p.get("modalidad") or "Reporte ciudadano"] += 1
        por_upz[r.upz] += 1
    return {"por_modalidad": dict(por_mod), "por_upz": dict(por_upz),
            "historico_bosa": open_data_service.historico_upz()}
