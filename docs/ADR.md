# ADR -- Architecture Decision Records
# Finanzas MCGHR

Registro de decisiones de arquitectura del proyecto.
Actualizado automaticamente por cerrar-sesion.ps1 al cierre de cada sesion.

Origen posible: INSTRUCCION-HERNAN | SUPUESTO-AGENTE | CONSENSO
Estado posible: ACTIVA | REEMPLAZADA-POR-ADR-XXX | CUESTIONADA

---

## ADR-001 -- Motor del ETL es Claude Desktop con tarea programada

**Fecha:** 2026-06-17
**Estado:** ACTIVA
**Origen:** INSTRUCCION-HERNAN

**Contexto:**
El proyecto necesita procesar correos, PDFs y extractos bancarios periodicamente.
La opcion inicial era un script Python standalone que llamaba a Claude API.
Hernan no quiere una suscripcion adicional a Claude API.

**Decision:**
El ETL es una tarea programada de Claude Desktop (Cowork), no un script Python.
Claude Desktop usa los MCP tools configurados (Gmail, filesystem, SQLite) para
leer fuentes, clasificar y escribir en la DB. Corre todos los dias a las 4am.

**Alternativas descartadas:**
- Script Python + Claude API: descartado por costo adicional de suscripcion
- Script Python standalone sin LLM: descartado por incapacidad de clasificar casos ambiguos

**Consecuencias:**
- El ETL no puede correr desatendido en un servidor sin Claude Desktop activo
- La clasificacion se beneficia del razonamiento del LLM en lugar de reglas fijas
- No hay costo adicional de API por el procesamiento del ETL

**Evidencia:** Chat "Completar ETL de transacciones bancarias y correos", sesion junio 2026

---

## ADR-002 -- Base SQLAlchemy vive en models/base.py

**Fecha:** 2026-06-15
**Estado:** ACTIVA
**Origen:** SUPUESTO-AGENTE (error que rompio el proyecto)

**Contexto:**
Al generar el primer backend, el agente creo una Base en core/database.py.
El repo ya tenia una Base en backend/models/base.py de la que heredaban todos los modelos.
El resultado fue dos instancias de Base incompatibles: create_all no veia las tablas reales.

**Decision:**
La unica Base de SQLAlchemy es backend/models/base.py.
core/database.py solo maneja el engine y la session, nunca define Base.
conftest.py debe importar todos los modelos explicitamente antes de create_all.

**Alternativas descartadas:**
- Unificar en core/database.py: descartado porque rompia los imports existentes

**Consecuencias:**
- Todo modelo nuevo debe heredar de backend.models.base.Base
- conftest.py es critico: si falta un import de modelo, la tabla no existe en tests
- El error "no such table" en tests casi siempre es un import faltante en conftest.py

**Evidencia:** Chat sesion junio 2026, error ImportError ReglaClasificacion

---

## ADR-003 -- ETL escribe directo a SQLite, no via API REST

**Fecha:** 2026-06-17
**Estado:** ACTIVA
**Origen:** INSTRUCCION-HERNAN (recomendacion del agente aceptada)

**Contexto:**
El ETL necesita escribir transacciones en la DB. La opcion era escribir via la API
REST del backend o directo a SQLite via MCP sqlite.

**Decision:**
El ETL escribe directo a SQLite via MCP sqlite tool de Claude Desktop.
No requiere que el backend este corriendo al mismo tiempo.

**Alternativas descartadas:**
- Escritura via API REST: descartada porque el ETL corre a las 4am cuando el backend
  puede no estar activo, y agrega dependencia de red innecesaria para un proceso local

**Consecuencias:**
- El ETL y el backend son independientes en tiempo de ejecucion
- El modo WAL de SQLite maneja la concurrencia entre ambos
- Si el schema cambia, hay que coordinar migracion entre el modelo del backend y el ETL

**Evidencia:** Chat "Completar ETL", sesion junio 2026

---

## ADR-004 -- Frontend usa Tailwind puro, sin CSS custom

**Fecha:** 2026-06-15
**Estado:** ACTIVA
**Origen:** CONSENSO (descubierto al ver que los estilos no compilaban)

**Contexto:**
El agente genero el primer modulo de Catalogos con CSS custom y variables --color-*.
Al renderizar, no se aplicaba ningun estilo. La causa raiz fue que faltaba
postcss.config.js, pero al investigar se descubrio que el Dashboard tampoco usaba
CSS custom sino Tailwind.

**Decision:**
Todo el frontend usa Tailwind puro: clases de utilidad directamente en JSX.
Prohibido: CSS custom, variables --color-*, archivos .css por modulo,
style={{}} inline con colores hardcodeados.

**Alternativas descartadas:**
- CSS Modules: descartado por inconsistencia con el resto del proyecto
- Variables CSS globales: descartado porque Tailwind ya provee el sistema de design tokens

**Consecuencias:**
- postcss.config.js es requerido para que Tailwind compile (ya existe en el repo)
- La paleta de colores es la definida en tailwind.config.js (primary-*, gray-*, etc.)
- Clases dinamicas deben estar hardcodeadas en el JSX para que JIT las detecte

