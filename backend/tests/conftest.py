"""
conftest.py local para el directorio tests/.

Añade un fixture que limpia la tabla de incidentes antes de cada test
que opere sobre la BD compartida (definida por el conftest.py raíz).
Esto garantiza que test_flujo_completo siempre parta de una cadena vacía,
independientemente del orden de ejecución de los tests.
"""
import pytest
from sqlalchemy import text


@pytest.fixture(autouse=True)
def limpiar_bd_entre_tests():
    """Vacía la tabla incidents antes de cada test para garantizar aislamiento."""
    from app.database import engine
    with engine.connect() as conn:
        # Ignora el error si la tabla aún no existe (tests de integridad pura)
        try:
            conn.execute(text("DELETE FROM incidents"))
            conn.commit()
        except Exception:
            pass
    yield
