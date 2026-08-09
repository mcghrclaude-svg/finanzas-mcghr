# ESTADO_PROYECTO.md  -- actualizado post-sesion Agosto 2026
# Plataforma Financiera MCGHR

**Fecha:** 9 Agosto 2026
**Proposito:** Documento de handoff para retomar el proyecto en claude.ai con contexto completo.

---

## Que es este proyecto

Plataforma de gestion financiera familiar para GHR (Hernan) y MC (Martha).
Arquitectura de 5 capas:

1. **Capa 0  -- Base de datos:** SQLite en OneDrive (`finanzas.db`) con schema
   de doble entrada contable, multi-moneda. Schema v1.2 aplicado.
2. **Capa 1  -- ETL Claude Desktop:** Tarea programada diaria a las 4am.
   Procesa correos Gmail, PDFs en OneDrive y JSONs de la PWA.
   Escribe en SQLite via MCP sqlite.
3. **Capa 2  -- Backend FastAPI:** API REST en http://localhost:8000
4. **Capa 3  -- Frontend React:** http://localhost:3000
5. **Capa 4  -- PWA Mobile:** Pendiente (Entrega 4)

---

## Como arrancar el stack

```powershell
# Opcion 1  -- Script de arranque (recomendado)
powershell -ExecutionPolicy Bypass -File "C:\Users\ghriz\finanzas-mcghr\iniciar_finanzas.ps1"

# Opcion 2  -- Manual
# Terminal 1:
cd C:\Users\ghriz\finanzas-mcghr
venv\Scripts\python.exe -m uvicorn backend.main:app --reload --env-file .env.dev

# Terminal 2:
cd C:\Users\ghriz\finanzas-mcghr\frontend
npm run dev
```

URLs:
- App: http://localhost:3000
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## Estado por componente

### Base de datos

| Item | Estado |
|---|---|
| Schema v1.1 (22 tablas + 5 vistas) | COMPLETO |
| Schema v1.2 (+id_evento, +estado_enriquecimiento) | COMPLETO  -- aplicado en OneDrive |
| Seed catalogos (25 cat, 12 cuentas, 22 contrapartes, 2 personas) | COMPLETO |
| Seed inbox (8 transacciones dummy para dev) | LISTO  -- ejecutar manualmente |

### Capa 1  -- ETL (Claude Desktop)

| Item | Estado |
|---|---|
| Skills Python (lector_correos, desproteger_pdf, auditor) | COMPLETO |
| MCP server mcp_lector_correos | COMPLETO |
| Prompt tarea programada Claude Desktop | COMPLETO  -- docs/ETL_PROMPT_CLAUDE_DESKTOP.md |
| Tokens OAuth Gmail hernan | COMPLETO  -- confirmado con busquedas reales exitosas (sesiones de julio) |
| Tokens OAuth Gmail malu | COMPLETO  -- confirmado con busquedas reales exitosas (sesiones de julio) |
| Tarea programada configurada en Claude Desktop (4am) | PENDIENTE  -- accion manual |

### Capa 2  -- Backend FastAPI

| Item | Estado | Tests |
|---|---|---|
| Core: database, config, exceptions | COMPLETO |  -- |
| Modelos SQLAlchemy (catalogo, transaccion, regla, inbox_mobile) | COMPLETO |  -- |
| Router catalogos -- todos los endpoints ABM implementados | COMPLETO | 5/5 |
| Router catalogos export PWA | COMPLETO | 1/1 |
| Router inbox (7 endpoints) + soporte estado=all | COMPLETO | 13/13 |
| Schema inbox -- InboxItemPatch ampliado, TramoOut, InboxItemRead completo | COMPLETO |  -- |
| Repository inbox -- selectinload Tramo.cuenta_origen/destino, estado=None sin filtro | COMPLETO |  -- |
| Resto de routers (transacciones, presupuestos, etc.) | TODO  -- placeholder |  -- |

**Total tests pasando: 55/55**

### Capa 3  -- Frontend React

