"""
generar_datos_prueba.py -- Genera la data minima para correr correlacion.py
de forma aislada (sin depender de Gmail real), un escenario a la vez.

Cada escenario produce un JSON en staging/candidatos_escenario_<letra>.json
con la MISMA forma que produce extraccion.py (reutiliza la logica de
decision real via extraccion._procesar_correo, no la duplica). Los
escenarios que necesitan estado previo en la DB (ej. dos transacciones
existentes para forzar ambiguedad) lo insertan directamente.

Ver docs/ESCENARIOS_PRUEBA_ETL.md para el resultado esperado de cada uno.

Uso:
    python scripts/etl/generar_datos_prueba.py --escenario b
    python scripts/etl/generar_datos_prueba.py --escenario todos
"""

from __future__ import annotations

import argparse
import email
import json
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import DB_DEV_PATH, ID_PREFIJO_PIPELINE, REPO_ROOT, STAGING_DIR, conectar_db_dev  # noqa: E402
from extraccion import _procesar_correo  # noqa: E402

FIXTURE_EML = REPO_ROOT / "tests" / "fixtures" / "correos" / "bancolombia_gasto_ejemplo.eml"


def _correo(id_: str, remitente: str, asunto: str, snippet: str, texto_plano: str, fecha: datetime) -> SimpleNamespace:
    return SimpleNamespace(id=id_, remitente=remitente, asunto=asunto, snippet=snippet,
                            texto_plano=texto_plano, fecha=fecha)


