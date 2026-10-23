"""Tests para el endpoint /api/analyze-image."""
import json
import base64
import os

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from app.main import app
from app.services import llm_service
from app.models.schemas import AnalyzeImageResponse, ImageVerdict
from app.services.image_offline_cache import IMAGE_FALLBACK
# La BD de tests es gestionada por conftest.py: DATABASE_URL apunta a un archivo temporal.


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_verdict(**kwargs) -> str:
    """Genera un JSON de ImageVerdict válido con valores por defecto."""
    base = {
        "es_autentico": "FALSO",
        "nivel_riesgo": "ALTO",
        "color_semaforo": "ROJO",
        "entidad_detectada": "Nequi",
        "senales_detectadas": ["Logo pixelado", "Tipografía inconsistente"],
        "url_qr_extraida": "",
        "explicacion_ciudadana": "El logo está pixelado y la tipografía no corresponde a Nequi.",
        "audio_guion": "Peligro. Este comprobante parece falso. No realice ningún pago.",
        "recomendaciones": ["No realice ningún pago.", "Llame a Nequi por la línea oficial."],
    }
    base.update(kwargs)
    return json.dumps(base)


def _fake_image_bytes() -> bytes:
    """Imagen JPEG mínima válida (1x1 píxel blanco)."""
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
        b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
        b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\x1e"
        b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00"
        b"\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00"
        b"\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00"
        b"\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142\x81"
        b"\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19"
        b"\x1a%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86"
        b"\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4"
        b"\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2"
        b"\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9"
        b"\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5"
        b"\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd7\xff\xd9"
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_imagen_falsa_retorna_veredicto(monkeypatch):
    """LLM mockeado que devuelve FALSO → respuesta 200 con color ROJO."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setattr(llm_service, "_call_gemini_image",
                        lambda b64, mime, txt: _make_verdict())

    with TestClient(app) as c:
        r = c.post(
            "/api/analyze-image",
            files={"imagen": ("comprobante.jpg", _fake_image_bytes(), "image/jpeg")},
            data={"texto": "Me mandaron este comprobante y me piden pagar $50.000 para liberarlo."},
        )
    assert r.status_code == 200
    d = r.json()
    assert d["es_autentico"] == "FALSO"
    assert d["color_semaforo"] == "ROJO"
    assert d["nivel_riesgo"] == "ALTO"
    assert d["evidencia_criptografica"]["hash_anterior"] is not None
    assert d["id_analisis"].startswith("IMG-")


def test_imagen_autentica_retorna_verde(monkeypatch):
    """LLM mockeado que devuelve AUTENTICO → respuesta 200 con color VERDE."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setattr(
        llm_service, "_call_gemini_image",
        lambda b64, mime, txt: _make_verdict(
            es_autentico="AUTENTICO", nivel_riesgo="BAJO", color_semaforo="VERDE",
            senales_detectadas=["Logo consistente con Nequi", "QR bien formado"],
        ),
    )

    with TestClient(app) as c:
        r = c.post(
            "/api/analyze-image",
            files={"imagen": ("comprobante.jpg", _fake_image_bytes(), "image/jpeg")},
            data={"texto": "Me enviaron este comprobante de pago, ¿es real?"},
        )
    assert r.status_code == 200
    assert r.json()["color_semaforo"] == "VERDE"


def test_qr_dominio_oficial_legitimo(monkeypatch):
    """QR con dominio bancolombia.com → qr_dominio_legitimo=True, riesgo no escala."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setattr(
        llm_service, "_call_gemini_image",
        lambda b64, mime, txt: _make_verdict(
            es_autentico="AUTENTICO", nivel_riesgo="BAJO", color_semaforo="VERDE",
            url_qr_extraida="https://bancolombia.com/verify?tx=ABC123",
        ),
    )

    with TestClient(app) as c:
        r = c.post(
            "/api/analyze-image",
            files={"imagen": ("comprobante.jpg", _fake_image_bytes(), "image/jpeg")},
            data={"texto": "Me enviaron este comprobante."},
        )
    assert r.status_code == 200
    d = r.json()
    assert d["qr_dominio_legitimo"] is True
    assert d["url_qr_extraida"] == "https://bancolombia.com/verify?tx=ABC123"
    # Dominio legítimo → riesgo no debe escalarse
    assert d["nivel_riesgo"] == "BAJO"


def test_qr_dominio_sospechoso_escala_riesgo(monkeypatch):
    """QR con dominio phishing → qr_dominio_legitimo=False y riesgo escala a ALTO."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setattr(
        llm_service, "_call_gemini_image",
        lambda b64, mime, txt: _make_verdict(
            es_autentico="SOSPECHOSO", nivel_riesgo="MEDIO", color_semaforo="AMARILLO",
            url_qr_extraida="https://nequi-pagos-bosa.xyz/verify?id=999",
        ),
    )

    with TestClient(app) as c:
        r = c.post(
            "/api/analyze-image",
            files={"imagen": ("comprobante.jpg", _fake_image_bytes(), "image/jpeg")},
            data={"texto": "Me mandaron este comprobante con un link raro."},
        )
    assert r.status_code == 200
    d = r.json()
    assert d["qr_dominio_legitimo"] is False
    # Dominio sospechoso → debe escalar a ALTO/ROJO
    assert d["nivel_riesgo"] == "ALTO"
    assert d["color_semaforo"] == "ROJO"
    # La señal del dominio debe aparecer en la lista
    assert any("dominio no oficial" in s for s in d["senales_detectadas"])