| Item | Estado |
|---|---|
| Estructura Vite + Tailwind + Zustand + React Query | COMPLETO |
| Layout + Sidebar + Header | COMPLETO |
| Modulo Catalogos -- ABM funcional (fix endpoints backend) | COMPLETO |
| Modulo Transacciones v6 | COMPLETO  -- ver detalle abajo |
| Dashboard | TODO  -- placeholder |
| Resto de modulos | TODO  -- placeholder |

**Modulo Transacciones v6 -- detalle:**

| Feature | Estado |
|---|---|
| Lista izquierda con ancho ajustable por drag | COMPLETO |
| Panel detalle grid 4 columnas sin scroll | COMPLETO |
| Campos editables: descripcion, fecha, tipo, quien_pago, es_recurrente, counterpart, category, paid_with, es_reembolsable, estado_reembolso, notas | COMPLETO |
| AutocompleteSelect (typeahead) en Category, Counterpart y Paid With | COMPLETO |
| Paid With vinculado a id_cuenta_origen del tramo 1 | COMPLETO |
| Toolbar: filtro All Sources | COMPLETO |
| Toolbar: filtro All People (filtra por quien_pago) | COMPLETO |
| Toolbar: filtro fecha desde/hasta | COMPLETO |
| Toolbar: sort by date/amount asc/desc | COMPLETO |
| Toolbar: boton Clear filters | COMPLETO |
| Toggle All/Pending -- fix: All muestra todos los estados | COMPLETO |
| Attachment: preview compacto con boton abrir en nueva ventana | COMPLETO |
| Campos ocultos (no en UI): para_quien, id_correo | DECISION  -- ocultos por ahora |

**Archivos Frontend:**

| Archivo | Estado |
|---|---|
| `frontend/src/modules/Transacciones/index.jsx` | ACTUALIZADO  -- v6 + fix #47, ver detalle arriba |
| `frontend/src/modules/Catalogos/index.jsx` | SIN CAMBIOS  -- funciona con fix de backend |

