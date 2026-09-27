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
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape as _xml_escape

TASK_NAME = "FinanzasMCGHR_ImportPWA"
REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHONW_PATH = Path(sys.executable).with_name("pythonw.exe")


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


def _task_xml(intervalo_minutos: int, ambiente: str, carpetas: list[str]) -> str:
    """
    Genera la definicion de la tarea como XML de Task Scheduler en vez de
    usar /TR + /SC + /MO de schtasks con un .bat intermedio.

    Motivo: Task Scheduler NO hereda el directorio de trabajo del repo --
    por defecto corre desde la carpeta del ejecutable indicado en /TR, y
    "-m scripts.import_pwa_gastos" necesita el repo como cwd para resolver
    el paquete "scripts". La version anterior resolvia esto con un .bat
    chico que hacia "cd /d" y llamaba a python.exe -- pero tanto cmd.exe
    (para interpretar el .bat) como python.exe (subsistema de consola)
    hacen parpadear una ventana cada vez que corre la tarea.

    El elemento <WorkingDirectory> del XML de Task Scheduler cubre el cwd
    de forma nativa (lo mismo que el campo "Iniciar en" de la UI), y
    apuntando /TR directo a pythonw.exe (subsistema GUI, sin consola,
    ya presente en el venv junto a python.exe) se elimina cmd.exe del medio
    -- cero ventanas, sin necesidad de un script intermedio persistido.

    A diferencia del .bat (que se re-ejecutaba en cada corrida), este XML
    solo se lee una vez al crear la tarea -- se genera en un archivo
    temporal descartable, no en el repo.
    """
    partes_carpetas = " ".join(f'"{c}"' for c in carpetas)
    argumentos = (
        f"-m scripts.import_pwa_gastos --ambiente {ambiente} --carpetas {partes_carpetas}"
    )
    inicio = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    return f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Importa gastos de la PWA mobile a la DB de escritorio (ambiente: {_xml_escape(ambiente)}).</Description>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <StartBoundary>{inicio}</StartBoundary>
      <Repetition>
        <Interval>PT{int(intervalo_minutos)}M</Interval>
      </Repetition>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>true</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>false</StartWhenAvailable>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <ExecutionTimeLimit>PT5M</ExecutionTimeLimit>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{_xml_escape(str(PYTHONW_PATH))}</Command>
      <Arguments>{_xml_escape(argumentos)}</Arguments>
      <WorkingDirectory>{_xml_escape(str(REPO_ROOT))}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
'''


def crear_o_actualizar(intervalo_minutos: int, ambiente: str, carpetas: list[str]) -> None:
    """Crea la tarea si no existe, o la reemplaza con la config nueva (schtasks
    no tiene un /Change que permita cambiar el comando ni el intervalo -- hay
    que recrearla)."""
    if consultar_estado().existe:
        eliminar()

    xml = _task_xml(intervalo_minutos, ambiente, carpetas)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".xml", encoding="utf-16", delete=False
    ) as f:
        f.write(xml)
        xml_path = f.name

    try:
        resultado = _run_schtasks(["/Create", "/TN", TASK_NAME, "/XML", xml_path, "/F"])
    finally:
        Path(xml_path).unlink(missing_ok=True)

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
