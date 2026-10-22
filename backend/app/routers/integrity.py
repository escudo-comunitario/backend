from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import integrity as forensic
from app.database import get_db
from app.models.schemas import IntegrityResponse
from app.services import ledger

router = APIRouter()


@router.get("/verify-integrity", response_model=IntegrityResponse)
def verify_integrity(limit: Optional[int] = Query(None, ge=1), db: Session = Depends(get_db)):
    """`limit` audita los primeros N bloques (la cadena se valida desde el génesis)."""
    return forensic.verify_chain(ledger.load_chain(db, limit))
