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
- App web local Flask para revision humana (Fase 2)

## Estructura del repositorio
```
finanzas-mcghr/
├── README.md
├── docs/
│   └── schema_v1.md          <- Schema de base de datos aprobado
├── schema/
│   └── finanzas_v1.sql       <- SQL de creacion (pendiente)
├── skills/
│   └── lector_correos/
│       └── lector_correos.py <- Skill de lectura de correos Gmail
└── mcp_servers/
    └── mcp_lector_correos/
        └── server.py         <- Servidor MCP
```

## Estado actual
- [x] Servidor MCP mcp_lector_correos funcionando (Gmail, 3 cuentas)
- [x] MCPs filesystem, sqlite y github configurados en Claude Desktop
- [x] autoforward configurado en iPhone de Hernan (SMS → Gmail)
- [x] Schema de base de datos v1 aprobado
- [ ] SQL de creacion de tablas
- [ ] Datos iniciales del catalogo
- [ ] Prompt de sesion para procesamiento de correos
- [ ] App web local para revision humana (Fase 2)

## Seguridad
El archivo config_correos.json con datos reales NUNCA va al repositorio.
Solo existe en la PC local. Ver .gitignore.
