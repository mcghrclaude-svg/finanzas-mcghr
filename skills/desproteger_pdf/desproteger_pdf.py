"""
================================================================================
desproteger_pdf.py — Skill para remover contrasenas de archivos PDF
================================================================================
Version:  1.0
Autor:    Plataforma MCGHR — generado con Claude.ai Pro
Ubicacion: C:\\Users\\ghriz\\.claude\\skills\\desproteger_pdf\\desproteger_pdf.py

DESCRIPCION:
    Skill reutilizable para remover la proteccion por contrasena de archivos PDF.
    Soporta multiples contrasenas posibles — prueba cada una hasta encontrar
    la correcta. Si ninguna funciona, reporta el error claramente.

    Usa pikepdf (basado en QPDF) que soporta todos los tipos de encriptacion
    PDF modernos: RC4 40/128-bit y AES 128/256-bit.

    El archivo original nunca se modifica. El resultado se guarda con sufijo
    configurable (default: _sin_password) en la misma carpeta o en una
    carpeta destino especificada.

REQUISITOS:
    pip install pikepdf

USO COMO MODULO:
    from desproteger_pdf import desproteger_pdf, desproteger_lote

    # Un archivo, multiples contrasenas posibles
    resultado = desproteger_pdf(
        ruta_entrada="C:\\...\\extracto.pdf",
        contrasenas=["mi_cedula", "fecha_nacimiento", "1234"],
    )
    print(resultado)  # {"ok": True, "ruta_salida": "...", "contrasena_usada": "..."}

    # Lote de archivos
    resultados = desproteger_lote(
        carpeta="C:\\...\\Extractos\\",
        contrasenas=["pass1", "pass2"],
        patron="*.pdf"
    )

USO STANDALONE (desde terminal):
    python desproteger_pdf.py --entrada extracto.pdf --passwords "pass1,pass2"
    python desproteger_pdf.py --carpeta C:\\Extractos --passwords "pass1,pass2"
================================================================================
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

try:
    import pikepdf
except ImportError:
    print(
        "ERROR: pikepdf no instalado.\n"
        "Ejecutar: pip install pikepdf",
        file=sys.stderr
    )
    sys.exit(1)

log = logging.getLogger(__name__)


# ===========================================================================
# FUNCIONES PRINCIPALES
# ===========================================================================

def desproteger_pdf(
    ruta_entrada: str | Path,
    contrasenas: list[str],
    carpeta_salida: Optional[str | Path] = None,
    sufijo: str = "_sin_password",
    sobreescribir: bool = False,
) -> dict:
    """
    Remueve la contrasena de un PDF probando cada contrasena de la lista.

    Args:
        ruta_entrada:   Ruta completa al PDF protegido.
        contrasenas:    Lista de contrasenas a probar en orden.
        carpeta_salida: Carpeta donde guardar el resultado.
        sufijo:         Sufijo a agregar al nombre del archivo resultante.
        sobreescribir:  Si True, sobreescribe el archivo destino si existe.

    Returns:
        dict con ok, ruta_salida, contrasena_usada, tamano_bytes, mensaje.
    """
    entrada = Path(ruta_entrada)

    if not entrada.exists():
        return {
            "ok": False,
            "error": "archivo_no_encontrado",
            "mensaje": f"No se encontro el archivo: {entrada}"
        }

    if not entrada.suffix.lower() == ".pdf":
        return {
            "ok": False,
            "error": "no_es_pdf",
            "mensaje": f"El archivo no es un PDF: {entrada.name}"
        }

    carpeta = Path(carpeta_salida) if carpeta_salida else entrada.parent
    carpeta.mkdir(parents=True, exist_ok=True)

    nombre_salida = entrada.stem + sufijo + ".pdf"
    salida = carpeta / nombre_salida

    if salida.exists() and not sobreescribir:
        return {
            "ok": False,
            "error": "archivo_existe",
            "mensaje": f"Ya existe el archivo destino: {salida}. Usar sobreescribir=True para reemplazarlo."
        }

    contrasenas_a_probar = [""] + list(contrasenas)
    contrasena_exitosa = None

    for pwd in contrasenas_a_probar:
        try:
            with pikepdf.open(str(entrada), password=pwd) as pdf:
                pdf.save(str(salida))
                contrasena_exitosa = pwd if pwd != "" else None
                tamano = salida.stat().st_size

                if contrasena_exitosa is None:
                    mensaje = f"El PDF no tenia contrasena. Copiado a: {salida.name}"
                else:
                    mensaje = f"Contrasena correcta encontrada. Guardado en: {salida.name}"

                log.info(f"  OK: {entrada.name} -> {salida.name} ({tamano:,} bytes)")

                return {
                    "ok": True,
                    "ruta_salida": str(salida),
                    "contrasena_usada": contrasena_exitosa,
                    "tamano_bytes": tamano,
                    "mensaje": mensaje
                }

        except pikepdf.PasswordError:
            continue

        except pikepdf.PdfError as e:
            return {
                "ok": False,
                "error": "pdf_corrupto",
                "mensaje": f"El archivo PDF parece estar corrupto: {e}"
            }

        except Exception as e:
            return {
                "ok": False,
                "error": "error_inesperado",
                "mensaje": f"Error inesperado procesando {entrada.name}: {e}"
            }

    return {
        "ok": False,
        "error": "contrasena_incorrecta",
        "mensaje": (
            f"Ninguna de las {len(contrasenas)} contrasenas proporcionadas "
            f"pudo abrir el archivo: {entrada.name}"
        )
    }


def desproteger_lote(
    carpeta: str | Path,
    contrasenas: list[str],
    patron: str = "*.pdf",
    carpeta_salida: Optional[str | Path] = None,
    sufijo: str = "_sin_password",
    sobreescribir: bool = False,
) -> list[dict]:
    """
    Procesa todos los PDFs de una carpeta que coincidan con el patron.

    Args:
        carpeta:        Carpeta que contiene los PDFs a procesar.
        contrasenas:    Lista de contrasenas a probar para cada archivo.
        patron:         Patron glob para filtrar archivos.
        carpeta_salida: Carpeta destino.
        sufijo:         Sufijo del archivo resultante.
        sobreescribir:  Si True, sobreescribe archivos destino existentes.

    Returns:
        Lista de dicts, uno por archivo procesado.
    """
    carpeta = Path(carpeta)

    if not carpeta.exists():
        return [{
            "ok": False,
            "error": "carpeta_no_encontrada",
            "mensaje": f"No se encontro la carpeta: {carpeta}",
            "archivo": str(carpeta)
        }]

    archivos = [
        f for f in sorted(carpeta.glob(patron))
        if sufijo not in f.stem
        and f.suffix.lower() == ".pdf"
    ]

    if not archivos:
        return [{
            "ok": False,
            "error": "sin_archivos",
            "mensaje": f"No se encontraron PDFs en: {carpeta}",
            "archivo": str(carpeta)
        }]

    log.info(f"  Procesando {len(archivos)} archivos en {carpeta.name}/")

    resultados = []
    for archivo in archivos:
        resultado = desproteger_pdf(
            ruta_entrada=archivo,
            contrasenas=contrasenas,
            carpeta_salida=carpeta_salida,
            sufijo=sufijo,
            sobreescribir=sobreescribir,
        )
        resultado["archivo"] = archivo.name
        resultados.append(resultado)

    ok = sum(1 for r in resultados if r["ok"])
    errores = len(resultados) - ok
    log.info(f"  Lote completo: {ok} OK, {errores} errores de {len(resultados)} archivos")

    return resultados


# ===========================================================================
# MODO STANDALONE
# ===========================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(
        description="desproteger_pdf — Remover contrasena de PDFs"
    )

    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--entrada",  help="Ruta al PDF a desproteger")
    grupo.add_argument("--carpeta",  help="Carpeta con PDFs a desproteger en lote")

    parser.add_argument(
        "--passwords",
        required=True,
        help='Contrasenas separadas por coma. Ejemplo: "pass1,pass2,mi_cedula"'
    )
    parser.add_argument("--salida",      help="Carpeta destino (opcional)")
    parser.add_argument("--sufijo",      default="_sin_password")
    parser.add_argument("--sobreescribir", action="store_true")
    parser.add_argument("--patron",      default="*.pdf")

    args = parser.parse_args()
    contrasenas = [p.strip() for p in args.passwords.split(",") if p.strip()]

    if args.entrada:
        resultado = desproteger_pdf(
            ruta_entrada=args.entrada,
            contrasenas=contrasenas,
            carpeta_salida=args.salida,
            sufijo=args.sufijo,
            sobreescribir=args.sobreescribir,
        )
        if resultado["ok"]:
            print(f"OK: {resultado['mensaje']}")
            print(f"   Ruta: {resultado['ruta_salida']}")
            print(f"   Tamano: {resultado['tamano_bytes']:,} bytes")
        else:
            print(f"ERROR [{resultado['error']}]: {resultado['mensaje']}")
            sys.exit(1)
    else:
        resultados = desproteger_lote(
            carpeta=args.carpeta,
            contrasenas=contrasenas,
            patron=args.patron,
            carpeta_salida=args.salida,
            sufijo=args.sufijo,
            sobreescribir=args.sobreescribir,
        )
        print(f"\nResultados ({len(resultados)} archivos):\n")
        for r in resultados:
            if r["ok"]:
                print(f"  OK  {r['archivo']} -> {Path(r['ruta_salida']).name}")
            else:
                print(f"  ERR {r.get('archivo', '?')} — {r['mensaje']}")

        if any(not r["ok"] for r in resultados):
            sys.exit(1)
