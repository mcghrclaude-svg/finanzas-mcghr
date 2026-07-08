# Finanzas MCGHR
Plataforma de gestion financiera familiar para Hernan (GHR) y Martha (MC).

## Que hace
Automatiza la recoleccion de datos financieros desde correos Gmail
(incluyendo SMS bancarios reenviados), los analiza con Claude Desktop,
y los persiste en una base de datos SQLite con doble entrada contable.

## Stack
- Claude Desktop Pro con MCPs: mcp_lector_correos, filesystem, sqlite, github
- Python 3.14 con venv en Windows
- SQLite (finanzas.db en OneDrive)
- Gmail OAuth 2.0 (multiples cuentas)
- autoforward app en iPhone para reenvio de SMS bancarios
- Backend FastAPI + Frontend React (Vite) para revision humana

## Estructura del repositorio
```
finanzas-mcghr/
├── README.md
├── backend/
│   ├── api/v1/routers/        <- Endpoints REST (catalogos, inbox, tools, etc.)
│   ├── models/                <- Modelos SQLAlchemy
│   └── services/               <- Logica de negocio
├── frontend/
│   └── src/modules/            <- Modulos React (Transacciones, Catalogos, Tools, etc.)
├── docs/
│   └── schema_v1.md            <- Schema de base de datos aprobado
├── schema/
│   └── finanzas_v1_4b.sql      <- SQL de creacion (version vigente)
├── src/
│   └── finanzas_familia.py     <- Utilidades del pipeline financiero
├── tests/                       <- Tests backend
├── skills/
│   └── lector_correos/
│       └── lector_correos.py   <- Skill de lectura de correos Gmail
├── mcp_servers/
│   └── mcp_lector_correos/
│       └── server.py           <- Servidor MCP
├── Dockerfile.backend
├── Dockerfile.frontend
└── docker-compose.yml           <- Contenedores para backend/frontend
```

## Estado actual
- [x] Servidor MCP mcp_lector_correos funcionando (Gmail, 3 cuentas)
- [x] MCPs filesystem, sqlite y github configurados en Claude Desktop
- [x] autoforward configurado en iPhone de Hernan (SMS → Gmail)
- [x] Schema de base de datos v1 aprobado e implementado (SQL aplicado, ver schema/)
- [x] Datos iniciales del catalogo (seed de categorias, cuentas, contrapartes, personas)
- [x] Backend FastAPI (routers de catalogos, inbox, tools, transacciones, etc.)
- [x] Frontend React para revision humana (modulos Transacciones, Catalogos, Tools)
- [ ] Prompt de sesion para procesamiento de correos (ETL Claude Desktop)

## Seguridad
El archivo config_correos.json con datos reales NUNCA va al repositorio.
Solo existe en la PC local. Ver .gitignore.
