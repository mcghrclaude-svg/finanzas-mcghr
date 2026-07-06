"""
================================================================================
lector_correos.py -- Skill generico de lectura de correos
================================================================================
Version:  1.0
Autor:    Plataforma MCGHR -- generado con Claude.ai Pro
Ubicacion: C:\\Users\\ghriz\\.claude\\skills\\lector_correos\\lector_correos.py

DESCRIPCION:
    Modulo Python reutilizable que abstrae la lectura de correos desde
    multiples proveedores (Gmail via OAuth, Outlook/Hotmail via IMAP).

    Disenado para ser IMPORTADO por otros scripts:
        from lector_correos import LectorCorreos

    No contiene logica de negocio ni filtros especificos de ningun proyecto.
    No marca correos como leidos. No modifica el estado de ningun buzon.

PROVEEDORES SOPORTADOS:
    - Gmail (OAuth 2.0 con credentials.json de Google Cloud)
    - Outlook / Hotmail (IMAP con contrasena de aplicacion Microsoft)

REQUISITOS:
    pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

USO BASICO:
    config = {
        "tipo": "gmail",
        "nombre": "hernan",
        "email": "ghrizzi.goog@gmail.com",
        "credentials_file": "C:\\...\\credentials.json",
        "tokens_dir": "C:\\...\\tokens"
    }
    lector = LectorCorreos(config)
    correos = lector.buscar(query="from:rappi", dias=7)
    for correo in correos:
        print(correo.asunto, correo.monto_detectado)

EXTENSIBILIDAD:
    Para agregar un nuevo proveedor (ej: Yahoo, iCloud):
    1. Crear clase YahooBackend(BaseBackend) en este mismo archivo
    2. Registrarla en BACKENDS al final del archivo
    Sin tocar el codigo existente.
================================================================================
"""

from __future__ import annotations

import base64
import email
import imaplib
import logging
import os
import re
import ssl
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.header import decode_header
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

# ---- Dependencias opcionales (Gmail) ------------------------------------------
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_DISPONIBLE = True
except ImportError:
    GMAIL_DISPONIBLE = False

log = logging.getLogger(__name__)

# ================================================================================
# MODELO DE DATOS
# ================================================================================

@dataclass
class Adjunto:
    """Representa un archivo adjunto de un correo."""
    nombre: str
    tipo_mime: str
    datos: bytes
    tamaño_bytes: int = 0

    def es_pdf(self) -> bool:
        return self.tipo_mime == "application/pdf" or self.nombre.lower().endswith(".pdf")

    def es_excel(self) -> bool:
        return self.tipo_mime in (
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ) or self.nombre.lower().endswith((".xls", ".xlsx"))

    def guardar(self, ruta: Path) -> Path:
        """Guarda el adjunto en disco. Retorna la ruta del archivo creado."""
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(self.datos)
        return ruta


@dataclass
class Correo:
    """Representa un correo electronico normalizado."""
    id: str
    asunto: str
    remitente: str
    destinatario: str
    fecha: datetime
    texto_plano: str
    snippet: str = ""
    adjuntos: list[Adjunto] = field(default_factory=list)
    cuenta_nombre: str = ""
    cuenta_email: str = ""
    proveedor: str = ""      # "gmail" | "imap"

    @property
    def fecha_str(self) -> str:
        return self.fecha.strftime("%Y-%m-%d")

    @property
    def texto_para_ia(self) -> str:
        """Texto optimizado para enviar a Claude API -- max 4000 chars."""
        return (
            f"ASUNTO: {self.asunto}\n"
            f"REMITENTE: {self.remitente}\n"
            f"FECHA: {self.fecha_str}\n"
            f"CONTENIDO: {self.texto_plano[:3500]}"
        )

    def tiene_adjuntos_financieros(self) -> bool:
        return any(a.es_pdf() or a.es_excel() for a in self.adjuntos)


# ================================================================================
# BACKENDS -- Uno por proveedor de correo
# ================================================================================

