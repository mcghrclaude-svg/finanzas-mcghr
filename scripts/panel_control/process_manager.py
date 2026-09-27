"""
process_manager -- arranca, detiene, reinicia y healthchequea Backend/Ux/PWA
de Finanzas MCGHR en la PC, por entorno (dev/test/staging/prod).

Reemplaza iniciar_finanzas.ps1 / detener_finanzas.ps1: generaliza a los 4
entornos (los .ps1 solo cubrian dev), lee el puerto de .env.{entorno} en vez
de tenerlo hardcodeado, y agrega un healthcheck real (GET) en vez de mirar
solo si el PID existe -- un proceso puede seguir vivo y haber crasheado a
nivel aplicacion (ver conversacion de diseno del panel de control).

Vive en su propio venv liviano (scripts/panel_control/requirements.txt),
separado del venv del backend -- por eso no depende de pydantic-settings ni
de nada del paquete backend/, solo de stdlib.

Uso por CLI (para probar sin la UI del tray):
    python process_manager.py estado
    python process_manager.py iniciar backend dev
    python process_manager.py detener backend dev
    python process_manager.py reiniciar ux prod
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VENV_UVICORN = REPO_ROOT / "venv" / "Scripts" / "uvicorn.exe"
FRONTEND_DIR = REPO_ROOT / "frontend"
PWA_DIR = REPO_ROOT / "pwa-gastos"
LOGDIR = REPO_ROOT / "logs"
DESEADO_PATH = LOGDIR / "deseado.json"

# Orden de presentacion en el panel: Prod primero (pedido explicito).
ENTORNOS = ("prod", "dev", "staging", "test")
COMPONENTES = ("backend", "ux", "pwa")

CREATE_NO_WINDOW = 0x08000000
HEALTHCHECK_TIMEOUT = 1.5


def _npm_cmd() -> str:
    encontrado = shutil.which("npm.cmd") or shutil.which("npm")
    return encontrado or r"C:\Program Files\nodejs\npm.cmd"


def _leer_env(entorno: str) -> dict[str, str]:
    """Lee variables de .env.{entorno} a mano (sin pydantic-settings, venv propio)."""
    ruta = REPO_ROOT / f".env.{entorno}"
    valores: dict[str, str] = {}
    if not ruta.exists():
        return valores
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.split("#", 1)[0].strip()
        if not linea or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        valores[clave.strip()] = valor.strip()
    return valores


def puerto(entorno: str, componente: str) -> int | None:
    """Puerto real del componente, leido de .env.{entorno} -- nunca hardcodeado.
    PWA solo corre localmente en Dev (preview con `vite --host`); en los demas
    entornos es un link informativo a lo publicado en GitHub Pages, sin puerto
    ni proceso local que controlar."""
    if componente == "pwa":
        return 5173 if entorno == "dev" else None
    env = _leer_env(entorno)
    clave = "BACKEND_PORT" if componente == "backend" else "FRONTEND_PORT"
    valor = env.get(clave)
    return int(valor) if valor and valor.isdigit() else None


def _pid_file(componente: str, entorno: str) -> Path:
    return LOGDIR / f"{componente}_{entorno}.pid"


def _log_files(componente: str, entorno: str) -> tuple[Path, Path]:
    base = LOGDIR / f"{componente}_{entorno}"
    return base.with_suffix(".log"), base.with_suffix(".err.log")


def _pid_vivo(pid: int) -> bool:
    resultado = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
        capture_output=True, text=True, creationflags=CREATE_NO_WINDOW,
    )
    return str(pid) in resultado.stdout


def _leer_pid(componente: str, entorno: str) -> int | None:
    archivo = _pid_file(componente, entorno)
    if not archivo.exists():
        return None
    try:
        pid = int(archivo.read_text(encoding="utf-8").strip())
    except ValueError:
        return None
    return pid if _pid_vivo(pid) else None


def _healthcheck(componente: str, puerto_actual: int) -> tuple[str, str]:
    """Devuelve (salud, detalle). salud: 'ok' | 'warn' | 'off'."""
    path = "/health" if componente == "backend" else "/"
    url = f"http://localhost:{puerto_actual}{path}"
    try:
        with urllib.request.urlopen(url, timeout=HEALTHCHECK_TIMEOUT) as resp:
            if 200 <= resp.status < 400:
                return "ok", "OK"
            return "warn", f"responde con {resp.status}"
    except urllib.error.HTTPError as e:
        return "warn", f"responde con {e.code}"
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
        return "off", "apagado"


@dataclass
class EstadoComponente:
    entorno: str
    componente: str
    puerto: int | None
    salud: str  # "ok" | "warn" | "off" | "n/a" (PWA fuera de Dev)
    detalle: str
    pid: int | None = None


def estado(componente: str, entorno: str) -> EstadoComponente:
    p = puerto(entorno, componente)
    if p is None:
        return EstadoComponente(entorno, componente, None, "n/a", "publicado (sin proceso local)")

    pid = _leer_pid(componente, entorno)
    if pid is None:
        return EstadoComponente(entorno, componente, p, "off", "apagado", None)

    salud, detalle = _healthcheck(componente, p)
    if salud == "off":
        # El proceso (PID) sigue vivo pero no responde -- eso es peor que
        # "apagado": crasheo a nivel app. Lo mostramos como warn, no off,
        # para no confundirlo con "nunca se prendio".
        salud, detalle = "warn", f"no responde en :{p} (PID {pid})"
    else:
        detalle = f"{detalle} (PID {pid})" if salud == "ok" else detalle
    return EstadoComponente(entorno, componente, p, salud, detalle, pid)


def estado_todos() -> list[EstadoComponente]:
    return [
        estado(componente, entorno)
        for entorno in ENTORNOS
        for componente in COMPONENTES
    ]


def _iniciar_backend(entorno: str, p: int) -> int:
    LOGDIR.mkdir(exist_ok=True)
    out, err = _log_files("backend", entorno)
    args = [str(VENV_UVICORN), "backend.main:app", "--port", str(p)]
    if entorno == "dev":
        args.append("--reload")
    env = {**_os_environ(), "ENV_FILE": f".env.{entorno}"}
    with open(out, "ab") as f_out, open(err, "ab") as f_err:
        proc = subprocess.Popen(
            args, cwd=REPO_ROOT, env=env,
            stdout=f_out, stderr=f_err,
            creationflags=CREATE_NO_WINDOW,
        )
    return proc.pid


def _iniciar_ux(entorno: str) -> int:
    LOGDIR.mkdir(exist_ok=True)
    out, err = _log_files("ux", entorno)
    script = {"dev": "dev", "test": "dev:test", "staging": "dev:staging", "prod": "dev:prod"}[entorno]
    with open(out, "ab") as f_out, open(err, "ab") as f_err:
        proc = subprocess.Popen(
            ["cmd.exe", "/c", _npm_cmd(), "run", script],
            cwd=FRONTEND_DIR, stdout=f_out, stderr=f_err,
            creationflags=CREATE_NO_WINDOW,
        )
    return proc.pid


def _iniciar_pwa_dev() -> int:
    LOGDIR.mkdir(exist_ok=True)
    out, err = _log_files("pwa", "dev")
    with open(out, "ab") as f_out, open(err, "ab") as f_err:
        proc = subprocess.Popen(
            ["cmd.exe", "/c", _npm_cmd(), "run", "dev"],
            cwd=PWA_DIR, stdout=f_out, stderr=f_err,
            creationflags=CREATE_NO_WINDOW,
        )
    return proc.pid


def _os_environ() -> dict[str, str]:
    import os
    return dict(os.environ)


def _clave(componente: str, entorno: str) -> str:
    return f"{componente}_{entorno}"


def _leer_deseados() -> dict[str, bool]:
    if not DESEADO_PATH.exists():
        return {}
    try:
        return json.loads(DESEADO_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _marcar_deseado(componente: str, entorno: str, encendido: bool) -> None:
    """Registra si el usuario quiere este componente prendido, para poder
    restaurarlo despues de un reinicio de Windows (ver restaurar_deseados()).
    Es intencion, no estado real: un componente que sigue vivo despues de
    Stop no se marca 'deseado' otra vez -- Stop es siempre una decision
    explicita del usuario, no se revierte sola."""
    LOGDIR.mkdir(exist_ok=True)
    deseados = _leer_deseados()
    deseados[_clave(componente, entorno)] = encendido
    DESEADO_PATH.write_text(json.dumps(deseados, indent=2), encoding="utf-8")


def iniciar(componente: str, entorno: str) -> EstadoComponente:
    _marcar_deseado(componente, entorno, True)

    if _leer_pid(componente, entorno) is not None:
        return estado(componente, entorno)  # ya esta corriendo, no duplicar

    p = puerto(entorno, componente)
    if p is None:
        raise ValueError(f"{componente}/{entorno} no tiene proceso local que iniciar")

    if componente == "backend":
        pid = _iniciar_backend(entorno, p)
    elif componente == "ux":
        pid = _iniciar_ux(entorno)
    elif componente == "pwa" and entorno == "dev":
        pid = _iniciar_pwa_dev()
    else:
        raise ValueError(f"componente desconocido: {componente}")

    _pid_file(componente, entorno).write_text(str(pid), encoding="utf-8")
    time.sleep(1.5)  # margen chico antes de que el llamador pida estado()
    return estado(componente, entorno)


def detener(componente: str, entorno: str) -> EstadoComponente:
    _marcar_deseado(componente, entorno, False)

    pid = _leer_pid(componente, entorno)
    archivo = _pid_file(componente, entorno)
    if pid is not None:
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True, creationflags=CREATE_NO_WINDOW,
        )
    archivo.unlink(missing_ok=True)
    return estado(componente, entorno)


def reiniciar(componente: str, entorno: str) -> EstadoComponente:
    detener(componente, entorno)
    time.sleep(0.5)
    return iniciar(componente, entorno)


def restaurar_deseados() -> list[EstadoComponente]:
    """Vuelve a prender lo que estaba corriendo cuando se apago/reinicio
    Windows la ultima vez -- pensado para llamarse una vez al arrancar
    tray_app.py. Un componente detenido a mano (detener()) no se restaura
    solo porque la PC se reinicio; solo lo que seguia 'deseado=True'."""
    restaurados = []
    for clave, encendido in _leer_deseados().items():
        if not encendido:
            continue
        componente, _, entorno = clave.partition("_")
        if puerto(entorno, componente) is None:
            continue
        try:
            restaurados.append(iniciar(componente, entorno))
        except Exception:
            pass
    return restaurados


if __name__ == "__main__":
    accion = sys.argv[1] if len(sys.argv) > 1 else "estado"
    if accion == "estado":
        print(json.dumps([asdict(e) for e in estado_todos()], indent=2, ensure_ascii=False))
    elif accion in ("iniciar", "detener", "reiniciar"):
        _componente, _entorno = sys.argv[2], sys.argv[3]
        fn = {"iniciar": iniciar, "detener": detener, "reiniciar": reiniciar}[accion]
        print(json.dumps(asdict(fn(_componente, _entorno)), indent=2, ensure_ascii=False))
    elif accion == "restaurar":
        print(json.dumps([asdict(e) for e in restaurar_deseados()], indent=2, ensure_ascii=False))
    else:
        print(f"Accion desconocida: {accion}", file=sys.stderr)
        sys.exit(1)
