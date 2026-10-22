import os
from fastapi.testclient import TestClient
from app.main import app
from app.database import DATABASE_URL
from tests.test_tamper import simulate_evidence_tampering

DB = DATABASE_URL.replace("sqlite:///", "")


def test_flujo_completo():
    with TestClient(app) as c:
        # 1) analyze offline (sin llaves => caché determinista)
        r = c.post("/api/analyze", json={"texto": "Su cuenta Daviplata será embargada hoy. Entre a http://daviplata-embargos-bosa.cc", "modo": "texto", "upz": "Bosa Central"})
        assert r.status_code == 200
        d = r.json()
        assert d["color_semaforo"] == "ROJO" and d["evidencia_criptografica"]["hash_anterior"] == "0" * 64
        assert d["datos_abiertos_referencia"]["coincidencias_similares_mes"] == 28

        r2 = c.post("/api/analyze", json={"texto": "Alcaldía Local de Bosa invita al cabildo ciudadano. Entrada libre y gratuita"})
        assert r2.json()["color_semaforo"] == "VERDE"
        assert r2.json()["evidencia_criptografica"]["hash_anterior"] == d["evidencia_criptografica"]["hash_actual"]

        # 2) report: la PII no debe persistir
        rep = c.post("/api/report", json={"upz": "El Porvenir", "payload": {"nombre": "Juan", "cedula": "1012345678", "mensaje": "me escribieron al 3112223344 o a juan@mail.com"}})
        assert rep.json()["status"] == "registrado"
        import sqlite3
        raw = sqlite3.connect(DB).execute("SELECT payload_json FROM incidents WHERE id=?", (rep.json()["id"],)).fetchone()[0]
        for pii in ("Juan", "1012345678", "3112223344", "juan@mail.com"):
            assert pii not in raw

        # 3) cadena íntegra -> adulteración -> rota
        assert c.get("/api/verify-integrity").json()["integro"] is True
        victima = simulate_evidence_tampering(DB, d["id_analisis"])
        v = c.get("/api/verify-integrity").json()
        assert v["integro"] is False and v["registro_alterado"] == victima

        # 4) stats y campañas
        s = c.get("/api/stats").json()
        assert sum(s["por_upz"].values()) == 3
        assert "alerta_activa" in c.get("/api/campaigns/latest").json()


def test_upz_invalida():
    with TestClient(app) as c:
        assert c.post("/api/report", json={"payload": {}, "upz": "Kennedy"}).status_code == 422