class BaseBackend(ABC):
    """Interfaz que todo backend de correo debe implementar."""

    def __init__(self, config: dict):
        self.config = config
        self.nombre = config.get("nombre", "desconocido")
        self.email = config.get("email", "")

    @abstractmethod
    def conectar(self) -> None:
        """Establece la conexion autenticada."""

    @abstractmethod
    def buscar_ids(self, query: str, fecha_desde: datetime,
                   fecha_hasta: Optional[datetime] = None) -> list[str]:
        """Retorna lista de IDs de mensajes que cumplen el criterio."""

    @abstractmethod
    def obtener_correo(self, id_mensaje: str,
                       incluir_adjuntos: bool = True) -> Optional[Correo]:
        """Obtiene el contenido completo de un mensaje por ID."""

    def buscar(self, query: str, dias: int = 7,
               fecha_desde: Optional[datetime] = None,
               fecha_hasta: Optional[datetime] = None,
               incluir_adjuntos: bool = True) -> list[Correo]:
        """
        Metodo principal. Busca correos y retorna objetos Correo completos.
        NUNCA modifica el estado de los mensajes (no marca como leido).

        Args:
            query:            Criterio de busqueda (sintaxis del proveedor)
            dias:             Dias hacia atras (ignorado si fecha_desde esta presente)
            fecha_desde:      Fecha de inicio explicita
            fecha_hasta:      Fecha de fin (None = ahora)
            incluir_adjuntos: Si True, descarga el contenido de los adjuntos
        """
        if fecha_desde is None:
            fecha_desde = datetime.now(timezone.utc) - timedelta(days=dias)

        self.conectar()
        ids = self.buscar_ids(query, fecha_desde, fecha_hasta)
        log.info(f"  [{self.nombre}] {len(ids)} mensajes encontrados con query: {query!r}")

        correos = []
        for id_msg in ids:
            try:
                correo = self.obtener_correo(id_msg, incluir_adjuntos)
                if correo:
                    correos.append(correo)
            except Exception as e:
                log.warning(f"  [{self.nombre}] Error obteniendo mensaje {id_msg}: {e}")

        return correos


# --------------------------------------------------------------------------------
# Backend Gmail
# --------------------------------------------------------------------------------

