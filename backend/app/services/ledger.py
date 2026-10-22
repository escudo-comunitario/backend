"""Registro encadenado: único punto que escribe en `incidents` (con lock para no bifurcar la cadena)."""
import json
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from sqlalchemy import func, text
from sqlalchemy.orm import Session

import integrity as forensic
from app.models.entities import Incident

_lock = threading.Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def register_incident(db: Session, payload: Dict[str, Any], upz: str, prefix: str = "ESC") -> Tuple[str, str, str, str]:
    """Persiste y encadena. Retorna (id, timestamp, hash_anterior, hash_actual)."""
    with _lock:
        last = db.query(Incident).order_by(text("rowid DESC")).first()
        prev = last.current_hash if last else forensic.GENESIS_HASH
        n = (db.query(func.count(Incident.id)).scalar() or 0) + 1
        ts = utc_now()
        rid = f"{prefix}-{ts[:4]}-BOSA-{n:04d}"
        payload_hash = forensic.calculate_payload_hash(payload)
        current = forensic.generate_record_hash(rid, ts, payload_hash, prev)
        db.add(Incident(id=rid, timestamp=ts, upz=upz, payload_json=json.dumps(payload),
                        previous_hash=prev, current_hash=current))
        db.commit()
    return rid, ts, prev, current


def load_chain(db: Session, limit: int | None = None):
    rows = db.query(Incident).order_by(text("rowid ASC")).all()
    if limit:
        rows = rows[:limit]
    return [{"id": r.id, "timestamp": r.timestamp, "payload": json.loads(r.payload_json),
             "previous_hash": r.previous_hash, "current_hash": r.current_hash} for r in rows]
