# Entorno local de desarrollo — PC GHR
**Fecha:** Junio 2026  
**Propósito:** Referencia exacta de lo instalado en la PC para que claude.ai pueda dar instrucciones precisas sin adivinar rutas ni versiones.

---

## Sistema operativo y usuario

| Campo | Valor |
|---|---|
| OS | Windows 11 |
| Usuario | `ghriz` |
| Home | `C:\Users\ghriz\` |
| OneDrive | `C:\Users\ghriz\OneDrive\` |

---

## Software instalado

| Herramienta | Versión | Notas |
|---|---|---|
| Python | 3.14 (default) | **NO usar para este proyecto** |
| Python | **3.12.10** | ✅ Usar siempre con `py -3.12` |
| Node.js | 20+ | Para el frontend |
| npm | incluido con Node | |
| Git | instalado | Autenticación via browser (GitHub GCM) |
| Claude Desktop | instalado | Cowork + MCP configurados |
| pip | 25.0.1 (en venv 3.12) | Ignorar aviso de upgrade |

---

## Repositorio local

| Campo | Valor |
|---|---|
| Ruta | `C:\Users\ghriz\finanzas-mcghr\` |
| Origen | `https://github.com/mcghrclaude-svg/finanzas-mcghr` |
| Rama activa | `main` |
| Clonado con | `git clone` + autenticación browser |

### Entornos virtuales Python

| Componente | Ruta del venv | Estado |
|---|---|---|
| Backend principal | `C:\Users\ghriz\finanzas-mcghr\venv\` | ✅ Creado con py -3.12, dependencias instaladas |
| MCP lector correos | `C:\Users\ghriz\finanzas-mcghr\mcp_servers\mcp_lector_correos\venv\` | ⏳ Pendiente crear |

**Activar backend:**
```powershell
cd C:\Users\ghriz\finanzas-mcghr
venv\Scripts\activate
```

**Activar MCP:**
```powershell
cd C:\Users\ghriz\finanzas-mcghr\mcp_servers\mcp_lector_correos
venv\Scripts\activate
```

### Frontend

| Campo | Valor |
|---|---|
| Ruta | `C:\Users\ghriz\finanzas-mcghr\frontend\` |
| `node_modules/` | ✅ Instalado (`npm install` ejecutado) |
| Puerto dev | 3000 |

---

## Base de datos

| Campo | Valor |
|---|---|
| Archivo | `C:\Users\ghriz\OneDrive\Finanzas MCGHR\Generales\finanzas.db` |
| Motor | SQLite 3 |
| Schema | v1.1 aplicado |
| Tablas | 22 |
| Vistas | 5 |
| Datos | Vacía — sin registros todavía |
| Modo WAL | Activado |
| Acceso MCP | Via `mcp__sqlite__*` apuntando a la ruta de OneDrive |

---

## Claude Desktop — MCPs configurados

| MCP | Descripción | Estado |
|---|---|---|
| `mcp__sqlite__*` | Acceso directo a `finanzas.db` | ✅ Activo |
| `mcp__github__*` | Acceso al repo `finanzas-mcghr` | ✅ Activo (owner: `mcghrclaude-svg`) |
| `mcp__filesystem__*` | Acceso a archivos locales bajo `C:\Users\ghriz\.claude\` | ✅ Activo |
| `mcp__mcp_lector_correos__*` | MCP Gmail/IMAP (server.py) | ⚠️ Registrado pero sin tokens OAuth |

---

## Archivos locales fuera del repo (no en GitHub)

### `C:\Users\ghriz\.claude\`
Carpeta raíz de Claude Desktop. Contiene:

| Archivo | Descripción | En repo |
|---|---|---|
| `config_correos.json` | Configuración real de cuentas de correo (credenciales) | ❌ NUNCA |
| `activar.ps1` | Script PowerShell para activar el entorno de trabajo | ❌ No |
| `instalar.ps1` | Script PowerShell de instalación inicial | ❌ No |

### `C:\Users\ghriz\.gmail-mcp\tokens\`
| Archivo | Descripción |
|---|---|
| `hernan.json` | Token OAuth Gmail de GHR (sensible) |
| `malu.json` | Token OAuth Gmail de MC (sensible) |

Estado actual: **no generados** — el OAuth flow no se ha ejecutado todavía.

---

## Archivos de configuración en el repo local

| Archivo | Ruta | Estado |
|---|---|---|
| `.env.dev` | `C:\Users\ghriz\finanzas-mcghr\.env.dev` | Presente (valores dev) |
| `.env.example` | `C:\Users\ghriz\finanzas-mcghr\.env.example` | En repo — plantilla |
| `.env` | NO existe todavía | Hay que crear copiando `.env.dev` y editando `ANTHROPIC_API_KEY` |

---

## Cuentas bancarias del proyecto (referencia para catálogo)

### GHR (Hernan)
| Banco | Tipo | ID sugerido |
|---|---|---|
| Bancolombia | Cuenta corriente | `BC_CC_GHR` |
| BBVA | (confirmar tipo) | `BBVA_GHR` |
| Banco de Occidente | (confirmar tipo) | `OCO_GHR` |
| Nequi | Billetera digital | `NEQUI_GHR` |
| Interactive Brokers | Inversiones USD | `IBKR_USD` |

### MC (Martha)
| Banco | Tipo | ID sugerido |
|---|---|---|
| Bancolombia | Cuenta (891333) | `BC_MC` |
| BBVA | Cuenta (855422) | `BBVA_MC` |
| Banco de Occidente | Cuenta (85722) | `OCO_MC` |

---

## Monedas del proyecto

| ID | Nombre | Símbolo | Crypto |
|---|---|---|---|
| COP | Peso colombiano | $ | No |
| USD | Dólar estadounidense | US$ | No |
| ARS | Peso argentino | AR$ | No |
| EUR | Euro | € | No |
| USDT | Tether | USDT | Sí |

---

## Personas del proyecto

| ID | Nombre completo |
|---|---|
| GHR | Hernan Rizzi |
| MC | Martha (apellido a confirmar) |

---

## Notas para instrucciones en PowerShell

- Siempre usar `py -3.12` en lugar de `python` o `py` a secas (hay dos versiones instaladas)
- Siempre activar el venv del componente correspondiente antes de correr scripts Python
- Las rutas con espacios (OneDrive) requieren comillas: `"C:\Users\ghriz\OneDrive\Finanzas MCGHR\Generales\finanzas.db"`
- Git se autentica via browser automáticamente — no pedir credenciales en comandos
