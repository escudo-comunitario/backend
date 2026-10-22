import json
import sqlite3
import sys


def simulate_evidence_tampering(db_path="escudo.db", target_id="ESC-2026-BOSA-0042"):
    """
    Modifica silenciosamente un solo payload de SQLite para demostrar que el recálculo
    SHA-256 en /api/verify-integrity expone el fraude. Si target_id no existe, usa el último registro.
    """
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, payload_json FROM incidents WHERE id = ?", (target_id,))
        row = cur.fetchone()
        if not row:
            cur.execute("SELECT id, payload_json FROM incidents ORDER BY rowid DESC LIMIT 1")
            row = cur.fetchone()
        if not row:
            print("[!] No hay registros. Ejecute primero un análisis desde la app.")
            return None
        target_id, raw = row
        payload = json.loads(raw)
        payload["explicacion_ciudadana"] = "MENSAJE ADULTERADO: Este texto fue modificado sin autorización."
        cur.execute("UPDATE incidents SET payload_json = ? WHERE id = ?", (json.dumps(payload), target_id))
        conn.commit()
        conn.close()
        print(f"\n[!] ALERTA FORENSE: El registro {target_id} ha sido adulterado.")
        print("[*] Al consultar GET /api/verify-integrity, la cadena debe romperse.\n")
        return target_id
    except Exception as e:
        print(f"[ERROR] No se pudo alterar la base de datos: {e}", file=sys.stderr)


if __name__ == "__main__":
    simulate_evidence_tampering(target_id=sys.argv[1] if len(sys.argv) > 1 else "ESC-2026-BOSA-0042")