def test_cuatro_senales_mas_advertencia_qr_conserva_las_cinco(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    senales = ["Señal uno", "Señal dos", "Señal tres", "Señal cuatro"]
    monkeypatch.setattr(
        llm_service,
        "_call_gemini_image",
        lambda b64, mime, txt: _make_verdict(
            senales_detectadas=senales,
            url_qr_extraida="https://pagos-no-oficiales.example/tx",
        ),
    )

    with TestClient(app) as c:
        r = c.post(
            "/api/analyze-image",
            files={"imagen": ("comprobante.jpg", _fake_image_bytes(), "image/jpeg")},
            data={"texto": "Verificar comprobante."},
        )

    assert r.status_code == 200
    assert r.json()["senales_detectadas"] == senales + [
        "El QR apunta a un dominio no oficial: pagos-no-oficiales.example"
    ]


@pytest.mark.parametrize("recommendations_count", [0, 1, 2, 3])
def test_recomendaciones_cantidad_y_conservacion_de_senales(monkeypatch, recommendations_count):
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    signals = ["El nombre del remitente no coincide", "El monto fue alterado"]
    recommendations = [f"Acción {i + 1}" for i in range(recommendations_count)]
    monkeypatch.setattr(
        llm_service,
        "_call_gemini_image",
        lambda b64, mime, txt: _make_verdict(
            senales_detectadas=signals,
            recomendaciones=recommendations,
        ),
    )

    with TestClient(app) as c:
        r = c.post(
            "/api/analyze-image",
            files={"imagen": ("comprobante.jpg", _fake_image_bytes(), "image/jpeg")},
            data={"texto": "Verificar comprobante."},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["senales_detectadas"] == signals
    if recommendations_count == 2:
        assert body["recomendaciones"] == recommendations
    else:
        assert body["recomendaciones"] == IMAGE_FALLBACK["recomendaciones"]
    assert len(body["recomendaciones"]) == 2
    assert all(item.strip() for item in body["recomendaciones"])


def test_recomendaciones_en_blanco_usan_fallback_sin_perder_senales(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    signals = ["Comprobante con inconsistencia visual"]
    monkeypatch.setattr(
        llm_service,
        "_call_gemini_image",
        lambda b64, mime, txt: _make_verdict(
            senales_detectadas=signals,
            recomendaciones=["  ", "Acción válida"],
        ),
    )

    with TestClient(app) as c:
        r = c.post(
            "/api/analyze-image",
            files={"imagen": ("comprobante.jpg", _fake_image_bytes(), "image/jpeg")},
            data={"texto": "Verificar comprobante."},
        )

    assert r.status_code == 200
    assert r.json()["senales_detectadas"] == signals
    assert r.json()["recomendaciones"] == IMAGE_FALLBACK["recomendaciones"]


def test_recomendaciones_validas_se_recortan_en_respuesta(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setattr(
        llm_service,
        "_call_gemini_image",
        lambda b64, mime, txt: _make_verdict(
            recomendaciones=["  Primera acción  ", " Segunda acción "]
        ),
    )

    with TestClient(app) as c:
        r = c.post(
            "/api/analyze-image",
            files={"imagen": ("comprobante.jpg", _fake_image_bytes(), "image/jpeg")},
            data={"texto": "Verificar comprobante."},
        )

    assert r.status_code == 200
    assert r.json()["recomendaciones"] == ["Primera acción", "Segunda acción"]


def test_exceso_de_senales_del_modelo_activa_fallback_sin_truncar(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    too_many_signals = [f"Señal {i}" for i in range(5)]
    monkeypatch.setattr(
        llm_service,
        "_call_gemini_image",
        lambda b64, mime, txt: _make_verdict(senales_detectadas=too_many_signals),
    )

    with TestClient(app) as c:
        r = c.post(
            "/api/analyze-image",
            files={"imagen": ("comprobante.jpg", _fake_image_bytes(), "image/jpeg")},
            data={"texto": "Verificar comprobante."},
        )

    assert r.status_code == 200
    assert r.json()["senales_detectadas"] == IMAGE_FALLBACK["senales_detectadas"]
    assert r.json()["senales_detectadas"] != too_many_signals


def test_modelo_propaga_error_de_programacion_en_vez_de_fallback(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake")

    def raise_unexpected_error(*args):
        raise RuntimeError("unexpected programming error")

    monkeypatch.setattr(llm_service, "_call_gemini_image", raise_unexpected_error)
    with pytest.raises(RuntimeError, match="unexpected programming error"):
        llm_service.analizar_imagen_con_llm("image", "image/jpeg", "context")


def test_respuesta_rechaza_recomendaciones_no_validas():
    base = {
        "id_analisis": "IMG-test",
        "timestamp": "2026-01-01T00:00:00Z",
        "es_autentico": "FALSO",
        "nivel_riesgo": "ALTO",
        "color_semaforo": "ROJO",
        "entidad_detectada": "Nequi",
        "senales_detectadas": ["Señal"],
        "url_qr_extraida": None,
        "qr_dominio_legitimo": None,
        "explicacion_ciudadana": "Explicación",
        "audio_guion": "Peligro",
        "recomendaciones": ["Primera", "   "],
        "evidencia_criptografica": {
            "hash_actual": "a",
            "hash_anterior": "b",
            "cadena_valida": True,
            "qr_payload_url": "https://example.test/verify",
        },
        "datos_abiertos_referencia": {"fuente": "test", "coincidencias_similares_mes": 0},
    }
    with pytest.raises(ValidationError):
        AnalyzeImageResponse.model_validate(base)


def test_sin_qr_dominio_es_none(monkeypatch):
    """Sin QR en la imagen → url_qr_extraida=None, qr_dominio_legitimo=None."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setattr(llm_service, "_call_gemini_image",
                        lambda b64, mime, txt: _make_verdict(url_qr_extraida=""))

    with TestClient(app) as c:
        r = c.post(
            "/api/analyze-image",
            files={"imagen": ("comprobante.jpg", _fake_image_bytes(), "image/jpeg")},
            data={"texto": "No tiene QR este comprobante."},
        )
    assert r.status_code == 200
    d = r.json()
    assert d["url_qr_extraida"] is None
    assert d["qr_dominio_legitimo"] is None


def test_formato_invalido_rechazado():
    """Subir un PDF → HTTP 422."""
    with TestClient(app) as c:
        r = c.post(
            "/api/analyze-image",
            files={"imagen": ("doc.pdf", b"%PDF-1.4 fake", "application/pdf")},
            data={"texto": "Este es un PDF."},
        )
    assert r.status_code == 422
    assert "JPG o PNG" in r.json()["detail"]


def test_imagen_muy_grande_rechazada():
    """Imagen > IMAGE_MAX_MB → HTTP 413. Usa bytes grandes directamente sin tocar el módulo."""
    # El límite por defecto es 5 MB. Creamos un payload de ~6 MB.
    fake_large = b"\xff\xd8" + b"x" * (6 * 1024 * 1024)
    with TestClient(app) as c:
        r = c.post(
            "/api/analyze-image",
            files={"imagen": ("grande.jpg", fake_large, "image/jpeg")},
            data={"texto": "Imagen muy grande."},
        )
    assert r.status_code == 413


def test_upz_invalida_rechazada():
    """UPZ que no existe → HTTP 422."""
    with TestClient(app) as c:
        r = c.post(
            "/api/analyze-image",
            files={"imagen": ("comprobante.jpg", _fake_image_bytes(), "image/jpeg")},
            data={"texto": "Comprobante sospechoso.", "upz": "Chapinero"},
        )
    assert r.status_code == 422


def test_llm_falla_usa_fallback():
    """Sin API key → usa IMAGE_FALLBACK (SOSPECHOSO/AMARILLO), respuesta 200."""
    with TestClient(app) as c:
        r = c.post(
            "/api/analyze-image",
            files={"imagen": ("comprobante.jpg", _fake_image_bytes(), "image/jpeg")},
            data={"texto": "Me mandaron este comprobante."},
        )
    assert r.status_code == 200
    d = r.json()
    assert d["es_autentico"] == "SOSPECHOSO"
    assert d["color_semaforo"] == "AMARILLO"
    assert d["id_analisis"].startswith("IMG-")


def test_encadenamiento_imagen_con_texto(monkeypatch):
    """Un análisis de texto seguido de uno de imagen → la cadena queda íntegra."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setattr(llm_service, "_call_gemini_image",
                        lambda b64, mime, txt: _make_verdict())

    with TestClient(app) as c:
        # Análisis de texto (usa offline_cache sin API key de texto)
        r1 = c.post("/api/analyze", json={
            "texto": "Su cuenta Daviplata será embargada. Entre a http://daviplata-bosa.cc",
            "upz": "Bosa Central",
        })
        assert r1.status_code == 200

        # Análisis de imagen
        r2 = c.post(
            "/api/analyze-image",
            files={"imagen": ("comprobante.jpg", _fake_image_bytes(), "image/jpeg")},
            data={"texto": "Me mandaron este comprobante falso.", "upz": "El Porvenir"},
        )
        assert r2.status_code == 200

        # La cadena debe estar íntegra
        integridad = c.get("/api/verify-integrity")
        assert integridad.json()["integro"] is True
        assert integridad.json()["bloques_auditados"] >= 2
