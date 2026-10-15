# AGENTS.md — Protocolo del Agente de Inteligencia Artificial (Backend & Ciberseguridad)

**Módulo:** Servidor RESTful, Subsistemas de Ciberseguridad Forense, Inferencia y Persistencia  
**Ubicación en Repositorio:** `backend/`  
**Iniciativa:** Escudo Comunitario  
**Equipo:** Bacata Tech Group  
**Responsables Técnicos:**  
* **Diego:** Líder Backend (FastAPI, orquestación LLM, datos abiertos y persistencia)  
* **Erick:** Líder Ciberseguridad (Módulo criptográfico `integrity.py`, hash chaining, validación forense)  
* **Daniel:** DevOps y Calidad (Persistencia, variables de entorno y soporte del pitch)  
**Marco Operativo:** Hackathon Colombia 5.0 (MinTIC / Universidad Distrital Francisco José de Caldas)  

---

## 1. Misión y Alcance del Agente Backend

Este protocolo dicta los estándares técnicos, restricciones operativas y patrones arquitectónicos que deben seguir los agentes de Inteligencia Artificial, desarrolladores y asistentes que operen sobre el entorno `backend/`.

La responsabilidad crítica del backend es proveer una API de **alta velocidad (latencias $< 200\text{ ms}$ en orquestación local)**, **tolerancia absoluta a cortes de conexión a internet (resiliencia offline)** y **validez probatoria pericial conforme a la Ley 527 de 1999 e ISO/IEC 27037**, protegiendo la privacidad ciudadana bajo el marco de la Ley 1581 de 2012.

---

## 2. Reglas Cardinales del Backend (Inviolables)

1. **Principio Offline-First / Cero Caídas en Demostración:**  
   El backend no debe depender de enlaces a servicios en la nube en tiempo real para sostener el funcionamiento continuo del sistema. Se implementará un mecanismo de contingencia con una memoria caché local precargada con los tres casos típicos de Bosa y un catálogo local de Datos Abiertos Bogotá (`delitos_bosa_local.json`). Si una llamada a proveedores externos de LLM demora más de $2.0\text{ s}$ o falla la red, el sistema conmutará de inmediato a la respuesta determinista sin arrojar errores `500` ni bloquear la interfaz del ciudadano.

2. **Persistencia Ligera y Embebida con SQLite:**  
   La persistencia se gestiona exclusivamente a través de SQLite (`sqlite:///./escudo.db`). Queda vetado el uso obligatorio de contenedores Docker, bases de datos remotas en PostgreSQL o servicios BaaS como Firebase durante la hackathon. La persistencia debe correr en el mismo proceso de ejecución de Python sin pasos complejos de aprovisionamiento.

3. **Inferencia Estructurada Obligatoria (Structured Outputs / JSON Mode):**  
   Toda interacción con LLMs (OpenAI o Google Gemini) debe forzar respuestas estrictamente estructuradas en formato JSON mapeadas uno a uno con esquemas de Pydantic v2. Queda prohibido el análisis heurístico con expresiones regulares sobre bloques de texto no estructurado.

4. **Integridad Criptográfica Pura con Python Estándar:**  
   El encadenamiento de auditoría forense (`integrity.py`) debe desarrollarse sobre la librería estándar `hashlib` de Python. No se admiten dependencias de contratos inteligentes ni cadenas de bloques (blockchains) pesadas que introduzcan consumo intensivo de memoria o latencias innecesarias.

5. **Privacidad Irreversible y Minimización de Datos (Ley 1581 de 2012 y Ley 1273 de 2009):**  
   Está estrictamente prohibido persistir o recibir en endpoints: nombres, números de cédula, correos personales, números celulares directos o credenciales bancarias. Toda georreferenciación de incidentes se abstrae a nivel de **UPZ** (Bosa Central, Bosa Occidental, Tintal Sur, El Porvenir).

6. **Desacoplamiento Absoluto y Compatibilidad con el Frontend:**  
   Cualquier cambio en la salida de los endpoints debe respetar de manera exacta la especificación de `mock_response.json` para no romper el cliente React de Emanuel. Los encabezados CORS deben permanecer abiertos para `http://localhost:5173` y `http://127.0.0.1:5173`.

---

## 3. Topología de Archivos del Backend

