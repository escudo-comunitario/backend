"""Análisis de comprobantes de pago por imagen con Gemini Vision y verificación de QR."""
import base64
import os
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import AnalyzeImageResponse, UPZS
from app.services import ledger, llm_service, open_data_service, privacy
from app.services.image_offline_cache import IMAGE_FALLBACK

router = APIRouter()

# Tipos MIME aceptados
MIME_PERMITIDOS = {"image/jpeg", "image/png"}

UPZ_POR_DEFECTO = "Bosa Central"

# Dominios oficiales de entidades financieras colombianas.
# Si el QR apunta a un dominio fuera de esta lista → señal de fraude.
DOMINIOS_LEGITIMOS = {
    "nequi.com",
    "daviplata.com",
    "bancolombia.com",
    "grupobancolombia.com",
    "davivienda.com",
    "pse.com.co",
    "exito.com",
    "efecty.com.co",
    "bbva.com.co",
    "movii.com.co",
    "colpatria.com",
    "bogota.gov.co",
}


def _dominio_es_legitimo(url: str) -> bool:
    """Extrae el dominio de la URL del QR y lo compara contra la whitelist."""
    try:
        netloc = urlparse(url).netloc.lower().removeprefix("www.")
        return any(netloc == d or netloc.endswith("." + d) for d in DOMINIOS_LEGITIMOS)
    except Exception:
        return False


def _recomendaciones_validas(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, str) and bool(item.strip()) for item in value)
    )


@router.post("/analyze-image", response_model=AnalyzeImageResponse)
async def analyze_image(
    imagen: UploadFile = File(..., description="Foto del comprobante (JPG o PNG)"),
    texto: str = Form(..., min_length=1, max_length=2000,
                      description="Describe qué pasó: quién te lo envió, qué te pidieron, etc."),
    upz: Optional[str] = Form(None, description="UPZ de Bosa donde ocurrió el incidente"),
    db: Session = Depends(get_db),
):
    """
    Analiza un comprobante de pago para determinar si es auténtico o falso.

    Pasos internos:
    1. Valida formato (JPG/PNG) y tamaño (≤ IMAGE_MAX_MB).
    2. Convierte la imagen a base64 y anonimiza el texto del ciudadano.
    3. Llama a Gemini Vision con imagen + texto + extracción de QR.
    4. Si hay URL en el QR, verifica el dominio contra la whitelist de entidades legítimas.
    5. Si el dominio es sospechoso, escala el riesgo a ALTO.
    6. Encadena el veredicto en el ledger criptográfico (prefix IMG-).
    """
    # ── 1. Validar formato ────────────────────────────────────────────────────
    if imagen.content_type not in MIME_PERMITIDOS:
        raise HTTPException(
            status_code=422,
            detail="Solo se aceptan imágenes en formato JPG o PNG.",
        )

    # ── 2. Leer y validar tamaño ──────────────────────────────────────────────
    image_bytes = await imagen.read()
    max_bytes = int(float(os.getenv("IMAGE_MAX_MB", "5")) * 1024 * 1024)
    if len(image_bytes) > max_bytes:
        max_mb = float(os.getenv("IMAGE_MAX_MB", "5"))
        raise HTTPException(
            status_code=413,
            detail=f"La imagen supera el tamaño máximo permitido de {max_mb:.0f} MB.",
        )

    # ── 3. Validar UPZ ────────────────────────────────────────────────────────
    upz_final = upz or UPZ_POR_DEFECTO
    if upz_final not in UPZS:
        raise HTTPException(
            status_code=422,
            detail=f"UPZ inválida. Opciones: {', '.join(UPZS)}",
        )

    # ── 4. Anonimizar texto del ciudadano (no enviar PII al LLM) ─────────────
    texto_limpio = privacy.scrub_text(texto)

    # ── 5. Codificar imagen en base64 ─────────────────────────────────────────
    image_b64 = base64.b64encode(image_bytes).decode()

    # ── 6. Analizar con Gemini Vision (o fallback si falla) ───────────────────
    verdict = llm_service.analizar_imagen_con_llm(image_b64, imagen.content_type, texto_limpio)
    resultado = verdict.model_dump() if verdict else dict(IMAGE_FALLBACK)

    # ── 7. Verificar dominio del QR extraído ──────────────────────────────────
    url_qr = resultado.get("url_qr_extraida") or ""
    qr_dominio_legitimo: Optional[bool] = None

    if url_qr:
        qr_dominio_legitimo = _dominio_es_legitimo(url_qr)
        if not qr_dominio_legitimo:
            # El QR apunta a un dominio no oficial → escalar riesgo a ALTO
            resultado["nivel_riesgo"] = "ALTO"
            resultado["color_semaforo"] = "ROJO"
            dominio_detectado = urlparse(url_qr).netloc.lower()
            resultado["senales_detectadas"].append(
                f"El QR apunta a un dominio no oficial: {dominio_detectado}"
            )

    # Reutiliza recomendaciones seguras ya definidas y conserva el resto del veredicto.
    if not _recomendaciones_validas(resultado.get("recomendaciones")):
        fallback_recommendations = IMAGE_FALLBACK.get("recomendaciones")
        if not _recomendaciones_validas(fallback_recommendations):
            raise HTTPException(
                status_code=500,
                detail="No fue posible preparar recomendaciones válidas para el análisis.",
            )
        resultado["recomendaciones"] = [item.strip() for item in fallback_recommendations]
    else:
        resultado["recomendaciones"] = [item.strip() for item in resultado["recomendaciones"]]

    # Gemini aporta hasta cuatro señales y el endpoint puede añadir una advertencia QR.
    # Si se rompe ese invariante, no se registran ni descartan señales: se responde con error.
    senales = resultado.get("senales_detectadas")
    if not isinstance(senales, list) or len(senales) > 5 or not all(isinstance(item, str) for item in senales):
        raise HTTPException(
            status_code=502,
            detail="El análisis no produjo una lista de señales válida.",
        )

    # ── 8. Registrar en el ledger (no se guarda la imagen, solo el veredicto) ─
    payload = {
        **resultado,
        "modo": "foto",
        "upz": upz_final,
        "texto_contexto": texto_limpio,      # Texto ya anonimizado
        "qr_dominio_legitimo": qr_dominio_legitimo,
    }
    rid, ts, prev, current = ledger.register_incident(db, payload, upz_final, prefix="IMG")

    # ── 9. Construir y devolver respuesta ─────────────────────────────────────
    return {
        "id_analisis": rid,
        "timestamp": ts,
        **resultado,
        "url_qr_extraida": url_qr or None,
        "qr_dominio_legitimo": qr_dominio_legitimo,
        "evidencia_criptografica": {
            "hash_actual": current,
            "hash_anterior": prev,
            "cadena_valida": True,
            "qr_payload_url": f"https://escudo-bosa.gov.co/verify?id={rid}",
        },
        "datos_abiertos_referencia": {
            "fuente": open_data_service.FUENTE,
            "coincidencias_similares_mes": open_data_service.coincidencias_mes(
                resultado.get("entidad_detectada", "Posible fraude sin clasificar")
            ),
        },
    }