**Archivos Frontend modificados en sesion 2026-07-05 (fix Issue #47 / PEN-008):**

| Archivo | Cambio |
|---|---|
| `frontend/src/modules/Transacciones/index.jsx` | Fix: `DetailPanel` invoca `onRecargar` (la `cargar()` del padre) tras confirmar una EP, para que el array `items` no quede obsoleto y la contraparte confirmada no se pierda al renavegar entre transacciones |

**Archivos modificados en sesion 2026-07-07 (ajustes UX Tools + Catalogs V2, branch chat-Ajustes_ux_2):**

| Archivo | Cambio |
|---|---|
| `frontend/src/modules/Tools/index.jsx` | Fix: cards de Tools arrancan colapsadas por default (antes expandidas). Se elimina la variante visual `danger` (fondo/borde rojo) de Reset Total y Restore -- todas las cards quedan con la paleta neutra |
| `frontend/src/modules/Tools/CatalogsV2.jsx` | Nuevo: pagina de editor de categorias en arbol (estilo regedt32), ruteada en `/catalogos-v2`, item propio del sidebar bajo Settings (solo dev). Panel izquierdo con jerarquia (expand/collapse, arranca colapsado), panel derecho con detalle + edicion. Por nodo: agregar hija (deshabilitado en nivel 3) e inactivar (deshabilitado si tiene hijas activas). Fix aplicado en la misma sesion: scroll independiente por panel (antes scrolleaba la pagina completa) |
| `frontend/src/modules/Catalogos/categoriaConfig.js` | Nuevo: extrae `generarSlug`/`generarSlugUnico` y `CAMPOS_CATEGORIAS` de `Catalogos/index.jsx` a un archivo compartido, usado tanto por Catalogos (vista clasica, sin cambio de comportamiento) como por CatalogsV2 |
| `frontend/src/modules/Catalogos/index.jsx` | Refactor: usa `categoriaConfig.js` en vez de definir `generarSlug`/`CAMPOS.categorias` localmente. Sin cambio de comportamiento |
| `frontend/src/App.jsx` | Nueva ruta `/catalogos-v2` (solo dev), junto a `/tools` |
| `frontend/src/components/layout/Sidebar.jsx` | Nuevo item "Catalogs V2" en el grupo Settings, debajo de Tools (solo dev) |
| `backend/api/v1/routers/catalogos.py` | `DELETE /categorias/{id}` (inactivar) ahora valida que la categoria no tenga hijas **activas** antes de desactivar; devuelve 409 si tiene |

Pendiente para una sesion futura (registrado como issues, no bloquea esta sesion): mover `CatalogsV2.jsx` a su propio modulo por ADR-007 ([#49](https://github.com/mcghrclaude-svg/finanzas-mcghr/issues/49)); drag and drop para reparentar categorias ([#50](https://github.com/mcghrclaude-svg/finanzas-mcghr/issues/50)).

**Archivos Backend modificados en sesion 2026-06-29:**

| Archivo | Cambio |
|---|---|
| `backend/api/v1/routers/catalogos.py` | Fix: todos los endpoints POST/PATCH/DELETE implementados (antes eran stubs vacios) |
| `backend/api/v1/routers/inbox.py` | Fix: estado=all no filtra por estado; expone tramos con cuenta_origen/destino |
| `backend/schemas/inbox.py` | Ampliado: TramoOut, InboxItemRead con tramos y campos nuevos, InboxItemPatch con todos los campos editables |
| `backend/repositories/inbox_repository.py` | Fix: selectinload de cuentas en tramos; listar() acepta estado=None |
| `docs/CITA.md` | Actualizado: CITA-009 agrega excepcion para texto visible en UI (botones, iconos JSX) |

### Capa 4  -- PWA Mobile

| Item | Estado |
|---|---|
| Formato JSON OneDrive documentado | COMPLETO  -- docs/ETL_DISENO_FUNCIONAL.md |
| carpeta OneDrive/PWA/ creada | COMPLETO |
| catalogos.json generado por backend | DESACTUALIZADO  -- POST /catalogos/export/pwa produce `{categorias, contrapartes, cuentas}` con `{id, nombre}`; la PWA nueva (pwa-gastos/) espera `{categorias, medios_de_pago, monedas}` con `{id, etiqueta}`, incluyendo un catalogo de moneda que todavia no existe en el backend. Ver detalle en "Pendiente: backend PC" abajo |
| Codigo PWA (React instalable en iPhone) -- `pwa-gastos/`, branch `chat-pwa-gastos` | PARCIAL  -- funcional de punta a punta en localhost, ver detalle abajo |

**PWA (`pwa-gastos/`) -- detalle, sesion 2026-08-09:**

| Feature | Estado |
|---|---|
| Login MSAL (loginRedirect, scope Files.ReadWrite.All, cuentas personales) | COMPLETO  -- probado en localhost con cuenta Microsoft real |
| Selector de carpetas de OneDrive (raiz de gastos, catalogos, resumen) | COMPLETO  -- selector propio sobre Graph API, no el widget oficial de Microsoft. Ver ADR-014 y CITA-014 |
| Alta de gasto (fecha, categoria/moneda/medio de pago con busqueda, monto, quien, foto con compresion) | COMPLETO |
| Botones Limpiar / Grabar y Cerrar / Grabar y Nuevo + mensaje de confirmacion/error de altura fija | COMPLETO |
| Moneda y medio de pago por default (Configuracion), precargados y editables en cada alta | COMPLETO  -- mismo patron que usuario por default |
| Guardado local (IndexedDB, sin campo de estado -- presencia = pendiente) | COMPLETO |
| Sincronizacion IndexedDB -> OneDrive (JSON + foto, borra al exito) | COMPLETO  -- probado con datos de ejemplo; subida real a una carpeta configurada todavia no probada de punta a punta |
| Ver gastos pendientes (listado + borrar) | COMPLETO |
| Resumen del mes | PENDIENTE (por diseno)  -- placeholder deshabilitado, formato del JSON de resumen no definido todavia |
| PWA instalable (manifest + service worker, vite-plugin-pwa) | COMPLETO |
| Workflow GitHub Actions (build + deploy a GitHub Pages) | COMPLETO  -- creado, no ejecutado todavia |
| Deploy real a GitHub Pages | PENDIENTE  -- accion manual, ver tabla de acciones pendientes abajo |
| Prueba en iPhone real (Safari, instalada como PWA) | PENDIENTE |

**Pendiente: backend PC para la PWA (no arranco):**

| Item | Estado |
|---|---|
| Script Python que lee `pendientes/`, valida contra schema real, inserta en Inbox, mueve a `procesados/` | PENDIENTE  -- no arranco |
| Exportador de catalogos actualizado (medios_de_pago desde `cuentas`, catalogo real de moneda) | PENDIENTE  -- no arranco. El export actual no coincide con el contrato que espera la PWA nueva (ver fila de arriba) |
| Generador de JSON de resumen mensual | PENDIENTE  -- formato todavia no definido |

---

## Roadmap

### Punto 3  -- ETL + Inbox

| Entrega | Descripcion | Estado |
|---|---|---|
| 3A | Backend inbox: service, repo, router, tests | COMPLETO |
| 3B | Schema v1.2 + prompt ETL Claude Desktop | COMPLETO |
| 3C | Frontend Inbox + export catalogos PWA | COMPLETO |
| 3D | UX Transacciones v6 + fix catalogos ABM | COMPLETO  -- sesion 2026-06-29 |

### Punto 4  -- PWA Mobile

| Entrega | Descripcion | Estado |
|---|---|---|
| 4A | PWA React: captura rapida de gastos desde iPhone | PARCIAL  -- funcional en localhost (ver Capa 4 arriba), pendiente deploy a GitHub Pages y prueba en iPhone real |
| 4B | Integracion con ETL via OneDrive (script Python de PC + exportador de catalogos actualizado) | PENDIENTE  -- no arranco |

### Punto 5  -- Completar routers backend (futuro)

Transacciones, presupuestos, obligaciones, inversiones, reportes, dashboard real.

---

## Decisiones de arquitectura (Junio 2026)

| Decision | Resultado | Razon |
|---|---|---|
| Motor del ETL | Claude Desktop tarea programada (no script Python) | Sin costo adicional API, razonamiento sofisticado, scheduler nativo |
| Schedule ETL | Diario a las 4am | Peticion del usuario |
| ETL escribe en DB | Directo a SQLite via MCP sqlite | Independiente del backend |
| Aprendizaje ETL | Lee reglas_clasificacion + ultimas 50 tx confirmadas como contexto | Mas preciso que solo regex |
| Correlacion eventos | Campo id_evento en transacciones (asignado por el ETL al correlacionar, no un hash precalculado) | Unifica notificacion + factura + extracto en una sola tx |
| Enriquecimiento | Campo estado_enriquecimiento (inicial/enriquecido/completo) | Seguimiento del ciclo contable |
| Catalogos para PWA | Backend exporta JSON a OneDrive, PWA lo lee desde ahi | Sin llamadas API desde el celular |
| PWA comunicacion | JSONs en OneDrive, sin API calls | Sin servidor adicional |
| Script arranque | iniciar_finanzas.ps1 en raiz del repo | Un click desde barra de tareas |
| Paid With en inbox | Vinculado a id_cuenta_origen del tramo 1. Multi-tramo: aviso readonly | Mayoria de gastos tiene 1 tramo |
| para_quien en UI | Oculto del formulario de detalle | Decision de UX -- no se usa por ahora |
| id_correo en UI | Oculto del formulario de detalle | Campo interno, no relevante para el usuario |
| Simbolos Unicode en UI | Permitidos en texto visible (botones, iconos JSX). Ver CITA-009 | ASCII solo para logica, comentarios y nombres |

---

## Acciones manuales pendientes (por el usuario)

| # | Accion | Instrucciones |
|---|---|---|
| 1 | Seed inbox en DB dev | Ver instrucciones en docs/INSTRUCCIONES_POST_INSTALACION.md |
| 2 | Configurar tarea ETL en Claude Desktop | Ver docs/ETL_CONFIGURACION_CLAUDE_DESKTOP.md |
| 3 | Agregar script arranque a barra de tareas | Ver instrucciones en docs/INSTRUCCIONES_POST_INSTALACION.md |
| 4 | Habilitar GitHub Pages para pwa-gastos | Settings > Pages > Source: GitHub Actions (una sola vez) |
| 5 | Agregar Redirect URI de produccion en Azure Portal | Despues del primer deploy, agregar `https://mcghrclaude-svg.github.io/finanzas-mcghr/` (con barra final) al App Registration `GastosApp-MCGHR` |
| 6 | Probar pwa-gastos en iPhone real | Desde Safari, "Agregar a pantalla de inicio", probar login/selector/alta/sync con cuenta Microsoft real (GHR y luego MC) |

Tokens OAuth Gmail (hernan y malu): resuelto -- confirmado con busquedas reales exitosas en ambas cuentas (sesiones de julio 2026).

---

## Issues abiertos

| # | Titulo | Prioridad |
|---|---|---|
| #4 | Configurar autoforward iPhone Martha | MEDIA |
| #5 | Regenerar token GitHub | URGENTE |
| #8 | Configurar tarea programada ETL Claude Desktop | ALTA |
| #9 | Implementar routers backend pendientes | MEDIA |
| #10 | PWA Mobile  -- Entrega 4 | BAJA |

---

## Lo que NO esta en el repo (por seguridad)

| Archivo | Ubicacion en PC | Razon |
|---|---|---|
| `config_correos.json` | `C:\Users\ghriz\.claude\` | Credenciales  -- en .gitignore |
| Tokens OAuth Gmail | `C:\Users\ghriz\.gmail-mcp\tokens\` | Tokens sensibles |
| `finanzas.db` | OneDrive | DB con datos reales  -- en .gitignore |
| `.env` / `.env.prod` | raiz del repo local | Variables con valores reales |

---

## Sesion 2026-07-07 (tarde) -- Sync de documentacion con estado real

Limpieza de documentacion (sin cambios de logica ni comportamiento),
verificada contra el codigo real antes de cada correccion. Mergeada a
main en el commit `36a7bef` (branch `docs/sync-estado-real-proyecto`).

**Archivos corregidos (8):**

| Archivo | Cambio |
|---|---|
| `README.md` | Estructura del repo actualizada (backend/, frontend/, src/, tests/, Docker); checklist refleja stack real FastAPI + React |
| `docs/schema_v1.md` | Estado actualizado a implementado; referencia a `finanzas_v1_4b.sql` como version vigente; agregada tabla `entidades_potenciales` (faltaba en el mapa y en el detalle) |
| `docs/ETL_DISENO_FUNCIONAL.md` | Seccion de entidades potenciales corregida para describir el mecanismo real (tabla separada `entidades_potenciales`, no insercion directa en catalogo); comentario de `id_evento` corregido en dos lugares (ya no se describe como hash determinista) |
| `schema/finanzas_v1_2.sql` | Comentario de `id_evento` corregido (asignado por el ETL al correlacionar, no un hash precalculado) -- solo el comentario, DDL sin cambios |
| `docs/ESTADO_PROYECTO.md` | Titulo corregido a Julio 2026; tabla de decisiones (id_evento) corregida; tokens OAuth Gmail (hernan y malu) marcados resueltos |
| `docs/PENDIENTES.md` | PEN-004 marcado resuelto para la implementacion base (schema/backend/UX), con nota de gap abierto no bloqueante sobre el chequeo de correlacion en el seed |

---

## Documentacion del Punto 3

| Documento | Contenido |
|---|---|
| `docs/ETL_DISENO_FUNCIONAL.md` | Flujo completo, correlacion eventos, clasificacion |
| `docs/ETL_PROMPT_CLAUDE_DESKTOP.md` | Prompt completo de la tarea programada del ETL |
| `docs/ETL_CONFIGURACION_CLAUDE_DESKTOP.md` | Como configurar la tarea en Claude Desktop |
| `docs/DISENO_3A_INBOX_BACKEND.md` | Endpoints inbox, logica, aprendizaje |
| `docs/DISENO_3B_ETL_PROMPT.md` | Schema v1.2, diseno del prompt |
| `docs/DISENO_3C_FRONTEND_INBOX_PWA.md` | Frontend Inbox, export catalogos, formato PWA |
| `docs/INSTRUCCIONES_POST_INSTALACION.md` | Pasos manuales pendientes con instrucciones detalladas |

---

*Ultima actualizacion: 9 Agosto 2026  -- Sesion PWA de captura de gastos, primera etapa funcional (branch chat-pwa-gastos, pendiente de mergear a main)*
