# CHANGELOG

## [0.2.1] - 2026-06-15

### fix: Tailwind no compilaba en el frontend

- Agrega `frontend/postcss.config.js` (faltaba — causa raiz del problema)
- Reescritura de modulo Catalogos en Tailwind puro (sin CSS custom)
- `CategoriaTree`, `TablaGenerica`, `ModalForm`, `ModalConfirm` usan clases Tailwind consistentes con el Dashboard
- Migracion de `pages/Dashboard.jsx` a `modules/Dashboard/index.jsx` con subcomponentes Tailwind

---

## [0.2.0] - 2026-06-15

### feat: modulo de gestion de catalogos maestros (Punto 1)

#### Backend
- `backend/api/v1/routers/catalogos.py` — CRUD completo para categorias, cuentas,
  contrapartes y personas. Reemplaza los endpoints vacios (TODO) que existian.
  Regla de soft-delete aplicada en todos los endpoints.
- `backend/schemas/catalogos.py` — Schemas Pydantic alineados con los modelos reales.
  Validacion de IDs (regex mayusculas), niveles de categoria (1-3), patrones de gasto.
- `backend/repositories/catalogos_repo.py` — Capa de acceso a datos. Arbol de categorias
  construido manualmente desde lista plana (el modelo no tiene relationship "hijos").
  Inactivacion en cascada para hijos y nietos de una categoria.

#### Seed
- `scripts/seed/seed_catalogos.py` — Datos maestros iniciales: 2 personas (GHR, MC),
  25 categorias en 3 niveles, 12 cuentas bancarias reales, 22 contrapartes frecuentes,
  10 reglas de clasificacion base. Fix: importa ReglaClasificacion (no Regla).

#### Tests
- `tests/conftest.py` — Fix critico: importa todos los modelos explicitamente antes
  de create_all, resuelve el problema de tablas no encontradas en tests.
- `tests/integration/test_catalogos.py` — 22 tests de integracion, todos en verde.
  Cubre CRUD, validaciones, filtros, inactivacion y cascada.

#### Frontend
- `frontend/src/modules/Catalogos/index.jsx` — Modulo principal de catalogos con
  navegacion lateral, stats bar, busqueda y filtros. Tailwind + react-hot-toast.
- `frontend/src/modules/Catalogos/CategoriaTree.jsx` — Arbol jerarquico con
  expand/collapse por nivel.
- `frontend/src/modules/Catalogos/TablaGenerica.jsx` — Tabla reutilizable para
  cuentas, contrapartes y personas con acciones en hover.
- `frontend/src/modules/Catalogos/ModalForm.jsx` — Modal de alta/edicion generico
  con campos configurables por entidad.
- `frontend/src/modules/Catalogos/ModalConfirm.jsx` — Dialogo de confirmacion
  para inactivar/activar registros.
- `frontend/src/api/catalogos.js` — Cliente API para todos los endpoints de catalogos.

#### Configuracion
- `.env.dev` — Separacion de variables backend (ENV, DB_PATH, etc.) y frontend
  (VITE_*). Las variables VITE_* van en frontend/.env.local.
- `frontend/.env.local` — Variables de entorno del frontend (no va al repo).

### fix: bugs criticos en el repo existente
- `backend/models/__init__.py` — Corrige ImportError: importaba `Regla` pero la
  clase se llama `ReglaClasificacion`. El backend no arrancaba.

### docs
- `docs/PRUEBAS_PUNTO1.md` — Instrucciones de prueba para el Punto 1.
- `docs/SETUP_DEV_MAESTROS.md` — Setup del entorno de desarrollo.

---

## Issues resueltos en esta sesion

- #REGLA-IMPORT — ImportError en backend/models/__init__.py: Regla vs ReglaClasificacion
- #ENV-SPLIT — Variables VITE_* causaban ValidationError en pydantic Settings
- #CONFTEST-TABLES — Tests fallaban con "no such table" por Base incorrecta en conftest
- #CAT-HIJOS — AttributeError en Categoria.hijos: el modelo no define relationship,
  se resuelve construyendo el arbol manualmente desde lista plana

## Issues pendientes para proximas sesiones

- #19 ASCII — Limpiar caracteres especiales de archivos Python existentes
- #20 ON-EVENT-DEPRECATED — backend/main.py usa on_event (deprecated). Migrar a lifespan.
- #21 FRONTEND-MOCK — Modulo Catalogos no tiene modo mock. Agregar VITE_USE_MOCK.
- #22 LF-CRLF — Configurar .gitattributes para line endings en Windows.
- POSTCSS-TYPE — Agregar "type": "module" a frontend/package.json.