```
backend/
├── app/
│   ├── data/
│   │   └── delitos_bosa_local.json    # Catálogo histórico local extraído de datos.gov.co
│   ├── routers/
│   │   ├── analyze.py                 # POST /api/analyze (Orquestación LLM + Fallback)
│   │   ├── reports.py                 # POST /api/report (Anonimización y registro SQLite)
│   │   ├── integrity.py               # GET /api/verify-integrity (Auditoría de cadena)
│   │   ├── campaigns.py               # GET /api/campaigns/latest (Alertas masivas push)
│   │   └── stats.py                   # GET /api/stats (Métricas agregadas por UPZ)
│   ├── services/
│   │   ├── llm_service.py             # Integración con LLM y manejo de Structured Outputs
│   │   ├── offline_cache.py           # Escenarios deterministas pregrabados para el pitch
│   │   └── open_data_service.py       # Cruce instantáneo con histórico de Bosa
│   ├── models/
│   │   ├── schemas.py                 # Modelos Pydantic v2 (Request/Response)
│   │   └── entities.py                # Modelos de tablas SQLAlchemy para SQLite
│   ├── database.py                    # Configuración de Engine SQLite y SessionLocal
│   └── main.py                        # Instancia FastAPI ASGI, CORS y montaje de rutas
├── tests/
│   ├── test_tamper.py                 # Script de prueba de adulteración (Pitch Erick)
│   └── test_chain.py                  # Pruebas unitarias de integridad matemática
├── integrity.py                       # Módulo forense desacoplado de Hash-Chaining (Erick)
├── requirements.txt                   # Dependencias estrictas y ligeras
└── .env.example                       # Plantilla de variables de entorno
```

---

## 4. Contrato Canónico de Datos (`mock_response.json`)

El modelo canónico que orquesta la respuesta del análisis de incidentes se define como:

```json
{
  "id_analisis": "ESC-2026-BOSA-0042",
  "timestamp": "2026-10-22T14:30:00Z",
  "nivel_riesgo": "ALTO",
  "color_semaforo": "ROJO",
  "modalidad_detectada": "Suplantación de Billetera Digital (Nequi / Daviplata)",
  "explicacion_ciudadana": "Están fingiendo ser de Daviplata para asustarlo con un falso embargo y pedirle que entre a una página falsa a poner su clave.",
  "audio_guion": "Peligro. No toque ningún enlace ni comparta claves. Su cuenta no tiene ningún problema.",
  "recomendaciones": [
    "No ingrese al enlace adjunto.",
    "No comparta contraseñas ni códigos que le lleguen por mensaje de texto.",
    "Avise de inmediato a su familiar de confianza."
  ],
  "evidencia_criptografica": {
    "hash_actual": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "hash_anterior": "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92",
    "cadena_valida": true,
    "qr_payload_url": "https://escudo-bosa.gov.co/verify?id=ESC-2026-BOSA-0042"
  },
  "datos_abiertos_referencia": {
    "fuente": "Datos Abiertos Bogotá - Delitos Informáticos Bosa",
    "coincidencias_similares_mes": 28
  }
}
```

---

## 5. Especificación de Endpoints del Backend

FastAPI expone cinco controladores REST esenciales:

| Verbo HTTP y Ruta | Estructura de Entrada | Respuesta Estructurada | Función en la Arquitectura |
| :--- | :--- | :--- | :--- |
| `POST /api/analyze` | `{"texto": str, "modo": "voz" \| "texto", "upz": Optional[str]}` | Estructura canónica completa de `mock_response.json` | Orquesta la inferencia semántica con el LLM o despacha desde la memoria caché de contingencia en caso de fallo de red. |
| `POST /api/report` | `{"payload": dict, "upz": str}` | `{"status": "registrado", "hash": str, "id": str}` | Anonimiza el reporte, lo persiste en SQLite y ejecuta el encadenamiento del hash criptográfico. |
| `GET /api/verify-integrity` | Parámetro opcional: `limit: Optional[int]` | `{"integro": bool, "bloques_auditados": int, "registro_alterado": Optional[str]}` | Recorre la totalidad de la cadena histórica revalidando la correspondencia matemática de punteros. |
| `GET /api/campaigns/latest` | Ninguna | `{"alerta_activa": bool, "titulo": str, "modalidad": str}` | Recupera la última alerta masiva comunitaria para emitir notificaciones push proactivas en el barrio. |
| `GET /api/stats` | Parámetro opcional: `dias: Optional[int]` | `{"por_modalidad": dict, "por_upz": dict}` | Provee métricas agregadas y anonimizadas para alimentar el radar territorial por UPZ de Bosa. |

---

## 6. Módulo de Integridad Criptográfica Forense (`integrity.py`)

Diseñado bajo la supervisión de Erick, este componente provee valor probatorio según la Ley 527 de 1999 e ISO/IEC 27037 mediante dos formulaciones matemáticas:

### Ecuación 1: Derivación Determinista del Resumen de Carga Útil (Payload Hash)
$$\text{Payload Hash} = \text{SHA-256}(\text{JSON\_Serializado}(\text{Payload}))$$

