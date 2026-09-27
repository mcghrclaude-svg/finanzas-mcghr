"""
scheduled_tasks -- estado de las Tareas Programadas de Windows para el panel
de control. Lee schtasks directo (mismo mecanismo que
backend/services/scheduled_task_service.py) para que el panel funcione
aunque el backend este apagado.

Para el historial de corridas NO se reinventa logging nuevo: la tabla
log_ejecuciones_mobile y su endpoint (GET /api/v1/pwa-config/historial) ya
existen (ver ADR y backend/api/v1/routers/pwa_config.py) -- aca se lee esa
misma tabla directo del archivo SQLite, sin pasar por el backend.

ADR-017: la tarea es global a la maquina (una sola para los 4 entornos), asi
que a que ambiente le pertenece la corrida actual no es un dato fijo -- se
lee de los argumentos reales con los que Task Scheduler tiene armada la
tarea ("--ambiente X" en el Command Line). Si todavia no se puede determinar
(por ejemplo, la tarea fue creada con la version vieja, basada en un .bat sin
argumentos visibles) se devuelve ambiente=None en vez de adivinar -- el panel
debe mostrar "sin datos" y no un ambiente incorrecto.
"""

from __future__ import annotations

import re
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path

from process_manager import CREATE_NO_WINDOW, REPO_ROOT, _leer_env

TASK_NAME = "FinanzasMCGHR_ImportPWA"


@dataclass
class EstadoTarea:
    existe: bool
    habilitada: bool = False
    ambiente: str | None = None
    proxima_ejecucion: str | None = None
    ultimo_resultado: str | None = None


def _run_schtasks(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["schtasks", *args], capture_output=True, text=True,
        timeout=15, creationflags=CREATE_NO_WINDOW,
    )


def consultar() -> EstadoTarea:
    resultado = _run_schtasks(["/Query", "/TN", TASK_NAME, "/FO", "LIST", "/V"])
    if resultado.returncode != 0:
        return EstadoTarea(existe=False)

    campos: dict[str, str] = {}
    for linea in resultado.stdout.splitlines():
        if ":" in linea:
            clave, _, valor = linea.partition(":")
            campos[clave.strip()] = valor.strip()

    tarea_a_correr = campos.get("Task To Run", "")
    m = re.search(r"--ambiente\s+(\w+)", tarea_a_correr)
    ambiente = m.group(1) if m else None

    estado_raw = campos.get("Scheduled Task State", "")
    return EstadoTarea(
        existe=True,
        habilitada=(estado_raw.lower() == "enabled"),
        ambiente=ambiente,
        proxima_ejecucion=campos.get("Next Run Time") or None,
        ultimo_resultado=campos.get("Last Result") or None,
    )


def pausar() -> None:
    resultado = _run_schtasks(["/Change", "/TN", TASK_NAME, "/DISABLE"])
    if resultado.returncode != 0:
        raise RuntimeError(f"No se pudo pausar la tarea programada: {resultado.stderr.strip()}")


def reanudar() -> None:
    resultado = _run_schtasks(["/Change", "/TN", TASK_NAME, "/ENABLE"])
    if resultado.returncode != 0:
        raise RuntimeError(f"No se pudo reanudar la tarea programada: {resultado.stderr.strip()}")


def _db_path(ambiente: str) -> Path | None:
    env = _leer_env(ambiente)
    db_path = env.get("DB_PATH")
    if not db_path or db_path == ":memory:":
        return None
    ruta = Path(db_path)
    if not ruta.is_absolute():
        ruta = REPO_ROOT / ruta
    return ruta if ruta.exists() else None


def historial(limit: int = 20) -> list[dict]:
    """Ultimas corridas, leidas directo de la DB del ambiente que la Tarea
    Programada tiene configurado ahora mismo. Lista vacia si no se puede
    determinar el ambiente o la tabla todavia no existe en esa DB."""
    est = consultar()
    if not est.existe or not est.ambiente:
        return []
    ruta = _db_path(est.ambiente)
    if ruta is None:
        return []

    con = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        filas = con.execute(
            "SELECT * FROM log_ejecuciones_mobile ORDER BY fecha_inicio DESC LIMIT ?",
            (limit,),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        con.close()
    return [dict(f) for f in filas]


def ultima_corrida() -> dict | None:
    filas = historial(limit=1)
    return filas[0] if filas else None


def ultimo_run_ok() -> bool | None:
    """True/False segun los errores de la ultima corrida real, leida de
    log_ejecuciones_mobile -- a diferencia de EstadoTarea.ultimo_resultado
    (el "Last Result" crudo de schtasks), esto no se confunde con los
    codigos pseudo-error que Task Scheduler usa para "corriendo ahora mismo"
    (267009) o "todavia no corrio" (267011). None si no hay corridas
    registradas todavia."""
    fila = ultima_corrida()
    if fila is None:
        return None
    return (fila.get("errores") or 0) == 0


if __name__ == "__main__":
    import json

    print(json.dumps({
        "estado": consultar().__dict__,
        "ultima_corrida": ultima_corrida(),
    }, indent=2, ensure_ascii=False))
