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

import ctypes

# Tiene que ejecutarse ANTES de importar pystray/webview: esos imports ya
# disparan la carga del runtime .NET (via pythonnet) que arma WinForms, y
# WinForms lee la metrica de DPI de la pantalla en ese momento. Declararlo
# despues (por ejemplo adentro de main()) llega tarde -- WinForms ya quedo
# con el contexto "no DPI-aware" y ni la ventana ni las cuentas de posicion
# en pantalla se corrigen aunque el resto del codigo este bien.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    pass

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

# webview.create_window(width=..., height=...) fija el tamano de la ventana
# COMPLETA (incluye borde + barra de titulo de Windows), no el area util
# donde se dibuja panel.html -- por eso se pide mas ancho/alto del que
# realmente necesita el contenido (336x560, ver panel.html), para que ese
# borde no le robe pixeles al contenido. panel.html en si ya no depende de
# que estos numeros sean exactos (usa width:100% en vez de un px fijo).
ANCHO_VENTANA = 336 + 24
ALTO_VENTANA = 560 + 40
MARGEN_BANDEJA = 8

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
        d = st.consultar().__dict__
        # No confundir con "ultimo_resultado" (Last Result crudo de
        # schtasks) -- ver docstring de ultimo_run_ok().
        d["ultima_corrida_ok"] = st.ultimo_run_ok()
        return d

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
    return icon_gen.salud_agregada(estados, st.ultimo_run_ok())


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
        _reposicionar_ventana()


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


class _RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

SPI_GETWORKAREA = 0x0030
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_NOSIZE = 0x0001


def _area_trabajo() -> _RECT:
    rect = _RECT()
    ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
    return rect


def _posicion_bandeja(ancho: int, alto: int) -> tuple[int, int]:
    """Primer calculo de posicion, para que la ventana no aparezca en el
    centro de la pantalla apenas se crea. Es una estimacion (todavia no
    existe la ventana real para medirla) -- _reposicionar_ventana() la
    corrige con el tamano real en cuanto se muestra."""
    area = _area_trabajo()
    x = area.right - ancho - MARGEN_BANDEJA
    y = area.bottom - alto - MARGEN_BANDEJA
    return max(x, 0), max(y, 0)


def _reposicionar_ventana() -> None:
    """Reubica la ventana contra su tamano REAL en pantalla (GetWindowRect),
    no el que se le pidio a create_window. Con DPI por monitor, la
    traduccion logico<->fisico que WinForms hace por dentro para
    Form.Location/Form.Size no siempre coincide con la que usan las APIs de
    pantalla (Screen.WorkingArea, o un calculo propio aparte) -- eso dejaba
    la ventana corrida hacia la izquierda pese a que la cuenta "en teoria"
    daba bien. GetWindowRect y SetWindowPos trabajan siempre en el mismo
    espacio de coordenadas que el resto de Windows, asi que autocorrige
    aunque el tamano real termine siendo distinto del pedido."""
    try:
        hwnd = ctypes.windll.user32.FindWindowW(None, "Panel de Control MCGHR")
        if not hwnd:
            return
        rect = _RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        ancho_real = rect.right - rect.left
        alto_real = rect.bottom - rect.top
        area = _area_trabajo()
        x = area.right - ancho_real - MARGEN_BANDEJA
        y = area.bottom - alto_real - MARGEN_BANDEJA
        ctypes.windll.user32.SetWindowPos(
            hwnd, 0, max(x, 0), max(y, 0), 0, 0,
            SWP_NOZORDER | SWP_NOACTIVATE | SWP_NOSIZE,
        )
    except Exception:
        pass


def main() -> None:
    global _window
    x, y = _posicion_bandeja(ANCHO_VENTANA, ALTO_VENTANA)
    _window = webview.create_window(
        "Panel de Control MCGHR",
        url=(HERE / "panel.html").as_uri(),
        js_api=PanelAPI(),
        width=ANCHO_VENTANA,
        height=ALTO_VENTANA,
        x=x,
        y=y,
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
