"""
icon_gen -- genera el icono de la bandeja con Pillow, en vez de un .ico
estatico: el color de fondo refleja la salud agregada (mismo criterio de
colores que el panel -- verde/amarillo/gris, nunca la posicion de un toggle)
para que el problema se note sin abrir el panel.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

COLOR_OK = (31, 157, 99)
COLOR_WARN = (183, 121, 31)
COLOR_CRIT = (197, 48, 48)
COLOR_OFF = (138, 147, 166)

_COLORES = {"ok": COLOR_OK, "warn": COLOR_WARN, "crit": COLOR_CRIT, "off": COLOR_OFF}


def salud_agregada(estados_componentes: list[str], ultima_corrida_ok: bool | None) -> str:
    """estados_componentes: lista de 'ok'/'warn'/'off'/'n/a' de estado_todos().
    ultima_corrida_ok: True/False segun los errores registrados en la ultima
    fila de log_ejecuciones_mobile (no el "Last Result" crudo de Task
    Scheduler -- ese campo usa codigos como 267009/267011 para "corriendo
    ahora mismo" / "todavia no corrio" que no son errores reales y generaban
    falsos rojos). None si no hay corridas registradas todavia: no hay
    evidencia de fallo, no se marca critico.
    Prioridad: una tarea programada que fallo pesa mas que un servicio apagado
    a proposito (eso es normal, no es un problema)."""
    if ultima_corrida_ok is False:
        return "crit"
    if "warn" in estados_componentes:
        return "warn"
    if "ok" in estados_componentes:
        return "ok"
    return "off"


def generar(salud: str, size: int = 64) -> Image.Image:
    color = _COLORES.get(salud, COLOR_OFF)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margen = size // 16
    draw.rounded_rectangle(
        [margen, margen, size - margen, size - margen],
        radius=size // 4, fill=color,
    )
    try:
        fuente = ImageFont.truetype("segoeuib.ttf", size=int(size * 0.55))
    except OSError:
        fuente = ImageFont.load_default()
    texto = "M"
    bbox = draw.textbbox((0, 0), texto, font=fuente)
    ancho, alto = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - ancho) / 2 - bbox[0], (size - alto) / 2 - bbox[1]),
        texto, fill=(255, 255, 255, 255), font=fuente,
    )
    return img