**Evidencia:** Commit 8fe28bb, chat sesion junio 2026

---

## ADR-005 -- Variables VITE_* van en frontend/.env.local

**Fecha:** 2026-06-15
**Estado:** ACTIVA
**Origen:** SUPUESTO-AGENTE (error que rompio el backend)

**Contexto:**
El agente puso variables VITE_* en .env.dev junto con las variables del backend.
El Settings de pydantic-settings tiene extra="forbid" implicito y rechazo las
variables VITE_* con un error de validacion que impedia arrancar el backend.

**Decision:**
Las variables del backend van en .env.dev (db_path, env, etc.).
Las variables del frontend (VITE_*) van EXCLUSIVAMENTE en frontend/.env.local.
frontend/.env.local no se commitea (esta en .gitignore).

**Alternativas descartadas:**
- Un solo archivo .env: descartado porque Settings del backend rechaza variables VITE_*

**Consecuencias:**
- Al configurar una PC nueva hay que crear frontend/.env.local manualmente
- VITE_USE_MOCK y VITE_API_URL nunca van en archivos commiteados

**Evidencia:** Chat sesion junio 2026, error pydantic validation

---

## ADR-006 -- IDs de catalogos autogenerados como slug

**Fecha:** 2026-06-17
**Estado:** ACTIVA
**Origen:** INSTRUCCION-HERNAN

**Contexto:**
El primer modulo de Catalogos pedia al usuario que ingresara el ID manualmente
(ej: "BCO-CC-GHR"). Hernan indico que el ID es un campo interno de la app,
no relevante para el usuario.

**Decision:**
Los IDs de todas las entidades de catalogos se autogeneran como slug del nombre.
Para evitar duplicados: SLUG-{4 chars aleatorios} si ya existe un slug igual.
El campo ID no se muestra en tablas ni se pide en formularios de alta.

**Alternativas descartadas:**
- UUID: descartado porque los IDs existentes en el seed son legibles (BCO-CC-GHR)
  y cambiarlos rompia la consistencia con datos ya cargados
- ID manual: descartado por instruccion explicita de Hernan

**Consecuencias:**
- Los IDs del seed existente (BCO-CC-GHR, NETFLIX, etc.) se mantienen tal cual
- Solo los IDs de entidades nuevas creadas desde la UI se autogeneran

**Evidencia:** Chat UX sesion junio 2026

---

## ADR-007 -- Modulos nuevos van en frontend/src/modules/

**Fecha:** 2026-06-15
**Estado:** ACTIVA
**Origen:** SUPUESTO-AGENTE (pages/ quedo como legacy no intencionado)

**Contexto:**
El agente genero el primer Dashboard en frontend/src/pages/Dashboard.jsx.
App.jsx importaba desde modules/Dashboard que era un stub vacio.
El resultado fue una inconsistencia entre el archivo real y el que usaba la app.

**Decision:**
Todos los modulos van en frontend/src/modules/NombreModulo/index.jsx.
frontend/src/pages/ es legacy y no recibe modulos nuevos.
App.jsx importa siempre desde modules/.

**Alternativas descartadas:**
- Mantener pages/ como ubicacion principal: descartado porque App.jsx ya apuntaba a modules/

**Consecuencias:**
- pages/Dashboard.jsx existe como legacy pero no la usa nadie
- Si se crea un modulo nuevo, va en modules/ sin excepcion
- La carpeta pages/ puede eliminarse en una limpieza futura

**Evidencia:** Commit b3ccbb7, chat sesion junio 2026

---

## ADR-008 -- completitud en transacciones es TEXT, no Numeric

**Fecha:** 2026-06-20
**Estado:** ACTIVA
**Origen:** SUPUESTO-AGENTE (error que genero 5 issues de deuda tecnica)

**Contexto:**
El modelo SQLAlchemy original definia completitud como Numeric(3,2).
La DB real lo tenia como TEXT con valores 'minimo', 'parcial', 'completo'.
El agente genero codigo que comparaba completitud < 0.6 y usaba float(),
que fallaba con TypeError en runtime.

**Decision:**
completitud es TEXT con exactamente tres valores posibles: 'minimo', 'parcial', 'completo'.
En frontend: ordenamiento y colores basados en un mapa
{minimo: 0, parcial: 1, completo: 2}, nunca parseando a float.
En backend: comparaciones como strings, nunca como numeros.

**Alternativas descartadas:**
- Migrar la DB a Numeric: descartado porque los datos existentes son strings
  y la semantica de 'minimo'/'parcial'/'completo' es mas clara que 0.3/0.6/1.0

**Consecuencias:**
- Issue #26 cerrado (commit 50b07a3)
- Cualquier query que filtre por completitud usa WHERE completitud = 'minimo'
- El frontend nunca usa parseFloat() ni comparaciones numericas sobre este campo

**Evidencia:** Issues #23-#27, commits sesion junio 2026

---

## ADR-009 -- Scripts PS1 usan ErrorActionPreference Continue, no Stop

