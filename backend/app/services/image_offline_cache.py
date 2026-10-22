"""Fallback determinista para análisis de imágenes cuando Gemini Vision no está disponible."""
from typing import Dict, Any

IMAGE_FALLBACK: Dict[str, Any] = {
    "es_autentico": "SOSPECHOSO",
    "nivel_riesgo": "MEDIO",
    "color_semaforo": "AMARILLO",
    "entidad_detectada": "No identificada",
    "senales_detectadas": ["No fue posible analizar la imagen automáticamente"],
    "url_qr_extraida": "",
    "explicacion_ciudadana": (
        "No pudimos verificar el comprobante ahora. "
        "Por precaución, no realice ningún pago hasta confirmarlo con la entidad."
    ),
    "audio_guion": "Precaución. Confirme este comprobante directamente con su banco antes de pagar.",
    "recomendaciones": [
        "Llame a su banco por el número oficial.",
        "No realice ningún pago hasta confirmar.",
    ],
}
