import json
from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import Incident
from app.models.schemas import CampaignResponse

router = APIRouter()
UMBRAL = 2  # incidentes ALTO de la misma modalidad en 7 días => alerta comunitaria


@router.get("/campaigns/latest", response_model=CampaignResponse)
def latest(db: Session = Depends(get_db)):
    desde = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    c = Counter()
    for r in db.query(Incident).filter(Incident.timestamp >= desde).all():
        p = json.loads(r.payload_json)
        if p.get("nivel_riesgo") == "ALTO":
            c[p["modalidad_detectada"]] += 1
    if c:
        modalidad, n = c.most_common(1)[0]
        if n >= UMBRAL:
            return {"alerta_activa": True, "modalidad": modalidad,
                    "titulo": f"Alerta en Bosa: {n} intentos de '{modalidad}' esta semana"}
    return {"alerta_activa": False, "titulo": "Sin alertas activas", "modalidad": ""}
