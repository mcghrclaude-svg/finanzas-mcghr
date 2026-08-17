"""
scheduled_task_service -- wrapper sobre schtasks.exe (nativo de Windows)
para controlar la corrida automatica de scripts/import_pwa_gastos.py.

La fuente de verdad del toggle encendido/apagado es la Tarea Programada
misma (Enabled/Disabled), no un flag en la DB -- el backend no corre 24/7,
asi que no puede ser el duenio del scheduling (ver CLAUDE.md).

Funciones sincronicas (subprocess bloqueante) -- el router las llama
con asyncio.to_thread para no bloquear el event loop.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

TASK_NAME = "FinanzasMCGHR_ImportPWA"
REPO_ROOT = Path(__file__).resolve().parents[2]
BAT_PATH = REPO_ROOT / "scripts" / "_run_import_pwa.bat"


@dataclass
class EstadoTarea:
    existe: bool
    habilitada: bool = False
    proxima_ejecucion: str | None = None
    ultimo_resultado: str | None = None


def _run_schtasks(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["schtasks", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def _comando_script(ambiente: str, carpetas: list[str]) -> str:
    """
    Task Scheduler NO hereda el directorio de trabajo del repo -- por defecto
    corre desde la carpeta del ejecutable (venv\\Scripts\\), no desde la raiz
    del repo, y "-m scripts.import_pwa_gastos" necesita el repo como cwd para
    resolver el paquete "scripts".

    Probado: pasar "cmd.exe /c "cd /d "X" && ..."" directo como /TR de schtasks
    NO funciona -- las comillas anidadas confunden el parser de schtasks, que
    termina ignorando el "cmd.exe /c" y guardando solo el comando de Python
    pelado (confirmado inspeccionando el XML de la tarea creada). En vez de
    pelear con el quoting de Windows, se escribe un .bat chico que hace el
    cd y corre el script, y /TR apunta directo a ese .bat (sin anidamiento).
    """
    partes_carpetas = " ".join(f'"{c}"' for c in carpetas)
    contenido_bat = (
        "@echo off\r\n"
        f'cd /d "{REPO_ROOT}"\r\n'
        f'"{sys.executable}" -m scripts.import_pwa_gastos '
        f'--ambiente {ambiente} --carpetas {partes_carpetas}\r\n'
    )
    BAT_PATH.write_text(contenido_bat, encoding="utf-8")
    return f'"{BAT_PATH}"'


def crear_o_actualizar(intervalo_minutos: int, ambiente: str, carpetas: list[str]) -> None:
    """Crea la tarea si no existe, o la reemplaza con la config nueva (schtasks
    no tiene un /Change que permita cambiar el comando ni el intervalo -- hay
    que recrearla)."""
    if consultar_estado().existe:
        eliminar()

    comando = _comando_script(ambiente, carpetas)
    resultado = _run_schtasks([
        "/Create", "/TN", TASK_NAME,
        "/TR", comando,
        "/SC", "MINUTE", "/MO", str(intervalo_minutos),
        "/RL", "LIMITED",
        "/F",  # sobreescribe si existiera
    ])
    if resultado.returncode != 0:
        raise RuntimeError(f"No se pudo crear la tarea programada: {resultado.stderr.strip()}")


def pausar() -> None:
    resultado = _run_schtasks(["/Change", "/TN", TASK_NAME, "/DISABLE"])
    if resultado.returncode != 0:
        raise RuntimeError(f"No se pudo pausar la tarea programada: {resultado.stderr.strip()}")


def reanudar() -> None:
    resultado = _run_schtasks(["/Change", "/TN", TASK_NAME, "/ENABLE"])
    if resultado.returncode != 0:
        raise RuntimeError(f"No se pudo reanudar la tarea programada: {resultado.stderr.strip()}")


def eliminar() -> None:
    _run_schtasks(["/Delete", "/TN", TASK_NAME, "/F"])


def consultar_estado() -> EstadoTarea:
    resultado = _run_schtasks(["/Query", "/TN", TASK_NAME, "/FO", "LIST", "/V"])
    if resultado.returncode != 0:
        return EstadoTarea(existe=False)

    campos: dict[str, str] = {}
    for linea in resultado.stdout.splitlines():
        if ":" in linea:
            clave, _, valor = linea.partition(":")
            campos[clave.strip()] = valor.strip()

    estado_raw = campos.get("Scheduled Task State", "")
    return EstadoTarea(
        existe=True,
        habilitada=(estado_raw.lower() == "enabled"),
        proxima_ejecucion=campos.get("Next Run Time") or None,
        ultimo_resultado=campos.get("Last Result") or None,
    )
