# mcp_lector_correos

Servidor MCP para lectura de correos Gmail.
Parte de la Plataforma de Gestion Financiera Familiar MCGHR.

## Ubicacion en la PC

```
C:\Users\ghriz\.claude\skills\mcp_lector_correos\
├── server.py       <- este servidor
└── README.md       <- este archivo
```

## Que hace

Expone tres herramientas MCP que Claude Desktop puede invocar:

| Herramienta | Que hace |
|---|---|
| `buscar_correos` | Lista metadatos de correos que cumplen un criterio Gmail |
| `leer_correo` | Obtiene texto completo y metadatos de adjuntos de un correo |
| `descargar_adjunto` | Descarga un adjunto a una carpeta en disco |

**No tiene logica de negocio.** No clasifica, no parsea montos, no escribe en SQLite.
Solo lee correos y descarga archivos. El analisis lo hace Claude Desktop.

## Instalacion

### 1. Instalar dependencia nueva

Activar el entorno virtual y agregar `mcp`:

```powershell
cd C:\Users\ghriz\.claude\Proyectos\FinanzasFamilia
.\venv\Scripts\Activate.ps1
pip install mcp
```

Verificar que las demas dependencias de Gmail esten instaladas:

```powershell
pip show google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Si alguna falta:

```powershell
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2. Registrar en claude_desktop_config.json

Ruta del archivo:
```
C:\Users\ghriz\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json
```

Agregar este bloque en `mcpServers` y **eliminar** el bloque `gmail-multi`:

```json
"mcp_lector_correos": {
  "command": "C:\\Users\\ghriz\\.claude\\Proyectos\\FinanzasFamilia\\venv\\Scripts\\python.exe",
  "args": [
    "C:\\Users\\ghriz\\.claude\\skills\\mcp_lector_correos\\server.py",
    "--config",
    "C:\\Users\\ghriz\\.claude\\Proyectos\\FinanzasFamilia\\config_correos.json"
  ]
}
```

### 3. Reiniciar Claude Desktop

Cerrar completamente (no solo la ventana -- salir desde el icono de la barra de tareas)
y volver a abrir.

## Verificacion rapida desde la terminal

Probar que el servidor arranca sin errores:

```powershell
C:\Users\ghriz\.claude\Proyectos\FinanzasFamilia\venv\Scripts\python.exe `
  C:\Users\ghriz\.claude\skills\mcp_lector_correos\server.py `
  --config C:\Users\ghriz\.claude\Proyectos\FinanzasFamilia\config_correos.json
```

Debe mostrar algo como:
```
2026-05-31 [INFO] mcp_lector_correos arrancando (transporte: stdio)
2026-05-31 [INFO] Config: C:\Users\ghriz\...\config_correos.json
2026-05-31 [INFO] Cuentas Gmail activas: ['hernan', 'malu']
2026-05-31 [INFO] Conexion a Gmail es lazy -- se conecta al primer llamado por cuenta
```

Despues presionar Ctrl+C para salir. Si muestra ese output, el servidor esta listo.

## Primera ejecucion (autorizacion OAuth)

La primera vez que Claude Desktop invoque `buscar_correos` o `leer_correo` para
una cuenta, el servidor necesita autorizar el acceso OAuth. Esto abre el browser
automaticamente y pide iniciar sesion con la cuenta Gmail correspondiente.

Esto ocurre una sola vez por cuenta. El token queda guardado en:
```
C:\Users\ghriz\.gmail-mcp\tokens\hernan.json
C:\Users\ghriz\.gmail-mcp\tokens\malu.json
```

En sesiones futuras el token se renueva en segundo plano sin abrir el browser.

## Comportamiento de errores

Todas las herramientas retornan JSON. Nunca lanzan excepciones hacia Claude Desktop.

| Situacion | Que retorna |
|---|---|
| Cuenta no encontrada | `{"error": "cuenta_no_encontrada", "mensaje": "..."}` |
| Error de red (3 reintentos) | `{"error": "error_red", "mensaje": "..."}` |
| Adjunto no encontrado | `{"ok": false, "error": "adjunto_no_encontrado", ...}` |
| Error de autenticacion | Falla rapido sin reintento, mensaje claro |

## Cuentas disponibles

Definidas en `config_correos.json > cuentas_gmail`:

| Nombre | Email | Titular | Activa |
|---|---|---|---|
| hernan | ghrizzi.goog@gmail.com | GHR | Si |
| malu | malu82@gmail.com | MC | Si |
| claude | MCGHR.claude@gmail.com | sistema | No (activar si llegan correos financieros) |

## Limites

- `max_resultados` por defecto: 50. Maximo absoluto: 200.
- Si hay mas correos que `max_resultados`, el campo `truncado: true` avisa que
  se debe acotar el rango de fechas o ser mas especifico en la query.

## Logs

El servidor escribe logs a stderr. Claude Desktop los captura en:
```
%APPDATA%\Claude\logs\mcp-server-mcp_lector_correos.log
```

Util para diagnosticar problemas de conexion o autenticacion.

## Notas de diseno

- **Conexion lazy:** el servidor arranca sin conectarse a Gmail. La conexion
  ocurre al primer llamado por cuenta. Esto permite tenerlo siempre registrado
  sin overhead hasta que se usa.
- **Sin marca de lectura:** nunca modifica el estado de ningun buzon.
- **Reintentos:** 3 intentos con backoff de 2s y 4s, solo para errores de red.
  Errores de configuracion o autenticacion fallan inmediatamente con mensaje claro.
- **Adjuntos:** `buscar_correos` y `leer_correo` no retornan bytes.
  Solo `descargar_adjunto` escribe datos en disco.
