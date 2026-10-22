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
