# Entorno local de desarrollo — PC GHR
**Fecha:** Junio 2026
**Proposito:** Referencia exacta de lo instalado en la PC para que claude.ai pueda dar instrucciones precisas sin adivinar rutas ni versiones.

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

| Herramienta | Version | Notas |
|---|---|---|
| Python | 3.14 (default) | **NO usar para este proyecto** |
| Python | **3.12.10** | Usar siempre con `py -3.12` |
| Node.js | 20+ | Para el frontend |
| npm | incluido con Node | |
| Git | instalado | Autenticacion via browser (GitHub GCM) |
| Claude Desktop | instalado | Cowork + MCP configurados |
| pip | 25.0.1 (en venv 3.12) | Ignorar aviso de upgrade |

---

## Repositorio local

| Campo | Valor |
|---|---|
| Ruta | `C:\Users\ghriz\finanzas-mcghr\` |
| Origen | `https://github.com/mcghrclaude-svg/finanzas-mcghr` |
| Rama activa | `main` |
| git user.email | `mcghr.claude@gmail.com` |
| git user.name | `Hernan Rizzi` |

### Entornos virtuales Python

| Componente | Ruta del venv | Estado |
|---|---|---|
| Backend principal | `C:\Users\ghriz\finanzas-mcghr\venv\` | Creado con py -3.12, dependencias instaladas |
| MCP lector correos | `C:\Users\ghriz\finanzas-mcghr\mcp_servers\mcp_lector_correos\venv\` | Pendiente crear |

**Activar backend (SIEMPRE antes de cualquier comando Python):**
```powershell
cd C:\Users\ghriz\finanzas-mcghr
venv\Scripts\activate
```

**Nota PowerShell:** si los scripts .ps1 no corren, ejecutar primero:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Frontend

| Campo | Valor |
|---|---|
| Ruta | `C:\Users\ghriz\finanzas-mcghr\frontend\` |
| `node_modules/` | Instalado (`npm install` ejecutado) |
| Puerto dev | 3000 |
| `postcss.config.js` | REQUERIDO para que Tailwind compile en Vite — ya existe en repo |

---

## Variables de entorno

| Archivo | Ubicacion | Uso |
|---|---|---|
| `.env.dev` | raiz del repo | Variables backend: ENV, DB_PATH, ANTHROPIC_API_KEY |
| `frontend/.env.local` | `frontend/` | Variables VITE_*: VITE_API_URL, VITE_USE_MOCK, VITE_MOCK_SCENARIO |

**Regla critica:** las variables `VITE_*` NO van en `.env.dev`. Pydantic las rechaza con "extra inputs not permitted". Van exclusivamente en `frontend/.env.local`.

---

## Comandos frecuentes

**Levantar backend:**
```powershell
cd C:\Users\ghriz\finanzas-mcghr
venv\Scripts\activate
uvicorn backend.main:app --reload --port 8000
```

**Levantar frontend:**
```powershell
cd C:\Users\ghriz\finanzas-mcghr\frontend
npm run dev
```

**Correr tests de integracion:**
```powershell
cd C:\Users\ghriz\finanzas-mcghr
venv\Scripts\activate
pytest tests/integration/test_catalogos.py -v
```

**Correr seed:**
```powershell
cd C:\Users\ghriz\finanzas-mcghr
venv\Scripts\activate
python -m scripts.seed.seed_catalogos
python -m scripts.seed.seed_velocidad_historica
```

**Aplicar migracion SQL:**
```powershell
sqlite3 "C:\Users\ghriz\OneDrive\Finanzas MCGHR\Generales\finanzas.db" < scripts\migrations\002_dashboard_schema.sql
```

---

## Base de datos

| Campo | Valor |
|---|---|
| Archivo | `C:\Users\ghriz\OneDrive\Finanzas MCGHR\Generales\finanzas.db` |
| Motor | SQLite 3 |
| Schema | v1.1 aplicado |
| Tablas | 22 |
| Vistas | 5 |
| Modo WAL | Activado |
| Acceso MCP | Via `mcp__sqlite__*` apuntando a la ruta de OneDrive |

---

## Claude Desktop — MCPs configurados

| MCP | Descripcion | Estado |
|---|---|---|
| `mcp__sqlite__*` | Acceso directo a `finanzas.db` | Activo |
| `mcp__github__*` | Acceso al repo `finanzas-mcghr` | Activo (owner: `mcghrclaude-svg`) |
| `mcp__filesystem__*` | Acceso a archivos locales | Activo |
| `mcp__mcp_lector_correos__*` | MCP Gmail/IMAP | Registrado pero sin tokens OAuth |

---

## Archivos locales fuera del repo

### `C:\Users\ghriz\.claude\`

| Archivo | Descripcion | En repo |
|---|---|---|
| `config_correos.json` | Configuracion real de cuentas de correo | NUNCA |
| `activar.ps1` | Script de activacion del entorno | No |
| `instalar.ps1` | Script de instalacion inicial | No |

### `C:\Users\ghriz\.gmail-mcp\tokens\`

| Archivo | Descripcion |
|---|---|
| `hernan.json` | Token OAuth Gmail de GHR (sensible) |
| `malu.json` | Token OAuth Gmail de MC (sensible) |

Estado actual: **no generados** — el OAuth flow no se ha ejecutado.

---

## Cuentas bancarias del proyecto

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

## Notas para instrucciones en PowerShell

- Usar `py -3.12` en lugar de `python` o `py` a secas
- Siempre activar venv antes de correr scripts Python
- Las rutas con espacios (OneDrive) requieren comillas
- Git se autentica via browser automaticamente
- Scripts .ps1 requieren: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
