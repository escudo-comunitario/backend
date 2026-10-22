"""Mide cuánto tarda Gemini con el prompt actual y con variantes que podrían acelerarlo.
Solo mide: no cambia nada del backend."""
import os, time, statistics
import httpx
from dotenv import load_dotenv

load_dotenv(".env")

from app.services import llm_service as s
from app.models.schemas import LLMVerdict

key = os.environ["GEMINI_API_KEY"]
model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MSG = ("Soporte Bancolombia: detectamos un ingreso sospechoso a su cuenta. Para evitar el bloqueo, "
       "dicte el código que le llegó por SMS al asesor.")

BASE = {
    "temperature": 0,
    "responseMimeType": "application/json",
    "responseSchema": s._strip_for_gemini(LLMVerdict.model_json_schema()),
}
VARIANTES = {
    "actual": {},
    "pensamiento minimo (thinkingLevel)": {"thinkingConfig": {"thinkingLevel": "minimal"}},
    "pensamiento apagado (thinkingBudget 0)": {"thinkingConfig": {"thinkingBudget": 0}},
    "tope de salida 500 tokens": {"maxOutputTokens": 500},
}


def limpio(txt: str) -> str:
    return txt.replace(key, "***")[:260]


s.precalentar()
print(f"Modelo: {model}\n")
for nombre, extra in VARIANTES.items():
    tiempos, ultimo = [], None
    for _ in range(3):
        t = time.time()
        try:
            r = s._client.post(URL, params={"key": key}, timeout=20, json={
                "systemInstruction": {"parts": [{"text": s.SYSTEM}]},
                "contents": [{"role": "user", "parts": [{"text": MSG}]}],
                "generationConfig": {**BASE, **extra},
            })
            if r.status_code != 200:
                print(f"{nombre}: ERROR {r.status_code} {limpio(r.text)}")
                tiempos = []
                break
            tiempos.append(round(time.time() - t, 2))
            ultimo = r.json()
        except Exception as e:
            print(f"{nombre}: ERROR {limpio(str(e))}")
            tiempos = []
            break
    if tiempos:
        u = (ultimo or {}).get("usageMetadata", {})
        print(f"{nombre}: {tiempos} | mediana {statistics.median(tiempos)} s | "
              f"tokens entrada {u.get('promptTokenCount')}, salida {u.get('candidatesTokenCount')}, "
              f"pensamiento {u.get('thoughtsTokenCount', 0)}")