# Plataforma de Gestión Financiera Familiar — MCGHR
> Este archivo es leído automáticamente por Claude Desktop al abrir esta carpeta.
> Contiene todo el contexto del proyecto. Leelo completo antes de hacer cualquier cambio.

---

## Qué es este proyecto

Sistema de gestión financiera personal para Hernan (GHR) y Martha (MC). Automatiza la
recolección de datos financieros desde múltiples fuentes (correos Gmail, Hotmail, PDFs
bancarios), los clasifica con Claude API, los almacena en una base de datos SQLite, y
los expone a través de una web app local para revisión humana y un dashboard en Power BI.

**No es un script puntual — es una plataforma modular diseñada para crecer.**

---

## Personas y cuentas

| Persona | Alias en código | Gmail principal | Hotmail | Observaciones |
|---|---|---|---|---|
| Hernan Rizzi | `GHR` | ghrizzi.goog@gmail.com | — | Cuenta principal de finanzas |
| Martha (esposa) | `MC` | malu82@gmail.com | Puede haber correos | Misma estructura que GHR |
| Sistema | `claude` | MCGHR.claude@gmail.com | — | Cuenta operativa del proyecto |

---

## Bancos y entidades financieras activas

| Entidad | Productos | Titular | Notificaciones |
|---|---|---|---|
| Bancolombia | Cuenta Corriente, TC | GHR | Email + SMS (shortcode 891333) |
| BBVA Colombia | Cuenta Corriente, TC | GHR | Email + SMS (shortcode 855422) |
| Banco de Occidente | TC Visa Signature LATAM (5749) | GHR | Extracto PDF mensual |
| Nequi | Cuenta digital | GHR | Solo app móvil, sin email |
| InteractiveBrokers | Cuenta de inversiones | GHR | Statements mensuales PDF |

---

## Arquitectura — 4 capas

```
Capa 1: lector_correos.py     → skill reutilizable (Gmail OAuth + Outlook IMAP)
Capa 2: finanzas_familia.py   → orquestador con filtros específicos de finanzas
Capa 3: app_revision.py       → web app local Flask para revisión humana (Fase 2)
Capa 4: auditor_correos.py    → detector de gaps en clasificación (Fase 3)
```

**Regla de dependencias:** cada capa solo importa capas inferiores. finanzas_familia
importa lector_correos. app_revision importa finanzas_familia. Nunca al revés.

---

## Estructura de carpetas

```
C:\Users\ghriz\
├── .claude\skills\lector_correos\     ← skill importable
├── .claude\Proyectos\FinanzasFamilia\ ← este proyecto (código)
└── .gmail-mcp\                        ← credenciales OAuth y tokens

C:\Users\ghriz\OneDrive\Finanzas MCGHR\
├── Generales\
│   ├── finanzas.db                    ← SQLite, fuente de verdad
│   ├── finanzas_maestro.xlsx          ← generado desde SQLite para Power BI
│   ├── reglas_clasificacion.json      ← aprendizaje por confirmación humana
│   ├── Stage\                         ← archivos pendientes de revisión
│   └── Dashboards\                    ← archivos .pbix de Power BI
├── GHR\
│   ├── Extractos\{Banco}\{Producto}\  ← extractos bancarios PDF
│   ├── Facturas\{YYYY-MM}\            ← facturas nombradas: Rappi_001.pdf
│   └── Impuestos\
└── MC\
    └── (misma estructura que GHR)
```

---

## Base de datos — SQLite

Archivo: `OneDrive\Finanzas MCGHR\Generales\finanzas.db`

Schema v1.1 activo — ver `docs/schema_v1.md` y `schema/finanzas_v1_1.sql` en el repo.

**Regla crítica:** NUNCA escribir datos financieros directamente en el Excel.
El Excel se regenera desde SQLite con el script `exportar_excel.py` (futuro).
Power BI conecta al Excel, no al SQLite directamente.

---

## Configuración — config_correos.json

Toda la configuración vive en `config_correos.json` (solo en PC local, nunca en repo).
Los scripts no tienen rutas ni credenciales hardcodeadas — todo viene del config.

**Variables de entorno requeridas:**
- `ANTHROPIC_API_KEY` — Claude API key (console.anthropic.com)
- `OUTLOOK_APP_PASSWORD` — Contraseña de aplicación Microsoft (account.microsoft.com)

---

## Módulos futuros planificados

- `InversionesBroker` — seguimiento de posiciones en Interactive Brokers
- `AnalisisGastos` — recomendaciones de reducción con Claude API
- `PresupuestoBase0` — planificación presupuestal mensual
- `GestionSemanal` — tracking de gastos vs presupuesto

---

## Decisiones de diseño importantes

1. **SQLite sobre Excel como BD:** el Excel no puede ser escrito mientras está abierto.
2. **Stage area para clasificación dudosa:** confianza < 0.75 → Stage.
3. **No marcar correos como leídos:** anti-duplicado via `correos_procesados` en SQLite.
4. **Hotmail via IMAP:** conector OAuth M365 no funciona con cuentas personales.
5. **Modularidad:** cada script es importable como módulo Python.
6. **Parametrización total:** ninguna ruta o credencial hardcodeada.

---

## Historial de decisiones

| Fecha | Decisión | Razón |
|---|---|---|
| Mayo 2026 | SQLite como BD principal | Escritura concurrente, no bloqueado por Excel abierto |
| Mayo 2026 | IMAP para Hotmail | Conector OAuth M365 no funciona con cuentas personales |
| Mayo 2026 | Stage area + aprendizaje | Clasificación automática con supervisión humana |
| Mayo 2026 | Arquitectura en 4 fases | Sistema crece modularmente sin reescribir lo existente |
| Junio 2026 | Schema v1.1 con doble entrada contable | Balance patrimonial real y trazabilidad completa |

---
*Última actualización: Junio 2026 — Plataforma MCGHR*
