import json
from app.services import llm_service


def _resp(nivel, color):
    return json.dumps({
        "nivel_riesgo": nivel, "color_semaforo": color,
        "modalidad_detectada": "X", "explicacion_ciudadana": "Y",
        "audio_guion": "Z", "recomendaciones": ["a"],
    })


def test_respuesta_coherente_pasa(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setattr(llm_service, "_call_openai", lambda t: _resp("ALTO", "ROJO"))
    assert llm_service.analizar_con_llm("hola").nivel_riesgo == "ALTO"


def test_nivel_y_color_incoherentes_caen_al_fallback(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    monkeypatch.setattr(llm_service, "_call_openai", lambda t: _resp("ALTO", "VERDE"))
    assert llm_service.analizar_con_llm("hola") is None


def test_json_invalido_cae_al_fallback(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    monkeypatch.setattr(llm_service, "_call_openai", lambda t: "esto no es json")
    assert llm_service.analizar_con_llm("hola") is None


def test_timeout_cae_al_fallback(monkeypatch):
    import time
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    monkeypatch.setattr(llm_service, "TIMEOUT", 0.2)
    monkeypatch.setattr(llm_service, "_call_openai", lambda t: (time.sleep(1), _resp("ALTO", "ROJO"))[1])
    assert llm_service.analizar_con_llm("hola") is None