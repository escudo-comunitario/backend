"""Minimización de datos (Ley 1581/2012): se limpia todo antes de persistir o enviar al LLM."""
import re
from typing import Any

PII_KEYS = {
    "nombre", "nombres", "apellido", "cedula", "cédula", "documento", "correo", "email",
    "celular", "telefono", "teléfono", "phone", "cuenta", "clave", "password", "contrasena",
    "contraseña", "tarjeta", "direccion", "dirección",
}

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?<!\d)(?:\+?57[\s-]?)?3\d{2}[\s-]?\d{3}[\s-]?\d{4}(?!\d)")
_LONG_NUM = re.compile(r"(?<![\d])\d{6,}(?![\d])")


def scrub_text(text: str) -> str:
    text = _EMAIL.sub("[correo]", text)
    text = _PHONE.sub("[celular]", text)
    return _LONG_NUM.sub("[numero]", text)


def anonymize(value: Any) -> Any:
    """Recorre dicts/listas: elimina llaves con PII y enmascara PII dentro de textos."""
    if isinstance(value, dict):
        return {k: anonymize(v) for k, v in value.items() if str(k).lower() not in PII_KEYS}
    if isinstance(value, list):
        return [anonymize(v) for v in value]
    if isinstance(value, str):
        return scrub_text(value)
    return value
