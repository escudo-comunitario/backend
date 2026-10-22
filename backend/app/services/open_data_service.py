import json
from pathlib import Path

_RUTA = Path(__file__).resolve().parent.parent / "data" / "delitos_bosa_local.json"
_DATA = json.loads(_RUTA.read_text(encoding="utf-8"))  # se precarga en memoria al importar

FUENTE = _DATA["fuente"]


def coincidencias_mes(modalidad: str) -> int:
    return int(_DATA["por_modalidad_mes"].get(modalidad, 0))


def historico_upz() -> dict:
    return dict(_DATA["por_upz_mes"])
