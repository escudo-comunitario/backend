from dotenv import load_dotenv
load_dotenv(".env")

import time
from app.services import llm_service as s

texto = "Soporte Bancolombia: detectamos un ingreso sospechoso a su cuenta. Para evitar el bloqueo, dicte el código que le llegó por SMS al asesor."
for i in range(3):
    t = time.time()
    r = s.analizar_con_llm(texto)
    print(f"Intento {i+1}: {round(time.time()-t, 2)} s ->",
          r.model_dump() if r else "None (cayó a la caché)")