### Ecuación 2: Cómputo del Encadenamiento Criptográfico de Bloque (Current Hash)
$$\text{Current Hash} = \text{SHA-256}(\text{ID} \parallel \text{Timestamp} \parallel \text{Payload Hash} \parallel \text{Previous Hash})$$

*(Para el registro génesis inicial, $\text{Previous Hash} = \text{"0" \times 64}$)*.

### Código Oficial de `integrity.py`
```python
import hashlib
import json
from typing import List, Dict, Any, Optional

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def calculate_payload_hash(data: Dict[str, Any]) -> str:
    """Serializa de forma determinista el diccionario y computa su SHA-256."""
    serialized = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

def generate_record_hash(record_id: str, timestamp: str, payload_hash: str, previous_hash: str) -> str:
    """Concatena los elementos canónicos del bloque y deriva el hash actual."""
    raw_block = f"{record_id}|{timestamp}|{payload_hash}|{previous_hash}"
    return hashlib.sha256(raw_block.encode('utf-8')).hexdigest()

def verify_chain(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Inspecciona la secuencia histórica de registros.
    Retorna estado de validez y localiza anomalías si existen.
    """
    if not records:
        return {"integro": True, "bloques_auditados": 0, "registro_alterado": None}

    for i in range(len(records)):
        curr = records[i]
        expected_prev = GENESIS_HASH if i == 0 else records[i - 1]['current_hash']

        # Validación de puntero secuencial
        if curr['previous_hash'] != expected_prev:
            return {
                "integro": False,
                "bloques_auditados": i,
                "registro_alterado": curr.get('id', f"indice_{i}"),
                "motivo": "Ruptura en el enlace de puntero previo"
            }

        # Recálculo matemático independiente del contenido
        payload_h = calculate_payload_hash(curr['payload'])
        recalculated = generate_record_hash(
            curr['id'], curr['timestamp'], payload_h, curr['previous_hash']
        )

        if recalculated != curr['current_hash']:
            return {
                "integro": False,
                "bloques_auditados": i + 1,
                "registro_alterado": curr.get('id', f"indice_{i}"),
                "motivo": "Alteración interna de contenido (Payload adulterado)"
            }

    return {"integro": True, "bloques_auditados": len(records), "registro_alterado": None}
```

---

## 7. Subsistema de Inferencia y Contingencia Determinista (`offline_cache.py`)

Para blindar la presentación en vivo ante caídas de red o demoras en la API externa del LLM, el servicio implementa una guarda de tiempo límite ($2.0\text{ s}$). Si se excede o hay fallo de red, se selecciona automáticamente uno de los 3 escenarios deterministas precargados:

1. **Escenario 1 (Riesgo ALTO / Semáforo ROJO — Suplantación de Daviplata / Nequi):**
   * *Entrada típica:* «Su cuenta Daviplata será embargada hoy por juzgado. Evite bloqueo entrando a: http://daviplata-embargos-bosa.cc».
   * *Diagnóstico:* Suplantación de identidad financiera y secuestro emocional por urgencia simulada.
   * *Audio guion:* «Peligro. No toque ningún enlace ni comparta claves. Su cuenta no tiene ningún problema.»

2. **Escenario 2 (Riesgo BAJO / Semáforo VERDE — Mensaje Institucional Legítimo):**
   * *Entrada típica:* «Alcaldía Local de Bosa invita al cabildo ciudadano en la Plaza Fundacional este sábado a las 9 am. Entrada libre y gratuita».
   * *Diagnóstico:* Comunicación institucional auténtica sin solicitud de datos sensibles ni redirecciones sospechosas.
   * *Audio guion:* «Mensaje seguro. Es una invitación oficial del barrio y no le pide claves ni dinero.»

3. **Escenario 3 (Riesgo ALTO / Semáforo ROJO — Falsa Oferta Laboral con Anticipo de Dinero):**
   * *Entrada típica:* «Seleccionado para vacante de logística en Bosa con sueldo de 3 millones. Consigne 45 mil pesos para exámenes médicos antes de las 3pm».
   * *Diagnóstico:* Estafa por cobro fraudulento de trámites de contratación.
   * *Audio guion:* «Alerta de engaño. Ningún trabajo legal le cobra dinero por exámenes médicos. No consigne nada.»

---

## 8. Persistencia y Consulta Territorial (`open_data_service.py`)

* **Base de datos SQLite:** Esquema plano en `escudo.db` con tabla `incidents`:
  * `id`: VARCHAR(64) PRIMARY KEY
  * `timestamp`: VARCHAR(32)
  * `upz`: VARCHAR(64)
  * `payload_json`: TEXT
  * `previous_hash`: VARCHAR(64)
  * `current_hash`: VARCHAR(64)