class GmailBackend(BaseBackend):
    """
    Backend para Gmail usando la Gmail API v1 con OAuth 2.0.
    Requiere credentials.json del proyecto Google Cloud.
    """

    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

    def __init__(self, config: dict):
        super().__init__(config)
        if not GMAIL_DISPONIBLE:
            raise ImportError(
                "Faltan dependencias de Gmail. Ejecuta:\n"
                "pip install google-auth-oauthlib google-auth-httplib2 "
                "google-api-python-client"
            )
        self._service = None
        self._credentials_file = config.get("credentials_file", "")
        self._tokens_dir = Path(config.get("tokens_dir", Path.home() / ".gmail-mcp" / "tokens"))

    def conectar(self) -> None:
        if self._service:
            return  # Ya conectado

        token_file = self._tokens_dir / f"{self.nombre}.json"
        self._tokens_dir.mkdir(parents=True, exist_ok=True)

        creds = None
        if token_file.exists():
            creds = Credentials.from_authorized_user_file(str(token_file), self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                log.info(f"  [{self.nombre}] Renovando token OAuth...")
                creds.refresh(Request())
            else:
                log.info(f"  [{self.nombre}] Iniciando flujo OAuth -- se abrira el browser")
                log.info(f"  [{self.nombre}] Inicia sesion con: {self.email}")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            token_file.write_text(creds.to_json())
            log.info(f"  [{self.nombre}] Token guardado en {token_file}")

        self._service = build("gmail", "v1", credentials=creds)

    def buscar_ids(self, query: str, fecha_desde: datetime,
                   fecha_hasta: Optional[datetime] = None) -> list[str]:
        q = f"{query} after:{fecha_desde.strftime('%Y/%m/%d')}"
        if fecha_hasta:
            q += f" before:{fecha_hasta.strftime('%Y/%m/%d')}"

        ids = []
        page_token = None
        while True:
            resp = self._service.users().messages().list(
                userId="me", q=q, maxResults=500, pageToken=page_token
            ).execute()
            ids.extend(m["id"] for m in resp.get("messages", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        return ids

    def obtener_correo(self, id_mensaje: str,
                       incluir_adjuntos: bool = True) -> Optional[Correo]:
        msg = self._service.users().messages().get(
            userId="me", id=id_mensaje, format="full"
        ).execute()

        headers = {h["name"].lower(): h["value"]
                   for h in msg["payload"].get("headers", [])}

        fecha = _parsear_fecha(headers.get("date", ""))
        texto, adjuntos = _extraer_contenido_gmail(
            self._service, id_mensaje, msg["payload"], incluir_adjuntos
        )

        return Correo(
            id=id_mensaje,
            asunto=_decodificar_header(headers.get("subject", "")),
            remitente=headers.get("from", ""),
            destinatario=headers.get("to", ""),
            fecha=fecha,
            texto_plano=texto,
            snippet=msg.get("snippet", ""),
            adjuntos=adjuntos,
            cuenta_nombre=self.nombre,
            cuenta_email=self.email,
            proveedor="gmail",
        )


# --------------------------------------------------------------------------------
# Backend IMAP (Outlook / Hotmail)
# --------------------------------------------------------------------------------

class IMAPBackend(BaseBackend):
    """
    Backend IMAP generico. Funciona con Outlook/Hotmail usando
    contrasena de aplicacion Microsoft.

    Como obtener la contrasena de aplicacion:
    1. Ir a account.microsoft.com
    2. Seguridad -> Opciones de seguridad avanzadas
    3. Contrasenas de aplicacion -> Crear nueva
    4. Guardar como variable de entorno OUTLOOK_APP_PASSWORD
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self._servidor = config.get("servidor", "imap-mail.outlook.com")
        self._puerto = config.get("puerto", 993)
        self._ssl = config.get("ssl", True)
        self._password_env = config.get("password_env", "OUTLOOK_APP_PASSWORD")
        self._conn: Optional[imaplib.IMAP4_SSL] = None

    def conectar(self) -> None:
        if self._conn:
            try:
                self._conn.noop()
                return  # Conexion activa
            except Exception:
                self._conn = None

        password = os.environ.get(self._password_env, "")
        if not password:
            raise ValueError(
                f"Variable de entorno {self._password_env!r} no configurada.\n"
                f"En PowerShell: $env:{self._password_env} = 'tu-contrasena-app'"
            )

        if self._ssl:
            ctx = ssl.create_default_context()
            self._conn = imaplib.IMAP4_SSL(
                self._servidor, self._puerto, ssl_context=ctx
            )
        else:
            self._conn = imaplib.IMAP4(self._servidor, self._puerto)

        self._conn.login(self.email, password)
        log.info(f"  [{self.nombre}] Conectado a {self._servidor} via IMAP")

    def buscar_ids(self, query: str, fecha_desde: datetime,
                   fecha_hasta: Optional[datetime] = None) -> list[str]:
        self._conn.select("INBOX", readonly=True)  # readonly=True -> no marca como leido

        # Convertir query de estilo Gmail a criterios IMAP
        criterios = _query_gmail_a_imap(query, fecha_desde, fecha_hasta)

        _, datos = self._conn.search(None, *criterios)
        if not datos or not datos[0]:
            return []

        return datos[0].split()

    def obtener_correo(self, id_mensaje: bytes,
                       incluir_adjuntos: bool = True) -> Optional[Correo]:
        # BODY.PEEK no marca el mensaje como leido (a diferencia de BODY)
        _, datos = self._conn.fetch(id_mensaje, "(BODY.PEEK[])")
        if not datos or not datos[0]:
            return None

        raw = datos[0][1]
        msg = email.message_from_bytes(raw)

        fecha = _parsear_fecha(msg.get("Date", ""))
        texto, adjuntos = _extraer_contenido_imap(msg, incluir_adjuntos)

        return Correo(
            id=id_mensaje.decode() if isinstance(id_mensaje, bytes) else id_mensaje,
            asunto=_decodificar_header(msg.get("Subject", "")),
            remitente=msg.get("From", ""),
            destinatario=msg.get("To", ""),
            fecha=fecha,
            texto_plano=texto,
            snippet=texto[:150],
            adjuntos=adjuntos,
            cuenta_nombre=self.nombre,
            cuenta_email=self.email,
            proveedor="imap",
        )


# ================================================================================
# CLASE PRINCIPAL PUBLICA
# ================================================================================

class LectorCorreos:
    """
    Punto de entrada principal del skill.
    Crea el backend correcto segun el tipo de cuenta.

    Uso:
        lector = LectorCorreos(config_cuenta)
        correos = lector.buscar(query="from:rappi", dias=7)
        correos = lector.buscar(
            query="from:rappi",
            fecha_desde=datetime(2026, 1, 1),
            fecha_hasta=datetime(2026, 3, 31)
        )
    """

    BACKENDS = {
        "gmail": GmailBackend,
        "imap":  IMAPBackend,
    }

    def __init__(self, config: dict):
        tipo = config.get("tipo", "gmail").lower()
        if tipo not in self.BACKENDS:
            raise ValueError(
                f"Tipo de cuenta desconocido: {tipo!r}. "
                f"Opciones: {list(self.BACKENDS)}"
            )
        self._backend = self.BACKENDS[tipo](config)

    def buscar(self, query: str, dias: int = 7,
               fecha_desde: Optional[datetime] = None,
               fecha_hasta: Optional[datetime] = None,
               incluir_adjuntos: bool = True) -> list[Correo]:
        """
        Busca correos. Ver BaseBackend.buscar() para documentacion completa.
        IMPORTANTE: nunca marca correos como leidos.
        """
        return self._backend.buscar(
            query=query,
            dias=dias,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            incluir_adjuntos=incluir_adjuntos,
        )

    @property
    def nombre(self) -> str:
        return self._backend.nombre

    @property
    def email(self) -> str:
        return self._backend.email


# ================================================================================
# FUNCIONES AUXILIARES INTERNAS
# ================================================================================

class _StripHTML(HTMLParser):
    _SKIP_TAGS = {"style", "script"}

    def __init__(self):
        super().__init__()
        self.partes = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth:
            return
        limpio = data.strip()
        if limpio:
            self.partes.append(limpio)

    def resultado(self) -> str:
        return " | ".join(self.partes)


def _html_a_texto(html: str) -> str:
    p = _StripHTML()
    p.feed(html)
    return p.resultado()


def _decodificar_header(valor: str) -> str:
    partes = decode_header(valor)
    resultado = []
    for parte, charset in partes:
        if isinstance(parte, bytes):
            resultado.append(parte.decode(charset or "utf-8", errors="replace"))
        else:
            resultado.append(parte)
    return "".join(resultado)


def _parsear_fecha(fecha_str: str) -> datetime:
    from email.utils import parsedate_to_datetime
    try:
        dt = parsedate_to_datetime(fecha_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)


def _extraer_contenido_gmail(service, msg_id: str, payload: dict,
                              incluir_adjuntos: bool) -> tuple[str, list[Adjunto]]:
    """Extrae texto y adjuntos del payload de Gmail API."""
    texto = ""
    adjuntos = []

    mime = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")
    body_id = payload.get("body", {}).get("attachmentId", "")
    filename = payload.get("filename", "")

    if mime == "text/plain" and body_data:
        texto = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

    elif mime == "text/html" and body_data:
        html = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
        texto = _html_a_texto(html)

    elif filename and body_id and incluir_adjuntos:
        att = service.users().messages().attachments().get(
            userId="me", messageId=msg_id, id=body_id
        ).execute()
        datos = base64.urlsafe_b64decode(att["data"])
        adjuntos.append(Adjunto(
            nombre=filename,
            tipo_mime=mime,
            datos=datos,
            tamaño_bytes=len(datos),
        ))

    for parte in payload.get("parts", []):
        sub_texto, sub_adj = _extraer_contenido_gmail(
            service, msg_id, parte, incluir_adjuntos
        )
        if sub_texto and not texto:
            texto = sub_texto
        adjuntos.extend(sub_adj)

    return texto, adjuntos


def _extraer_contenido_imap(msg: email.message.Message,
                             incluir_adjuntos: bool) -> tuple[str, list[Adjunto]]:
    """Extrae texto y adjuntos de un mensaje IMAP."""
    texto = ""
    adjuntos = []

    if msg.is_multipart():
        for parte in msg.walk():
            tipo = parte.get_content_type()
            disp = str(parte.get("Content-Disposition", ""))

            if tipo == "text/plain" and "attachment" not in disp:
                carga = parte.get_payload(decode=True)
                charset = parte.get_content_charset() or "utf-8"
                if carga and not texto:
                    texto = carga.decode(charset, errors="replace")

            elif tipo == "text/html" and "attachment" not in disp and not texto:
                carga = parte.get_payload(decode=True)
                charset = parte.get_content_charset() or "utf-8"
                if carga:
                    texto = _html_a_texto(carga.decode(charset, errors="replace"))

            elif incluir_adjuntos and "attachment" in disp:
                nombre = parte.get_filename() or "adjunto"
                nombre = _decodificar_header(nombre)
                datos = parte.get_payload(decode=True) or b""
                adjuntos.append(Adjunto(
                    nombre=nombre,
                    tipo_mime=tipo,
                    datos=datos,
                    tamaño_bytes=len(datos),
                ))
    else:
        tipo = msg.get_content_type()
        carga = msg.get_payload(decode=True) or b""
        charset = msg.get_content_charset() or "utf-8"
        if tipo == "text/plain":
            texto = carga.decode(charset, errors="replace")
        elif tipo == "text/html":
            texto = _html_a_texto(carga.decode(charset, errors="replace"))

    return texto, adjuntos


def _query_gmail_a_imap(query: str, fecha_desde: datetime,
                         fecha_hasta: Optional[datetime]) -> list[str]:
    """
    Convierte una query estilo Gmail a criterios IMAP basicos.
    Soporta: from:, subject:, palabras clave simples.
    """
    criterios = []

    # Fecha desde
    criterios.append(f'SINCE "{fecha_desde.strftime("%d-%b-%Y")}"')

    # Fecha hasta
    if fecha_hasta:
        criterios.append(f'BEFORE "{fecha_hasta.strftime("%d-%b-%Y")}"')

    # from:
    m = re.search(r'from:(\S+)', query)
    if m:
        criterios.append(f'FROM "{m.group(1)}"')

    # subject:
    m = re.search(r'subject:([^\s]+)', query)
    if m:
        criterios.append(f'SUBJECT "{m.group(1)}"')

    if not criterios[2:]:  # Sin filtros de contenido -> todos los correos del periodo
        criterios.append("ALL")

    return criterios


# ================================================================================
# MODO STANDALONE -- Para pruebas desde la terminal
# ================================================================================

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="lector_correos.py -- Prueba de conexion y busqueda"
    )
    parser.add_argument("--config",    required=True, help="Ruta al config_correos.json")
    parser.add_argument("--cuenta",    required=True, help="Nombre de la cuenta (ej: hernan)")
    parser.add_argument("--query",     default="",    help="Query de busqueda")
    parser.add_argument("--dias",      type=int, default=7)
    parser.add_argument("--adjuntos",  action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    with open(args.config) as f:
        cfg = json.load(f)

    # Buscar la cuenta en Gmail o IMAP
    cuenta_cfg = None
    if args.cuenta in cfg.get("cuentas_gmail", {}):
        c = cfg["cuentas_gmail"][args.cuenta]
        cuenta_cfg = {
            "tipo":             "gmail",
            "nombre":           args.cuenta,
            "email":            c["email"],
            "credentials_file": cfg["rutas"]["credentials_gmail"],
            "tokens_dir":       cfg["rutas"]["tokens_gmail"],
        }
    elif args.cuenta in cfg.get("cuentas_imap", {}):
        c = cfg["cuentas_imap"][args.cuenta]
        cuenta_cfg = {
            "tipo":        "imap",
            "nombre":      args.cuenta,
            "email":       c["email"],
            "servidor":    c["servidor"],
            "puerto":      c["puerto"],
            "ssl":         c["ssl"],
        }
    else:
        print(f"Cuenta '{args.cuenta}' no encontrada en el config.")
        exit(1)

    lector = LectorCorreos(cuenta_cfg)
    correos = lector.buscar(
        query=args.query,
        dias=args.dias,
        incluir_adjuntos=args.adjuntos,
    )

    print(f"\n{len(correos)} correos encontrados:\n")
    for c in correos:
        print(f"  [{c.fecha_str}] {c.remitente[:40]:<40} | {c.asunto[:60]}")
        if c.adjuntos:
            for a in c.adjuntos:
                print(f"    adjunto: {a.nombre} ({a.tamaño_bytes:,} bytes)")
