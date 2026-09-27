"""
tray_app -- icono de bandeja (pystray) + panel de control (pywebview) para
Finanzas MCGHR. Pensado para correr con pythonw.exe (sin consola) -- ver
scripts/panel_control/instalar_autostart.ps1 para el arranque automatico.

El panel arranca oculto: un clic (o doble clic) en el icono de la bandeja lo
muestra. Los datos que ve panel.html vienen de PanelAPI, que delega en
process_manager.py (Backend/Ux/PWA por entorno) y scheduled_tasks.py
(Tarea Programada de importacion de gastos de la PWA).
"""

from __future__ import annotations

import os
import threading
import time
import webbrowser
from pathlib import Path

import pystray
import webview

import icon_gen
import process_manager as pm
import scheduled_tasks as st

HERE = Path(__file__).resolve().parent
LINK_PWA_PUBLICADA = "https://mcghrclaude-svg.github.io/finanzas-mcghr/"

_window: webview.Window | None = None
_saliendo_de_verdad = False  # True solo durante _salir() -- distingue "cerrar de verdad" de la X de la ventana


class PanelAPI:
    def estado_todos(self):
        salida = []
        for e in pm.estado_todos():
            d = e.__dict__.copy()
            if e.componente == "pwa" and e.entorno != "dev":
                d["link_publicado"] = LINK_PWA_PUBLICADA
            salida.append(d)
        return salida

    def iniciar(self, componente: str, entorno: str):
        return pm.iniciar(componente, entorno).__dict__

    def detener(self, componente: str, entorno: str):
        return pm.detener(componente, entorno).__dict__

    def reiniciar(self, componente: str, entorno: str):
        return pm.reiniciar(componente, entorno).__dict__

    def tarea_estado(self):
        return st.consultar().__dict__

    def historial(self, limit: int = 20):
        return st.historial(limit=limit)

    def abrir_link(self, url: str):
        if url:
            webbrowser.open(url)

    def abrir_carpeta_logs(self):
        pm.LOGDIR.mkdir(exist_ok=True)
        os.startfile(pm.LOGDIR)  # type: ignore[attr-defined]


def _salud_agregada_actual() -> str:
    estados = [e.salud for e in pm.estado_todos()]
    tarea = st.consultar()
    return icon_gen.salud_agregada(estados, tarea.ultimo_resultado)


def _loop_icono(icon: pystray.Icon) -> None:
    while True:
        try:
            icon.icon = icon_gen.generar(_salud_agregada_actual())
        except Exception:
            pass
        time.sleep(15)


def _mostrar_panel(icon=None, item=None) -> None:
    if _window is not None:
        _window.show()


def _al_cerrar_ventana() -> bool | None:
    """Handler de window.events.closing: la X de la ventana solo la oculta,
    nunca mata el proceso -- el icono de la bandeja debe seguir disponible
    para volver a abrirla. Devolver False cancela el cierre real (ver
    webview/platforms/winforms.py: on_closing). Salir de verdad pasa por
    _salir(), que primero levanta _saliendo_de_verdad para no cancelarse
    a si mismo."""
    if _saliendo_de_verdad:
        return None
    if _window is not None:
        _window.hide()
    return False


def _salir(icon: pystray.Icon, item=None) -> None:
    global _saliendo_de_verdad
    _saliendo_de_verdad = True
    icon.stop()
    if _window is not None:
        _window.destroy()


def main() -> None:
    global _window
    _window = webview.create_window(
        "Panel de Control MCGHR",
        url=(HERE / "panel.html").as_uri(),
        js_api=PanelAPI(),
        width=336,
        height=560,
        resizable=False,
        hidden=True,
    )
    _window.events.closing += _al_cerrar_ventana

    icon = pystray.Icon(
        "finanzas_mcghr_panel",
        icon_gen.generar("off"),
        "Finanzas MCGHR",
        menu=pystray.Menu(
            pystray.MenuItem("Abrir panel", _mostrar_panel, default=True),
            pystray.MenuItem("Salir", _salir),
        ),
    )
    threading.Thread(target=icon.run, daemon=True).start()
    threading.Thread(target=_loop_icono, args=(icon,), daemon=True).start()
    # Restaura lo que estaba prendido antes del ultimo apagado/reinicio de
    # Windows. En background: arrancar varios componentes puede tardar unos
    # segundos y no debe demorar la aparicion del icono de la bandeja.
    threading.Thread(target=pm.restaurar_deseados, daemon=True).start()

    webview.start()


if __name__ == "__main__":
    main()
