import os, time, statistics
from dotenv import load_dotenv

load_dotenv(".env")

from app.services import llm_service as s

s.TIMEOUT = 15.0  # solo para medir, sin que el límite de 2 s corte la prueba
key = os.environ["GEMINI_API_KEY"]
msg = "Su cuenta sera bloqueada hoy. Entre a http://banco-seguro.xyz y dicte el codigo que le llego por SMS"
MODELOS = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite"]
REPETICIONES = 5

s.precalentar()
for m in MODELOS:
    os.environ["GEMINI_MODEL"] = m
    tiempos = []
    for i in range(REPETICIONES):
        t = time.time()
        try:
            s._call_gemini(msg)
            tiempos.append(round(time.time() - t, 2))
        except Exception as e:
            print(m, "ERROR", str(e).replace(key, "***")[:160])
            break
    if tiempos:
        print(m, "tiempos:", tiempos, "| mediana:", statistics.median(tiempos), "| mínimo:", min(tiempos))