def _guardar(letra: str, candidatos: list[dict]) -> Path:
    STAGING_DIR.mkdir(exist_ok=True)
    ruta = STAGING_DIR / f"candidatos_escenario_{letra}.json"
    ruta.write_text(json.dumps(candidatos, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[generar_datos_prueba] escenario {letra}: {ruta}")
    return ruta


# ------------------------------------------------------------------
# a) Correo de marketing puro -> se descarta
# ------------------------------------------------------------------

def escenario_a() -> None:
    correo = _correo(
        "test-a-remitente-marketing", "promociones@tiendagenerica.com",
        "Ofertas de la semana solo por hoy!",
        "Aprovecha nuestros descuentos exclusivos de esta semana en toda la tienda",
        "Aprovecha nuestros descuentos exclusivos de esta semana en toda la tienda. "
        "Sin montos especificos, solo promociones generales.",
        datetime(2026, 6, 10, 9, 0, tzinfo=timezone.utc),
    )
    candidato = _procesar_correo(correo, "hernan")
    assert candidato["descartable"] is True, "esperado: descartable=True"
    _guardar("a", [candidato])


# ------------------------------------------------------------------
# b) Correo de comercio con monto en el snippet (usa el fixture real)
# ------------------------------------------------------------------

def _leer_fixture_bancolombia() -> SimpleNamespace:
    msg = email.message_from_bytes(FIXTURE_EML.read_bytes())
    cuerpo = msg.get_payload()
    if isinstance(cuerpo, list):
        cuerpo = cuerpo[0].get_payload(decode=True).decode("utf-8", errors="replace")
    fecha = parsedate_to_datetime(msg["Date"])
    return _correo(
        "test-b-bancolombia-exito", msg["From"], msg["Subject"],
        cuerpo[:200], cuerpo, fecha,
    )


def escenario_b() -> None:
    correo = _leer_fixture_bancolombia()
    candidato = _procesar_correo(correo, "hernan")
    assert candidato["descartable"] is False, "esperado: descartable=False (monto en snippet)"
    assert candidato["necesito_lectura_completa"] is False, "esperado: monto ya estaba en el snippet"
    _guardar("b", [candidato])


# ------------------------------------------------------------------
# c) "Order Programada" -- monto no esta en el snippet, requiere regla B
# ------------------------------------------------------------------

def escenario_c() -> None:
    snippet = "Hola! Tu pedido fue programado exitosamente. Te avisaremos cuando este por llegar."
    cuerpo_completo = (
        snippet + " Total de tu pedido: $128.500. Direccion de entrega: Calle 10 #20-30, Bogota."
    )
    correo = _correo(
        "test-c-order-programada", "pedidos@tiendaonline.com", "Tu Order Programada esta en camino",
        snippet, cuerpo_completo, datetime(2026, 6, 12, 14, 0, tzinfo=timezone.utc),
    )
    candidato = _procesar_correo(correo, "hernan")
    assert candidato["descartable"] is False, "esperado: descartable=False (regla B encontro monto en el cuerpo)"
    assert candidato["necesito_lectura_completa"] is True, "esperado: necesito_lectura_completa=True"
    _guardar("c", [candidato])


# ------------------------------------------------------------------
# d) Correo de comercio + SMS reenviado que correlacionan
# ------------------------------------------------------------------

def escenario_d() -> None:
    correo_bancolombia = _correo(
        "test-d-bancolombia-rappi", "alertas@bancolombia.com.co",
        "Notificacion de Compra con Tarjeta de Credito",
        "Compra aprobada por $89.900 en RAPPI",
        "Compra aprobada por $89.900 en RAPPI\nTarjeta terminada en 5678\nFecha: 20/06/2026 13:15\nLugar: BOGOTA, CO",
        datetime(2026, 6, 20, 13, 15, tzinfo=timezone.utc),
    )
    correo_sms = _correo(
        "test-d-sms-891333", "ghrizzi.goog@gmail.com", "891333",
        "Bancolombia le informa Compra por $89.900 en RAPPI aprobada. Tarjeta *5678",
        "Bancolombia le informa Compra por $89.900 en RAPPI aprobada. Tarjeta *5678",
        datetime(2026, 6, 20, 13, 17, tzinfo=timezone.utc),
    )
    candidatos = [
        _procesar_correo(correo_bancolombia, "hernan"),
        _procesar_correo(correo_sms, "hernan"),
    ]
    _guardar("d", candidatos)
    print("[generar_datos_prueba]   NOTA: correlacion.py debe correrse una vez con este JSON completo "
          "(los dos correos en el mismo input) para que el segundo encuentre al primero.")


# ------------------------------------------------------------------
# e) Mismo message_id procesado dos veces -> dedup
# ------------------------------------------------------------------

def escenario_e() -> None:
    # Reusa el mismo candidato del escenario b. La prueba real es correr
    # correlacion.py DOS VECES sobre este mismo archivo (ver
    # docs/TESTING_PIPELINE_ETL.md) -- la segunda corrida no debe duplicar
    # la transaccion.
    correo = _leer_fixture_bancolombia()
    candidato = _procesar_correo(correo, "hernan")
    _guardar("e", [candidato])


# ------------------------------------------------------------------
# f) Contraparte que no existe en el catalogo -> entidad potencial
# ------------------------------------------------------------------

def escenario_f() -> None:
    correo = _correo(
        "test-f-tienda-nueva", "pagos@tiendanueva.co", "Compra aprobada",
        "Compra aprobada por $32.000 en TIENDA NUEVA XYZ",
        "Compra aprobada por $32.000 en TIENDA NUEVA XYZ\nTarjeta terminada en 9999\nFecha: 22/06/2026 10:00",
        datetime(2026, 6, 22, 10, 0, tzinfo=timezone.utc),
    )
    candidato = _procesar_correo(correo, "hernan")
    _guardar("f", [candidato])


# ------------------------------------------------------------------
# g) Dos candidatos de correlacion posibles -> ambiguos
# ------------------------------------------------------------------

def _sembrar_transacciones_ambiguas(db_path: str) -> None:
    conn = conectar_db_dev(db_path)
    ahora = datetime.now(timezone.utc).isoformat()
    for sufijo, fecha in (("seed-g1", "2026-06-25"), ("seed-g2", "2026-06-26")):
        tx_id = f"{ID_PREFIJO_PIPELINE}{sufijo}"
        conn.execute(
            """
            INSERT OR IGNORE INTO transacciones
                (id, fecha, tipo, descripcion, estado, confianza, revisado_humano,
                 completitud, quien_pago, fuente, origen, estado_enriquecimiento, creado_en, actualizado_en)
            VALUES (?, ?, 'gasto', 'Semilla escenario g -- posible duplicado', 'pendiente',
                    0.5, 0, 'minimo', 'GHR', 'gmail_hernan', 'email', 'inicial', ?, ?)
            """,
            (tx_id, fecha, ahora, ahora),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO tramos (id_transaccion, numero_orden, monto_origen, moneda_origen, estado)
            VALUES (?, 1, 150000, 'COP', 'pendiente')
            """,
            (tx_id,),
        )
    conn.commit()
    conn.close()
    print("[generar_datos_prueba]   Sembradas 2 transacciones existentes (25 y 26/06) por $150.000 COP -- GHR")


def escenario_g(db_path: str) -> None:
    _sembrar_transacciones_ambiguas(db_path)
    correo = _correo(
        "test-g-tercer-evento", "alertas@bancolombia.com.co", "Notificacion de Compra con Tarjeta de Credito",
        "Compra aprobada por $150.000 en ALGUN COMERCIO",
        "Compra aprobada por $150.000 en ALGUN COMERCIO\nTarjeta terminada en 1111\nFecha: 24/06/2026 11:00",
        datetime(2026, 6, 24, 11, 0, tzinfo=timezone.utc),
    )
    candidato = _procesar_correo(correo, "hernan")
    _guardar("g", [candidato])


ESCENARIOS = {
    "a": lambda db: escenario_a(),
    "b": lambda db: escenario_b(),
    "c": lambda db: escenario_c(),
    "d": lambda db: escenario_d(),
    "e": lambda db: escenario_e(),
    "f": lambda db: escenario_f(),
    "g": lambda db: escenario_g(db),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera datos de prueba para los escenarios del pipeline ETL")
    parser.add_argument("--escenario", default="todos", choices=list(ESCENARIOS) + ["todos"])
    parser.add_argument("--db", default=str(DB_DEV_PATH))
    args = parser.parse_args()

    letras = list(ESCENARIOS) if args.escenario == "todos" else [args.escenario]
    for letra in letras:
        ESCENARIOS[letra](args.db)
    return 0


if __name__ == "__main__":
    sys.exit(main())
