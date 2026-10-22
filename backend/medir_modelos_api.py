import os, time, statistics, requests
from dotenv import load_dotenv

load_dotenv(".env")
KEY = os.environ["GEMINI_API_KEY"]
MSG = "Su cuenta sera bloqueada hoy. Entre a http://banco-seguro.xyz y dicte el codigo que le llego por SMS"
MODELOS = [
    "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
]
REPETICIONES = 4

for m in MODELOS:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
    tiempos, errores = [], 0
    for _ in range(REPETICIONES):
        t = time.time()
        try:
            r = requests.post(
                url,
                headers={"x-goog-api-key": KEY},
                json={
                    "contents": [{"parts": [{"text": MSG}]}],
                    "generationConfig": {"maxOutputTokens": 100},
                },
                timeout=20,
            )
            if r.status_code == 200:
                tiempos.append(round(time.time() - t, 2))
            else:
                errores += 1
                print(m, "ERROR", r.status_code, r.text[:100].replace("\n", " "))
        except Exception as e:
            errores += 1
            print(m, "ERROR", str(e)[:100])
        time.sleep(0.5)
    if tiempos:
        print(m, tiempos, "| mediana:", statistics.median(tiempos), "| errores:", errores)
    else:
        print(m, "sin mediciones | errores:", errores)