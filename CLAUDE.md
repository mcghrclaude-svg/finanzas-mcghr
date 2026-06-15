# Plataforma de Gestión Financiera Familiar — MCGHR
> Este archivo es leído automáticamente por herramientas de IA (Claude, Codex, Grok, etc.)
> Contiene el contexto esencial del proyecto. Leerlo completo antes de hacer cualquier cambio.
> Para continuar el proyecto, leer en orden: este archivo → functional_spec.md → architecture.md → schema_v1.md → testing_strategy.md

---

## Qué es este proyecto

Plataforma de gestión financiera personal para Hernan (GHR) y Martha (MC). Automatiza la
recolección de datos financieros desde múltiples fuentes (correos Gmail, Hotmail, PDFs
bancarios, app mobile), los clasifica con Claude API, los almacena en SQLite, y los expone
a través de una web app local (FastAPI + React) con dashboard y cola de revisión humana.

**No es un script puntual — es una plataforma modular diseñada para crecer.**

---

## Documentación completa del proyecto

| Documento | Contenido |
|---|---|
| `docs/functional_spec.md` | Especificación funcional completa — qué hace la app, módulo por módulo |
| `docs/architecture.md` | Arquitectura técnica — stack, estructura de carpetas, decisiones de diseño |
| `docs/schema_v1.md` | Documentación del schema de base de datos |
| `docs/testing_strategy.md` | Estrategia de entornos de prueba, datos dummy, scripts y herramientas |
| `schema/finanzas_v1_1.sql` | Schema SQL activo (versión 1.1) |
| `docs/api.md` | Documentación de la API REST (pendiente de generar) |

**Leer siempre la documentación antes de escribir código.**

---

## Personas y cuentas

| Persona | Alias en código | Gmail principal | Observaciones |
|---|---|---|---|
| Hernan Rizzi | `GHR` | ghrizzi.goog@gmail.com | Cuenta principal de finanzas |
| Martha (esposa) | `MC` | malu82@gmail.com | Misma estructura que GHR |
| Sistema | `claude` | MCGHR.claude@gmail.com | Cuenta operativa del proyecto |

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

## Arquitectura en una línea

```
Fuentes (correos, PDFs, mobile) → ETL (finanzas_familia.py + Claude API)
→ SQLite (schema v1.1) → Backend (FastAPI) → Frontend (React PWA)
```

Ver `docs/architecture.md` para el diagrama completo y las decisiones de diseño.

---

## Stack tecnológico

- **Backend:** Python 3.11 + FastAPI + SQLAlchemy + SQLite
- **Frontend:** React 18 + Vite + Tailwind CSS + Zustand
- **ETL:** Python (finanzas_familia.py) + Claude API
- **Mobile:** PWA responsive instalable en iPhone (Safari y Chrome)
- **Despliegue:** Docker Compose (PC Windows o Raspberry Pi)
- **Sincronización mobile:** JSONs via OneDrive Personal

---

## Base de datos

Archivo: `OneDrive\Finanzas MCGHR\Generales\finanzas.db`  
Schema activo: v1.1 — ver `schema/finanzas_v1_1.sql` y `docs/schema_v1.md`

**Regla crítica:** NUNCA escribir datos financieros directamente en la BD ni en el Excel.
- Solo el ETL (`finanzas_familia.py`) y la API REST del backend escriben en SQLite
- El Excel se regenera desde SQLite con script dedicado
- Power BI conecta al Excel, no a SQLite directamente

---

## Entornos de prueba

Tres entornos aislados: `dev` (desarrollo diario), `test` (tests automatizados), `staging` (pre-release).
Nunca se usan datos reales de GHR/MC en entornos de prueba.

```bash
# Crear y poblar un entorno
python scripts/env/reset_env.py --env dev --volume minimal

# Correr tests
pytest tests/unit/ tests/integration/ -v
```

Ver `docs/testing_strategy.md` para la estrategia completa, scripts y datos dummy.

---

## Configuración

