from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

UPZS = ["Bosa Central", "Bosa Occidental", "Tintal Sur", "El Porvenir"]
UPZLiteral = Literal["Bosa Central", "Bosa Occidental", "Tintal Sur", "El Porvenir"]


# ---------- Veredicto que debe devolver el LLM (Structured Outputs) ----------
class LLMVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nivel_riesgo: Literal["ALTO", "MEDIO", "BAJO"]
    color_semaforo: Literal["ROJO", "AMARILLO", "VERDE"]
    modalidad_detectada: str
    explicacion_ciudadana: str
    audio_guion: str
    recomendaciones: List[str]


# ---------- /api/analyze ----------
class AnalyzeRequest(BaseModel):
    texto: str = Field(min_length=1, max_length=2000)
    modo: Literal["voz", "texto"] = "texto"
    upz: Optional[UPZLiteral] = None


class EvidenciaCriptografica(BaseModel):
    hash_actual: str
    hash_anterior: str
    cadena_valida: bool
    qr_payload_url: str


class DatosAbiertosReferencia(BaseModel):
    fuente: str
    coincidencias_similares_mes: int


class AnalyzeResponse(BaseModel):
    id_analisis: str
    timestamp: str
    nivel_riesgo: str
    color_semaforo: str
    modalidad_detectada: str
    explicacion_ciudadana: str
    audio_guion: str
    recomendaciones: List[str]
    evidencia_criptografica: EvidenciaCriptografica
    datos_abiertos_referencia: DatosAbiertosReferencia


# ---------- /api/report ----------
class ReportRequest(BaseModel):
    payload: Dict[str, Any]
    upz: UPZLiteral


class ReportResponse(BaseModel):
    status: str
    hash: str
    id: str


# ---------- /api/verify-integrity ----------
class IntegrityResponse(BaseModel):
    integro: bool
    bloques_auditados: int
    registro_alterado: Optional[str] = None
    motivo: Optional[str] = None


# ---------- /api/campaigns/latest ----------
class CampaignResponse(BaseModel):
    alerta_activa: bool
    titulo: str
    modalidad: str


# ---------- /api/stats ----------
class StatsResponse(BaseModel):
    por_modalidad: Dict[str, int]
    por_upz: Dict[str, int]
    historico_bosa: Dict[str, int] = {}


# ---------- /api/analyze-image ----------
class ImageVerdict(BaseModel):
    """Veredicto estructurado que devuelve Gemini Vision al analizar un comprobante."""
    model_config = ConfigDict(extra="forbid")

    es_autentico: Literal["AUTENTICO", "SOSPECHOSO", "FALSO"]
    nivel_riesgo: Literal["ALTO", "MEDIO", "BAJO"]
    color_semaforo: Literal["ROJO", "AMARILLO", "VERDE"]
    entidad_detectada: str          # "Nequi", "Daviplata", "No identificada", …
    senales_detectadas: List[str]   # Máximo 4 señales encontradas
    url_qr_extraida: str            # URL del QR si hay uno; "" si no hay QR visible
    explicacion_ciudadana: str      # ≤ 25 palabras, español colombiano sencillo
    audio_guion: str                # ≤ 15 palabras, para leer en voz alta
    recomendaciones: List[str]      # Exactamente 2 acciones


class AnalyzeImageResponse(BaseModel):
    id_analisis: str
    timestamp: str
    es_autentico: str
    nivel_riesgo: str
    color_semaforo: str
    entidad_detectada: str
    senales_detectadas: List[str]
    url_qr_extraida: Optional[str]
    qr_dominio_legitimo: Optional[bool]  # None si no había QR
    explicacion_ciudadana: str
    audio_guion: str
    recomendaciones: List[str]
    evidencia_criptografica: EvidenciaCriptografica
    datos_abiertos_referencia: DatosAbiertosReferencia