**Fecha:** 2026-06-22
**Estado:** ACTIVA
**Origen:** SUPUESTO-AGENTE (error repetido en multiples scripts)

**Contexto:**
El agente genero scripts con $ErrorActionPreference = "Stop" a nivel global.
Cuando un comando git falla (porque el script corre fuera del repo),
Stop detiene el script antes de llegar al Read-Host de fallback.
El usuario ve un error rojo y el script no llega a pedir la ruta del repo.

**Decision:**
Los scripts PS1 usan $ErrorActionPreference = "Continue" a nivel global.
Los comandos que pueden fallar (especialmente git fuera del repo) se envuelven
en try-catch con verificacion de $LASTEXITCODE.
Read-Host siempre tiene un default explicito entre corchetes.

**Alternativas descartadas:**
- Stop con try-catch en cada comando: descartado por verbosidad y porque es facil olvidar
  un comando sin su try-catch

**Consecuencias:**
- Los errores no fatales no detienen el script
- El patron obligatorio para deteccion del repo es:
  try { $r = git rev-parse... } catch {}; if (-not $r) { $r = Read-Host "... [default]" }

**Evidencia:** Chat sesion junio 2026, error instalar-hook.ps1

---

## ADR-010 -- Chats paralelos usan branches git por tema

**Fecha:** 2026-06-22
**Estado:** ACTIVA
**Origen:** INSTRUCCION-HERNAN

**Contexto:**
Hernan trabaja con chats paralelos para temas distintos (UX, backend).
Ambos chats commiteaban sobre main, generando pisadas accidentales.
Un git add -A mezclo cambios de UX con fixes de backend en un solo commit.

**Decision:**
Cada chat de un tema especifico trabaja sobre una branch dedicada: chat-ux, chat-backend, etc.
Al terminar la sesion, chequear-conflictos.ps1 valida que no hay solapamiento
de archivos antes de mergear a main.
El merge a main lo decide Hernan despues de ver el resultado del chequeo.

**Alternativas descartadas:**
- Un solo chat para todo: descartado porque los chats se llenan y pierden contexto
- Ambos sobre main con coordinacion manual: descartado porque fallo en la practica

**Consecuencias:**
- iniciar-chat-tema.ps1 crea o actualiza la branch del tema
- chequear-conflictos.ps1 detecta solapamiento automaticamente
- Hernan no necesita entender git para usar el flujo, solo correr los scripts

**Evidencia:** Chat sesion junio 2026 (este chat)

---

## ADR-011 -- conftest.py importa todos los modelos explicitamente

**Fecha:** 2026-06-15
**Estado:** ACTIVA
**Origen:** SUPUESTO-AGENTE (error "no such table" en tests)

**Contexto:**
El conftest.py original importaba Base desde backend.core.database.
Los modelos heredan de backend.models.base.Base.
Son dos instancias distintas de Base: create_all sobre la primera
no registraba las tablas de los modelos reales.

**Decision:**
conftest.py importa explicitamente TODOS los modelos antes del create_all:
from backend.models import catalogo, transaccion, presupuesto, etc.
Esto fuerza el registro de cada modelo en la Base correcta antes de crear tablas.

**Alternativas descartadas:**
- Import de Base desde models/__init__.py solamente: descartado porque
  si falta un modelo en __init__.py la tabla no aparece y el error es silencioso

**Consecuencias:**
- Cada vez que se agrega un modelo nuevo, hay que agregarlo al import de conftest.py
- El error "no such table" en tests es siempre sintoma de un import faltante aqui

**Evidencia:** Chat sesion junio 2026, fix conftest

---

## ADR-012 -- Correlacion de eventos ETL via campo id_evento

**Fecha:** 2026-06-17
**Estado:** ACTIVA
**Origen:** CONSENSO

**Contexto:**
Un mismo hecho economico (ej: compra con TC) llega por multiples canales:
notificacion SMS, factura adjunta en correo, linea en extracto mensual.
Sin correlacion, el ETL registraria tres transacciones en lugar de una.

**Decision:**
El campo id_evento en la tabla transacciones (TEXT, nullable) agrupa eventos
del mismo hecho economico. El ETL lo genera como hash de monto+fecha+cuenta
con tolerancia de +-1 dia. Cuando llega un evento nuevo, busca transacciones
con el mismo id_evento y las enriquece en lugar de crear una nueva.
El campo estado_enriquecimiento ('inicial','enriquecido','completo') indica
si la transaccion todavia espera mas datos de otros canales.

**Alternativas descartadas:**
- Correlacion manual por el usuario: descartado por friction excesiva
- Sin correlacion (registrar todos los eventos): descartado porque duplica datos

**Consecuencias:**
- Migracion schema v1.2 agrego id_evento y estado_enriquecimiento (commit 1011491)
- El ETL puede enriquecer transacciones existentes, no solo crear nuevas
- Un gasto con TC no genera movimiento de caja hasta que se paga el extracto

**Evidencia:** Chat ETL sesion junio 2026, schema/finanzas_v1_2.sql