Toda la configuración vive en `config_correos.json` (local, nunca en el repo).

**Variables de entorno requeridas** (ver `.env.example`):
- `ANTHROPIC_API_KEY` — Claude API (console.anthropic.com)
- `OUTLOOK_APP_PASSWORD` — Contraseña de app Microsoft (account.microsoft.com)
- `DB_PATH`, `ONEDRIVE_PATH`, `BACKUP_PATH` — rutas del sistema

---

## Estado actual del proyecto (Junio 2026)

- [x] Schema v1.1 definido y documentado
- [x] ETL básico funcionando (`src/finanzas_familia.py`) — WIP, pendiente de commit
- [x] Skills: lector_correos, desproteger_pdf, auditor_correos
- [x] Especificación funcional completa (`docs/functional_spec.md`)
- [x] Arquitectura técnica definida (`docs/architecture.md`)
- [x] Estrategia de entornos y testing definida (`docs/testing_strategy.md`)
- [ ] Backend FastAPI — **próximo paso**
- [ ] Frontend React — pendiente
- [ ] PWA mobile — pendiente
- [ ] Backup/restore — pendiente
- [ ] Entorno dev (se crea con el primer módulo del backend)

**El próximo paso de desarrollo es el backend FastAPI**, comenzando por:
`/api/v1/transacciones/` y `/api/v1/transacciones/pendientes/`

---

## Reglas de desarrollo

1. **Leer los docs antes de escribir código** — la spec funcional y la arquitectura son la fuente de verdad
2. **Separación estricta UI/lógica** — el frontend nunca toca SQLite directamente
3. **El ETL es el único escritor del schema** (además de la API REST del backend)
4. **Sin hardcodeo** — ninguna ruta, credencial o config en el código
5. **Commits semánticos** — `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`
6. **Sin borrado físico** — los datos financieros solo se inactivan, nunca se borran
7. **Undo en el frontend** — toda acción del usuario es reversible hasta que graba explícitamente
8. **Nunca datos reales en pruebas** — tests y dev usan siempre datos dummy del seeder
9. **Tests antes de merge** — `pytest tests/unit/ tests/integration/` debe pasar en verde

---

## Módulos planificados (fases futuras)

| Módulo | Descripción | Fase |
|---|---|---|
| Obligaciones | Préstamos, alquiler, servicios públicos, recordatorios | Fase 2 |
| Inversiones | Acciones IBKR, inmuebles, patrimonio neto | Fase 2 |
| Analítica Claude | Análisis conversacional sobre datos financieros | Fase 2 |
| Autenticación | Login por usuario, encriptación de campos sensibles | Fase 3 |
| Proyecciones | Patrimonio neto a 12/24/60 meses | Fase 3 |

---

## Historial de decisiones clave

| Fecha | Decisión | Razón |
|---|---|---|
| Mayo 2026 | SQLite como BD principal | Escritura concurrente, portable, sin servidor |
| Mayo 2026 | IMAP para Hotmail | Conector OAuth M365 no funciona con cuentas personales |
| Mayo 2026 | Stage area + aprendizaje | Clasificación automática con supervisión humana |
| Junio 2026 | Schema v1.1 con doble entrada contable | Balance patrimonial real y trazabilidad completa |
| Junio 2026 | FastAPI sobre Flask | Async nativo, OpenAPI automático, mejor DX |
| Junio 2026 | React + Zustand para Undo | Estado complejo de sesión, stack Undo/Redo |
| Junio 2026 | PWA responsive sobre app nativa | Sin App Store, mismo código, menor mantenimiento |
| Junio 2026 | Flujo mobile via JSON en OneDrive | Sin depender de que la PC esté encendida |
| Junio 2026 | Backup completo (no incremental) | Simplicidad de restore; el tamaño no lo justifica |
| Junio 2026 | 3 entornos aislados (dev/test/staging) | Buenas prácticas SDLC, nunca datos reales en pruebas |

---
*Última actualización: Junio 2026 — Plataforma Financiera MCGHR*
