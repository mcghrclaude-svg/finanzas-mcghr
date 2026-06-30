"""
================================================================================
server.py -- Servidor MCP para lectura de correos Gmail
================================================================================
Version:  1.0
Autor:    Plataforma MCGHR -- generado con Claude.ai Pro
Ubicacion: C:\\Users\\ghriz\\.claude\\skills\\mcp_lector_correos\\server.py

DESCRIPCION:
    Servidor MCP que expone tres herramientas para que Claude Desktop pueda
    leer correos Gmail de multiples cuentas sin tener logica de negocio propia.

    Solo soporta Gmail via OAuth 2.0. Sin IMAP.

    El servidor arranca liviano (sin conectar a Gmail) y se conecta de forma
    lazy al primer llamado a cada herramienta. Esto permite tenerlo siempre
    registrado en claude_desktop_config.json sin overhead hasta que se usa.

HERRAMIENTAS:
    - buscar_correos   -- lista metadatos de correos que cumplen un criterio
    - leer_correo      -- obtiene texto completo y adjuntos de un correo
    - descargar_adjunto -- descarga un adjunto a disco

USO:
    python server.py --config C:\\...\\config_correos.json

REGISTRO EN claude_desktop_config.json:
    "mcp_lector_correos": {
      "command": "C:\\Users\\ghriz\\.claude\\Proyectos\\FinanzasFamilia\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\ghriz\\.claude\\skills\\mcp_lector_correos\\server.py",
        "--config",
        "C:\\Users\\ghriz\\.claude\\Proyectos\\FinanzasFamilia\\config_correos.json"
      ]
    }

DEPENDENCIAS:
    pip install mcp google-auth-oauthlib google-auth-httplib2 google-api-python-client

NOTAS:
    - Nunca marca correos como leidos
    - Todos los errores se retornan como JSON con campo "error" -- nunca
      se lanzan excepciones hacia el cliente MCP
    - Reintentos automaticos (3 intentos, backoff 2s/4s) solo para errores
      de red. Errores de autenticacion o configuracion fallan rapido.
================================================================================
"""

from __future__ import annotations

import argparse
import json
import logging
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Argparse primero -- antes de importar mcp, para que --help funcione rapido
# ---------------------------------------------------------------------------
_parser = argparse.ArgumentParser(
    description="mcp_lector_correos -- Servidor MCP de lectura de correos Gmail"
)
_parser.add_argument(
    "--config",
    required=True,
    help="Ruta al config_correos.json",
)
_args = _parser.parse_args()

# ---------------------------------------------------------------------------
# Cargar config y agregar skill_lector al path
# ---------------------------------------------------------------------------
_config_path = Path(_args.config)
if not _config_path.exists():
    print(f"ERROR: config no encontrado: {_config_path}", file=sys.stderr)
    sys.exit(1)

with open(_config_path, encoding="utf-8") as _f:
    CFG: dict = json.load(_f)

_skill_path = CFG.get("rutas", {}).get("skill_lector", "")
if _skill_path and Path(_skill_path).exists():
    sys.path.insert(0, str(_skill_path))
