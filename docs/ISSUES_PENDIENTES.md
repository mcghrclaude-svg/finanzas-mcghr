# Issues pendientes — Finanzas MCGHR
**Ultima actualizacion:** Junio 2026

Este archivo refleja los issues abiertos en GitHub. Ver tambien: https://github.com/mcghrclaude-svg/finanzas-mcghr/issues

---

## Issues abiertos

| # GitHub | Alias | Titulo | Prioridad | Bloqueante |
|---|---|---|---|---|
| #19 | ASCII | Limpiar caracteres especiales de archivos Python existentes | Media | No |
| #20 | ON-EVENT-DEPRECATED | Migrar on_event a lifespan en backend/main.py | Baja | No |
| #21 | FRONTEND-MOCK | Agregar modo mock al modulo Catalogos | Media | No |
| #22 | LF-CRLF | Configurar .gitattributes para line endings en Windows | Baja | No |
| — | POSTCSS-TYPE | Agregar `"type": "module"` a frontend/package.json | Baja | No |

---

## Detalle

### #19 ASCII — Limpiar caracteres especiales
Los archivos Python existentes (catalogo.py, transaccion.py, etc.) tienen tildes y enye en comentarios. En Windows con encodings mixtos esto puede causar errores.

**Alcance:** `backend/models/`, `backend/services/`, `backend/api/` previos al modulo Catalogos.
**Regla desde ahora:** ningun archivo nuevo usa caracteres fuera de ASCII puro.

### #20 ON-EVENT-DEPRECATED — Migrar lifespan
`backend/main.py` usa `@app.on_event("startup")` deprecado en FastAPI moderno.
Fix: `@asynccontextmanager` con `lifespan` parameter. No bloquea nada, solo genera warning.

### #21 FRONTEND-MOCK — Mock para Catalogos
El modulo Catalogos consume la API real directamente, sin modo mock.
Fix: agregar `catalogosMock.js` y toggle `VITE_USE_MOCK` en `frontend/src/api/catalogos.js`.

### #22 LF-CRLF — Line endings
Sin `.gitattributes`, git en Windows convierte LF a CRLF generando diffs espurios.
Fix: agregar `.gitattributes` con reglas por extension.

### POSTCSS-TYPE — package.json type module
Vite/postcss genera warning por ausencia de `"type": "module"` en `frontend/package.json`.
Fix: agregar `"type": "module"` al package.json del frontend.

---

## Issues cerrados recientes

| Alias | Titulo | Cerrado en |
|---|---|---|
| REGLA-IMPORT | ImportError Regla vs ReglaClasificacion | v0.2.0 |
| ENV-SPLIT | Variables VITE_* en .env.dev causaban ValidationError | v0.2.0 |
| CONFTEST-TABLES | Tests fallaban con "no such table" | v0.2.0 |
| CAT-HIJOS | AttributeError Categoria.hijos — no existe relationship | v0.2.0 |
| DASHBOARD-IMPORT | App.jsx importaba modules/Dashboard (placeholder) | v0.2.1 |
| POSTCSS-MISSING | postcss.config.js no existia, Tailwind no compilaba | v0.2.1 |