* **Datos Abiertos:** Se precarga en memoria un extracto estructurado de delitos informáticos en Bosa desde `app/data/delitos_bosa_local.json`. La consulta entrega agregados directos para el endpoint `/api/stats` permitiendo calcular tendencias mensuales sin realizar llamadas HTTP externas.

---

## 9. Script Demostrador de Adulteración Forense (`tests/test_tamper.py`)

Diseñado para la intervención de Erick durante el **minuto 3** del pitch:

```python
import sqlite3
import json
import sys

def simulate_evidence_tampering(db_path="escudo.db", target_id="ESC-2026-BOSA-0042"):
    """
    Modifica silenciosamente un solo carácter dentro del payload de un incidente en SQLite
    para demostrar que el recálculo SHA-256 en /api/verify-integrity expone el fraude.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Consultar el registro original
        cursor.execute("SELECT payload_json FROM incidents WHERE id = ?", (target_id,))
        row = cursor.fetchone()

        if not row:
            print(f"[!] Registro {target_id} no encontrado. Creando entrada de prueba...")
            return

        payload = json.loads(row[0])
        # Adulteración maliciosa: cambio de texto
        payload["explicacion_ciudadana"] = "MENSAJE ADULTERADO: Este texto fue modificado sin autorización."

        cursor.execute(
            "UPDATE incidents SET payload_json = ? WHERE id = ?",
            (json.dumps(payload), target_id)
        )
        conn.commit()
        conn.close()

        print(f"\n[!] ALERTA FORENSE: El registro {target_id} ha sido adulterado.")
        print("[*] Al consultar GET /api/verify-integrity, la cadena matemática debe romperse inmediatamente.\n")

    except Exception as e:
        print(f"[ERROR] No se pudo alterar la base de datos: {e}", file=sys.stderr)

if __name__ == "__main__":
    simulate_evidence_tampering()
```

---

## 10. Marco Legal y Cumplimiento Normativo (Backend)

| Disposición Jurídica | Obligación Legal | Implementación Técnica en Backend |
| :--- | :--- | :--- |
| **Ley 1581 de 2012** (Datos Personales) | Principio de minimización y consentimiento expreso. | No existen campos para nombres, números telefónicos o cédulas. La función de registro anonimiza irreversiblemente el payload y solo georreferencia por UPZ. |
| **Ley 1273 de 2009** (Protección de la Información) | Prohibición penal de interceptación de datos (Art. 269C). | Cero escucha pasiva. El backend únicamente procesa textos aportados de manera voluntaria y explícita por el usuario. |
| **Ley 527 de 1999 & ISO/IEC 27037** (Evidencia Digital) | Integridad, autenticidad y preservación de cadena de custodia. | Encadenamiento SHA-256 determinista en `integrity.py` con sellado de tiempo UTC que permite presentar la prueba pericial ante el CAI Virtual o Fiscalía. |
| **Circular Externa 002 de 2024 (SIC)** | Transparencia algorítmica sobre sistemas de IA. | Los esquemas devueltos por el backend obligan al frontend a renderizar la cláusula preventiva de orientación no sustitutiva de dictámenes oficiales. |

---

## 11. Guion de Ejecución del Pitch para el Backend (5 Minutos)

El backend soporta directamente los hitos técnicos de la sustentación:

* **Minuto 2 (Orquestación de Inferencia):** Diego monitorea la respuesta inmediata de `/api/analyze`. Si la conectividad de la universidad flaquea, la caché determinista devuelve la respuesta en $< 50\text{ ms}$ asegurando la fluidez del semáforo.
* **Minuto 3 (Auditoría Pericial en Vivo):**
  1. Erick muestra la llamada a `/api/verify-integrity` respondiendo `{"integro": true}`.
  2. Erick ejecuta en la terminal `python tests/test_tamper.py`.
  3. Se refresca la llamada o la interfaz y salta en pantalla: `{"integro": false, "registro_alterado": "ESC-2026-BOSA-0042", "motivo": "Alteración interna de contenido"}`.
* **Minuto 4 (Radar Territorial):** Daniel y Diego muestran el endpoint `/api/stats` cruzando los incidentes registrados con el histórico de `delitos_bosa_local.json`.
* **Minuto 5 (Cierre):** Sustentación del costo marginal \$0 (arquitectura ligera FastAPI + SQLite sin pagos recurrentes de infraestructura).

---

## 12. Puesta en Marcha Rápida (Quickstart Backend)

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 2. Instalar dependencias esenciales
pip install -r requirements.txt

# 3. Iniciar servidor ASGI en modo desarrollo
uvicorn app.main:app --reload --port 8000
```

* Swagger UI interactivo disponible en: `http://localhost:8000/docs`  
* Verificación de salud: `http://localhost:8000/api/campaigns/latest`