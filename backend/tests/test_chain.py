import integrity as I


def _cadena(n=3):
    recs, prev = [], I.GENESIS_HASH
    for i in range(n):
        p = {"k": i}
        rid, ts = f"R{i}", f"2026-10-22T10:0{i}:00Z"
        cur = I.generate_record_hash(rid, ts, I.calculate_payload_hash(p), prev)
        recs.append({"id": rid, "timestamp": ts, "payload": p, "previous_hash": prev, "current_hash": cur})
        prev = cur
    return recs


def test_vacia():
    assert I.verify_chain([])["integro"] is True


def test_valida():
    r = I.verify_chain(_cadena())
    assert r["integro"] and r["bloques_auditados"] == 3


def test_payload_alterado():
    c = _cadena(); c[1]["payload"]["k"] = 99
    r = I.verify_chain(c)
    assert not r["integro"] and r["registro_alterado"] == "R1"


def test_puntero_roto():
    c = _cadena(); c[2]["previous_hash"] = "f" * 64
    assert I.verify_chain(c)["registro_alterado"] == "R2"


def test_hash_determinista_sin_importar_orden():
    assert I.calculate_payload_hash({"a": 1, "b": 2}) == I.calculate_payload_hash({"b": 2, "a": 1})


def test_genesis():
    assert _cadena(1)[0]["previous_hash"] == "0" * 64
