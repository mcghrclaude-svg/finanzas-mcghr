# Lecciones Aprendidas — Finanzas MCGHR
**Proposito:** Errores ya cometidos y decisiones ya tomadas. Leer ANTES de escribir codigo.

---

## Reglas criticas de desarrollo

1. Siempre leer el repo completo antes de escribir codigo
2. Los modelos SQLAlchemy estan en backend/models/ — no crear modelos paralelos
3. La Base real esta en backend/models/base.py (NO en database.py)
4. conftest.py DEBE importar todos los modelos explicitamente para que
   Base.metadata.create_all los detecte
5. Variables VITE_* NO van en .env.dev — van en frontend/.env.local
6. Nunca caracteres especiales en codigo — solo ASCII
7. Modulos nuevos van en frontend/src/modules/ NO en pages/
8. Tailwind puro — no CSS custom, no variables --color-*
9. Cada entrega incluye script instalador .ps1 con $SRC = $PSScriptRoot
10. Archivos con mismo nombre se entregan con nombres diferenciados
    (ej: backend_schemas_inbox.py no schemas.py)
11. Flujo: claude.ai genera -> PC valida -> fix en claude.ai (nunca al reves)
12. Siempre activar venv: venv\Scripts\activate
13. Scripts PS1: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
14. git pull antes de git push
15. El repo tiene dos DB: la real en OneDrive (NO tocar) y la de dev local

---

## Arquitectura ETL — decision critica (Junio 2026)

**El ETL no es un script Python que llama a Claude API.**

Despues de analizar las capacidades de Claude Desktop (/schedule), se decidio:

- El ETL es una **tarea programada de Claude Desktop**
- Usa los MCP tools configurados en la PC (sqlite, mcp_lector_correos, filesystem)
- Claude Desktop es el motor de razonamiento — no hay llamada a anthropic.Anthropic()
- Los skills Python (lector_correos.py, desproteger_pdf.py) son herramientas
  que Claude Desktop invoca via MCP, no el motor principal

**Por que:** Claude Desktop tiene scheduler nativo (/schedule), no requiere
suscripcion adicional de API, y puede razonar sobre casos ambiguos mejor que
un script deterministico con patrones regex.

**Implicacion:** `src/finanzas_familia.py` existente es codigo legado /
referencia. El ETL real sera el prompt de la tarea programada (Entrega 3B).

---

## ETL escribe directo a SQLite — no via API REST

El ETL usa `mcp__sqlite__*` para escribir directamente en `finanzas.db`.
No llama a los endpoints del backend.

**Por que:** el ETL debe poder correr a las 4am independientemente de si
el backend FastAPI esta levantado. Son procesos independientes.

**Implicacion:** la DB puede tener datos que el backend aun no expone. Eso
esta bien — el backend es read-mostly para el frontend.

---

## Correlacion de eventos — campo id_evento

El mismo hecho economico puede llegar por multiples canales:
- Notificacion del banco por correo (mismo dia)
- Factura adjunta en el correo (mismo dia)
- Linea en el extracto mensual (4 semanas despues)

Para no duplicar transacciones, el ETL genera un `id_evento` deterministico
(hash de monto + cuenta + fecha con tolerancia +/-3 dias + titular).

Si dos eventos tienen el mismo id_evento, el ETL enriquece la transaccion
existente en lugar de crear una nueva.

Campo `estado_enriquecimiento`: inicial -> enriquecido -> completo

Ver: docs/ETL_DISENO_FUNCIONAL.md seccion "Correlacion de eventos"

---

## PWA comunica via OneDrive, no via API

La PWA en el iPhone escribe JSONs en OneDrive. No llama a ningun endpoint
del backend. El ETL lee esos JSONs en la proxima ejecucion.

**Por que:** no requiere que la PC este encendida para registrar un gasto
desde el celular. El procesamiento ocurre en la siguiente corrida del ETL.

El backend si expone un endpoint `GET /api/v1/catalogos/export/pwa` pero
ese endpoint escribe en OneDrive — la PWA lee desde OneDrive, no desde la API.

---

## Modelo Transaccion — campos TODO pendientes

El modelo `backend/models/transaccion.py` tiene los modelos `Tramo` y `Asiento`
con TODO — campos incompletos. Completar antes de implementar el servicio
de transacciones.

El campo `completitud` en el modelo SQLAlchemy es `Numeric(3,2)` (numero 0.0-1.0)
pero en el schema SQL v1.1 es `TEXT` (minimo|parcial|completo). Usar el del
modelo SQLAlchemy — es mas preciso para calculos de prioridad en el inbox.

El modelo no tiene los campos nuevos de v1.2 (id_evento, estado_enriquecimiento).
Agregar en la entrega 3B junto con la migracion SQL.

---

## Inbox — tabla usada

El Inbox de revision humana usa la tabla `transacciones` directamente,
filtrando por `estado = 'pendiente'` y `revisado_humano = 0`.

La tabla `inbox_mobile` es distinta — es el registro de que JSONs de OneDrive
ya fueron procesados por el ETL (para no reprocesar). No es la cola de revision.

Confusion frecuente: el nombre "inbox_mobile" sugiere que es el inbox de la
app, pero es el log de procesamiento de archivos JSON de la PWA.

---

## Entorno PC — referencia

| Dato | Valor |
|---|---|
| OS | Windows 11 |
| Usuario | ghriz |
| Python a usar | py -3.12 (NO el 3.14 que es el default) |
| Repo | C:\Users\ghriz\finanzas-mcghr\ |
| venv backend | C:\Users\ghriz\finanzas-mcghr\venv\ |
| DB produccion | C:\Users\ghriz\OneDrive\Finanzas MCGHR\Generales\finanzas.db |

---

*Ultima actualizacion: Junio 2026 — Plataforma Financiera MCGHR*
