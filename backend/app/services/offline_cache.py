"""Escenarios deterministas para que el pitch nunca falle (regla cardinal #1)."""
from typing import Dict, Any

ESCENARIOS: Dict[int, Dict[str, Any]] = {
    1: {
        "nivel_riesgo": "ALTO", "color_semaforo": "ROJO",
        "modalidad_detectada": "Suplantación de Billetera Digital (Nequi / Daviplata)",
        "explicacion_ciudadana": "Están fingiendo ser de Daviplata para asustarlo con un falso embargo y pedirle que entre a una página falsa a poner su clave.",
        "audio_guion": "Peligro. No toque ningún enlace ni comparta claves. Su cuenta no tiene ningún problema.",
        "recomendaciones": [
            "No ingrese al enlace adjunto.",
            "No comparta contraseñas ni códigos que le lleguen por mensaje de texto.",
            "Avise de inmediato a su familiar de confianza.",
        ],
    },
    2: {
        "nivel_riesgo": "BAJO", "color_semaforo": "VERDE",
        "modalidad_detectada": "Mensaje institucional legítimo",
        "explicacion_ciudadana": "Es una invitación oficial de la Alcaldía Local. No le pide dinero, claves ni datos personales.",
        "audio_guion": "Mensaje seguro. Es una invitación oficial del barrio y no le pide claves ni dinero.",
        "recomendaciones": [
            "Puede asistir con tranquilidad.",
            "Confirme la fecha en los canales oficiales de la Alcaldía Local.",
        ],
    },
    3: {
        "nivel_riesgo": "ALTO", "color_semaforo": "ROJO",
        "modalidad_detectada": "Falsa Oferta Laboral con Anticipo de Dinero",
        "explicacion_ciudadana": "Le ofrecen un trabajo muy bueno pero le piden plata primero. Ninguna empresa seria cobra por exámenes médicos antes de contratar.",
        "audio_guion": "Alerta de engaño. Ningún trabajo legal le cobra dinero por exámenes médicos. No consigne nada.",
        "recomendaciones": [
            "No consigne dinero a nadie.",
            "Verifique la empresa por sus canales oficiales.",
            "Si ya pagó, guarde el comprobante y denuncie en el CAI Virtual.",
        ],
    },
}

# Respuesta prudente cuando no hay LLM y el texto no calza con ningún escenario.
GENERICO = {
    "nivel_riesgo": "MEDIO", "color_semaforo": "AMARILLO",
    "modalidad_detectada": "Posible fraude sin clasificar",
    "explicacion_ciudadana": "No pudimos confirmar si es seguro. Por precaución, no haga clic ni entregue datos hasta verificarlo.",
    "audio_guion": "Precaución. No comparta claves ni dinero hasta confirmar por un canal oficial.",
    "recomendaciones": [
        "No toque enlaces ni comparta códigos.",
        "Llame directamente a la entidad por su línea oficial.",
        "Consulte con un familiar de confianza.",
    ],
}

_PALABRAS = {
    1: ["daviplata", "nequi", "embargo", "embargada", "bloqueo", "juzgado", "http", "www."],
    2: ["alcaldía", "alcaldia", "cabildo", "entrada libre", "gratuita", "plaza fundacional"],
    3: ["vacante", "sueldo", "consigne", "exámenes", "examenes", "anticipo", "seleccionado", "empleo"],
}


def seleccionar_escenario(texto: str) -> Dict[str, Any]:
    t = texto.lower()
    puntajes = {k: sum(p in t for p in ps) for k, ps in _PALABRAS.items()}
    mejor = max(puntajes, key=puntajes.get)
    return dict(ESCENARIOS[mejor]) if puntajes[mejor] > 0 else dict(GENERICO)
