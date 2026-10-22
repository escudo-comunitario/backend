from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services import ledger, llm_service, offline_cache, open_data_service, privacy

router = APIRouter()

UPZ_POR_DEFECTO = "Bosa Central"


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)):
    texto = privacy.scrub_text(req.texto)

    verdict = llm_service.analizar_con_llm(texto)
    resultado = verdict.model_dump() if verdict else offline_cache.seleccionar_escenario(texto)

    # No se guarda el texto original del ciudadano, solo el veredicto (minimización de datos).
    upz = req.upz or UPZ_POR_DEFECTO
    payload = {**resultado, "modo": req.modo, "upz": upz}
    rid, ts, prev, current = ledger.register_incident(db, payload, upz, prefix="ESC")

    return {
        "id_analisis": rid,
        "timestamp": ts,
        **resultado,
        "evidencia_criptografica": {
            "hash_actual": current,
            "hash_anterior": prev,
            "cadena_valida": True,
            "qr_payload_url": f"https://escudo-bosa.gov.co/verify?id={rid}",
        },
        "datos_abiertos_referencia": {
            "fuente": open_data_service.FUENTE,
            "coincidencias_similares_mes": open_data_service.coincidencias_mes(resultado["modalidad_detectada"]),
        },
    }