else:
    print(
        f"ERROR: ruta skill_lector no encontrada: {_skill_path!r}\n"
        "Verificar config_correos.json > rutas > skill_lector",
        file=sys.stderr,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Importar skill (despues de configurar el path)
# ---------------------------------------------------------------------------
try:
    from lector_correos import GmailBackend, Adjunto  # noqa: E402
except ImportError as _e:
    print(f"ERROR importando lector_correos: {_e}", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Importar FastMCP
# ---------------------------------------------------------------------------
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print(
        "ERROR: paquete 'mcp' no instalado.\n"
        "Ejecutar: pip install mcp",
        file=sys.stderr,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Logging -- stderr para no contaminar el canal stdio del protocolo MCP
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("mcp_lector_correos")

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
MAX_RESULTADOS_TECHO = 200
MAX_RESULTADOS_DEFAULT = 50
REINTENTOS = 3
BACKOFF_SEGUNDOS = [2, 4]   # esperas entre reintento 1->2 y 2->3

_ERRORES_RED = (
    ConnectionResetError,
    ConnectionError,
    TimeoutError,
    OSError,
    socket.error,
)

# ---------------------------------------------------------------------------
# Cache de backends -- uno por cuenta, creado de forma lazy
# ---------------------------------------------------------------------------
_backends: dict[str, GmailBackend] = {}


def _config_cuenta(nombre: str) -> Optional[dict]:
    """Retorna el dict de configuracion para GmailBackend, o None si no existe."""
    cuentas = CFG.get("cuentas_gmail", {})
    if nombre not in cuentas:
        return None
    datos = cuentas[nombre]
    if not datos.get("activa", True):
        return None
    rutas = CFG.get("rutas", {})
    return {
        "tipo":             "gmail",
        "nombre":           nombre,
        "email":            datos["email"],
        "credentials_file": rutas.get("credentials_gmail", ""),
        "tokens_dir":       rutas.get("tokens_gmail", ""),
    }


def _obtener_backend(nombre: str) -> tuple[Optional[GmailBackend], Optional[str]]:
    """
    Retorna (backend, None) si la cuenta existe y esta activa.
    Retorna (None, mensaje_error) si no.
    Crea el backend de forma lazy (sin conectar a Gmail todavia).
    """
    if nombre in _backends:
        return _backends[nombre], None

    cfg = _config_cuenta(nombre)
    if cfg is None:
        cuentas_validas = [
            k for k, v in CFG.get("cuentas_gmail", {}).items()
            if v.get("activa", True)
        ]
        return None, (
            f"Cuenta '{nombre}' no encontrada o inactiva. "
            f"Cuentas disponibles: {cuentas_validas}"
        )

    try:
        backend = GmailBackend(cfg)
        _backends[nombre] = backend
        return backend, None
    except Exception as e:
        return None, f"Error creando backend para '{nombre}': {e}"


def _con_reintento(fn, *args, **kwargs):
    """
    Ejecuta fn(*args, **kwargs) con hasta REINTENTOS intentos.
    Solo reintenta en errores de red. Otros errores se propagan inmediatamente.
    """
    ultimo_error = None
    for intento in range(REINTENTOS):
        try:
            return fn(*args, **kwargs)
        except _ERRORES_RED as e:
            ultimo_error = e
            if intento < REINTENTOS - 1:
                espera = BACKOFF_SEGUNDOS[min(intento, len(BACKOFF_SEGUNDOS) - 1)]
                log.warning(
                    f"Error de red (intento {intento + 1}/{REINTENTOS}): {e}. "
                    f"Reintentando en {espera}s..."
                )
                time.sleep(espera)
            else:
                log.error(f"Fallo tras {REINTENTOS} intentos: {e}")
        except Exception:
            raise   # Errores no-red se propagan sin reintento
    raise ultimo_error


def _err(codigo: str, mensaje: str, **extra) -> str:
    """Serializa un error como JSON."""
    return json.dumps({"error": codigo, "mensaje": mensaje, **extra}, ensure_ascii=False)


def _parsear_fecha_param(valor: Optional[str], nombre_param: str) -> tuple[Optional[datetime], Optional[str]]:
    """Parsea un string 'YYYY-MM-DD' a datetime UTC. Retorna (dt, None) o (None, error)."""
    if valor is None:
        return None, None
    try:
        dt = datetime.strptime(valor[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return dt, None
    except ValueError:
        return None, f"Formato invalido para {nombre_param}: '{valor}'. Usar YYYY-MM-DD."


# ===========================================================================
# Servidor MCP
# ===========================================================================

mcp = FastMCP("mcp_lector_correos")


# ---------------------------------------------------------------------------
# Herramienta 1: buscar_correos
# ---------------------------------------------------------------------------

@mcp.tool()
def buscar_correos(
    cuenta: str,
    query: str = "",
    dias: int = 7,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    max_resultados: int = MAX_RESULTADOS_DEFAULT,
) -> str:
    """
    Lista correos de una cuenta Gmail que cumplen un criterio de busqueda.
    Retorna solo metadatos (no el texto completo ni datos binarios de adjuntos).
    Usar leer_correo para obtener el contenido completo de un correo especifico.
    Nunca marca correos como leidos.

    Args:
        cuenta:          Nombre de cuenta Gmail: 'hernan', 'malu' o 'claude'.
        query:           Criterio de busqueda en sintaxis Gmail.
                         Ejemplos: 'from:alertas@bancolombia.com.co',
                         'subject:extracto', 'from:rappi has:attachment'.
                         String vacio retorna todos los correos del periodo.
        dias:            Dias hacia atras desde hoy. Ignorado si fecha_desde esta presente.
        fecha_desde:     Fecha de inicio en formato YYYY-MM-DD. Anula 'dias'.
        fecha_hasta:     Fecha de fin en formato YYYY-MM-DD. None significa hoy.
        max_resultados:  Maximo de correos a retornar. Techo absoluto: 200.
                         Si hay mas, el campo 'truncado' sera true.

    Returns:
        JSON con campos:
        - cuenta (str): nombre de la cuenta consultada
        - total_encontrados (int): total real de correos que cumplen el criterio
        - retornados (int): cuantos se incluyen en esta respuesta
        - truncado (bool): true si hay mas correos que max_resultados
        - correos (list): lista de objetos con id, asunto, remitente, fecha,
          snippet, tiene_adjuntos, nombres_adjuntos
        En caso de error: {"error": "...", "mensaje": "..."}
    """
    # Validar cuenta
    backend, error_cuenta = _obtener_backend(cuenta)
    if error_cuenta:
        return _err("cuenta_no_encontrada", error_cuenta)

    # Validar fechas
    dt_desde, err = _parsear_fecha_param(fecha_desde, "fecha_desde")
    if err:
        return _err("parametro_invalido", err)
    dt_hasta, err = _parsear_fecha_param(fecha_hasta, "fecha_hasta")
    if err:
        return _err("parametro_invalido", err)

    # Aplicar techo
    max_resultados = max(1, min(max_resultados, MAX_RESULTADOS_TECHO))

    try:
        # Paso 1: obtener IDs (sin descargar cuerpos)
        def _buscar():
            backend.conectar()
            fecha_base = dt_desde
            if fecha_base is None:
                from datetime import timedelta
                fecha_base = datetime.now(timezone.utc) - timedelta(days=dias)
            return backend.buscar_ids(query, fecha_base, dt_hasta)

        ids = _con_reintento(_buscar)

        total_encontrados = len(ids)
        truncado = total_encontrados > max_resultados
        ids_a_procesar = ids[:max_resultados]

        # Paso 2: para cada ID, obtener solo metadatos livianos
        # Usamos format="metadata" para no descargar el cuerpo completo
        correos_resultado = []
        for id_msg in ids_a_procesar:
            try:
                def _get_meta(mid=id_msg):
                    msg = backend._service.users().messages().get(
                        userId="me", id=mid, format="metadata",
                        metadataHeaders=["Subject", "From", "To", "Date"]
                    ).execute()
                    return msg

                msg = _con_reintento(_get_meta)

                headers = {
                    h["name"].lower(): h["value"]
                    for h in msg["payload"].get("headers", [])
                }

                # Detectar adjuntos sin descargarlos
                partes = msg["payload"].get("parts", [])
                nombres_adjuntos = [
                    p.get("filename", "")
                    for p in partes
                    if p.get("filename", "")
                ]
                tiene_adjuntos = len(nombres_adjuntos) > 0

                # Parsear fecha del header
                from lector_correos import _decodificar_header, _parsear_fecha
                fecha_str = ""
                try:
                    dt = _parsear_fecha(headers.get("date", ""))
                    fecha_str = dt.strftime("%Y-%m-%d")
                except Exception:
                    fecha_str = ""

                correos_resultado.append({
                    "id":               id_msg,
                    "asunto":           _decodificar_header(headers.get("subject", "(sin asunto)")),
                    "remitente":        headers.get("from", ""),
                    "fecha":            fecha_str,
                    "snippet":          msg.get("snippet", ""),
                    "tiene_adjuntos":   tiene_adjuntos,
                    "nombres_adjuntos": nombres_adjuntos,
                })

            except Exception as e:
                log.warning(f"  Error obteniendo metadatos de {id_msg}: {e}")
                # Se omite este correo del resultado pero no se falla todo

        return json.dumps({
            "cuenta":            cuenta,
            "total_encontrados": total_encontrados,
            "retornados":        len(correos_resultado),
            "truncado":          truncado,
            "correos":           correos_resultado,
        }, ensure_ascii=False)

    except _ERRORES_RED as e:
        return _err("error_red", f"Error de conectividad tras {REINTENTOS} intentos: {e}")
    except Exception as e:
        log.exception(f"buscar_correos: error inesperado para cuenta '{cuenta}'")
        return _err("error_interno", str(e))


# ---------------------------------------------------------------------------
# Herramienta 2: leer_correo
# ---------------------------------------------------------------------------

@mcp.tool()
def leer_correo(
    cuenta: str,
    id_correo: str,
) -> str:
    """
    Obtiene el contenido completo de un correo especifico: texto plano y
    metadatos de adjuntos (nombre, tipo MIME, tamano). No descarga datos
    binarios de adjuntos -- usar descargar_adjunto para eso.
    Nunca marca el correo como leido.

    Args:
        cuenta:    Nombre de cuenta Gmail: 'hernan', 'malu' o 'claude'.
        id_correo: ID del correo tal como fue retornado por buscar_correos.

    Returns:
        JSON con campos: id, asunto, remitente, destinatario, fecha,
        cuenta_nombre, cuenta_email, texto_plano, adjuntos (lista de
        {nombre, tipo_mime, tamano_bytes}).
        En caso de error: {"error": "...", "mensaje": "..."}
    """
    backend, error_cuenta = _obtener_backend(cuenta)
    if error_cuenta:
        return _err("cuenta_no_encontrada", error_cuenta)

    if not id_correo or not id_correo.strip():
        return _err("parametro_invalido", "id_correo no puede estar vacio")

    try:
        def _obtener():
            backend.conectar()
            # incluir_adjuntos=True para obtener metadatos de adjuntos,
            # pero el servidor NO retorna los bytes -- los descarta.
            return backend.obtener_correo(id_correo.strip(), incluir_adjuntos=True)

        correo = _con_reintento(_obtener)

        if correo is None:
            return _err("correo_no_encontrado", f"No se encontro el correo con id '{id_correo}'")

        # Serializar adjuntos sin incluir los bytes (campo .datos)
        adjuntos_meta = [
            {
                "nombre":       a.nombre,
                "tipo_mime":    a.tipo_mime,
                "tamano_bytes": a.tamaño_bytes,
            }
            for a in correo.adjuntos
        ]

        return json.dumps({
            "id":            correo.id,
            "asunto":        correo.asunto,
            "remitente":     correo.remitente,
            "destinatario":  correo.destinatario,
            "fecha":         correo.fecha_str,
            "cuenta_nombre": correo.cuenta_nombre,
            "cuenta_email":  correo.cuenta_email,
            "texto_plano":   correo.texto_plano,
            "adjuntos":      adjuntos_meta,
        }, ensure_ascii=False)

    except _ERRORES_RED as e:
        return _err("error_red", f"Error de conectividad tras {REINTENTOS} intentos: {e}")
    except Exception as e:
        log.exception(f"leer_correo: error inesperado para cuenta '{cuenta}', id '{id_correo}'")
        return _err("error_interno", str(e))


# ---------------------------------------------------------------------------
# Herramienta 3: descargar_adjunto
# ---------------------------------------------------------------------------

@mcp.tool()
def descargar_adjunto(
    cuenta: str,
    id_correo: str,
    nombre_adjunto: str,
    carpeta_destino: str,
    nombre_archivo_destino: Optional[str] = None,
) -> str:
    """
    Descarga un adjunto de un correo Gmail y lo guarda en disco.
    Crea la carpeta de destino si no existe. Sobreescribe si ya existe el archivo.

    Args:
        cuenta:                 Nombre de cuenta Gmail: 'hernan', 'malu' o 'claude'.
        id_correo:              ID del correo (de buscar_correos o leer_correo).
        nombre_adjunto:         Nombre exacto del adjunto tal como aparece en
                                leer_correo > adjuntos > nombre.
        carpeta_destino:        Ruta completa de la carpeta donde guardar el archivo.
                                Ejemplos:
                                'C:\\Users\\ghriz\\OneDrive\\Finanzas MCGHR\\Generales\\Stage'
                                'C:\\Users\\ghriz\\OneDrive\\Finanzas MCGHR\\GHR\\Extractos\\Bancolombia\\TarjetaCredito'
        nombre_archivo_destino: Nombre con el que se grabara el archivo. Opcional.
                                Si se omite, se usa el nombre original del adjunto.

    Returns:
        JSON con campos: ok (bool), ruta_guardado, nombre, tamano_bytes.
        En caso de error: {"ok": false, "error": "...", "mensaje": "..."}
    """
    backend, error_cuenta = _obtener_backend(cuenta)
    if error_cuenta:
        return json.dumps({"ok": False, "error": "cuenta_no_encontrada", "mensaje": error_cuenta})

    # Validar parametros obligatorios
    for param, valor in [
        ("id_correo", id_correo),
        ("nombre_adjunto", nombre_adjunto),
        ("carpeta_destino", carpeta_destino),
    ]:
        if not valor or not str(valor).strip():
            return json.dumps({
                "ok": False,
                "error": "parametro_invalido",
                "mensaje": f"'{param}' no puede estar vacio",
            })

    nombre_final = (nombre_archivo_destino or nombre_adjunto).strip()
    carpeta = Path(carpeta_destino.strip())
    ruta_final = carpeta / nombre_final

    try:
        # Obtener el correo completo con adjuntos (incluye bytes)
        def _obtener():
            backend.conectar()
            return backend.obtener_correo(id_correo.strip(), incluir_adjuntos=True)

        correo = _con_reintento(_obtener)

        if correo is None:
            return json.dumps({
                "ok": False,
                "error": "correo_no_encontrado",
                "mensaje": f"No se encontro el correo con id '{id_correo}'",
            })

        # Buscar el adjunto por nombre
        adjunto_encontrado: Optional[Adjunto] = None
        for a in correo.adjuntos:
            if a.nombre == nombre_adjunto:
                adjunto_encontrado = a
                break

        if adjunto_encontrado is None:
            nombres_disponibles = [a.nombre for a in correo.adjuntos]
            return json.dumps({
                "ok": False,
                "error": "adjunto_no_encontrado",
                "mensaje": (
                    f"No se encontro adjunto '{nombre_adjunto}' en el correo '{id_correo}'. "
                    f"Adjuntos disponibles: {nombres_disponibles}"
                ),
            })

        # Guardar en disco
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta_final.write_bytes(adjunto_encontrado.datos)

        log.info(f"  Adjunto guardado: {ruta_final} ({adjunto_encontrado.tamaño_bytes:,} bytes)")

        return json.dumps({
            "ok":            True,
            "ruta_guardado": str(ruta_final),
            "nombre":        nombre_final,
            "tamano_bytes":  adjunto_encontrado.tamaño_bytes,
        }, ensure_ascii=False)

    except PermissionError as e:
        return json.dumps({
            "ok": False,
            "error": "permiso_denegado",
            "mensaje": f"Sin permiso para escribir en '{carpeta_destino}': {e}",
        })
    except _ERRORES_RED as e:
        return json.dumps({
            "ok": False,
            "error": "error_red",
            "mensaje": f"Error de conectividad tras {REINTENTOS} intentos: {e}",
        })
    except Exception as e:
        log.exception(f"descargar_adjunto: error inesperado")
        return json.dumps({
            "ok": False,
            "error": "error_interno",
            "mensaje": str(e),
        })


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    log.info("mcp_lector_correos arrancando (transporte: stdio)")
    log.info(f"Config: {_config_path}")
    cuentas_activas = [
        k for k, v in CFG.get("cuentas_gmail", {}).items()
        if v.get("activa", True)
    ]
    log.info(f"Cuentas Gmail activas: {cuentas_activas}")
    log.info("Conexion a Gmail es lazy -- se conecta al primer llamado por cuenta")
    mcp.run(transport="stdio")
