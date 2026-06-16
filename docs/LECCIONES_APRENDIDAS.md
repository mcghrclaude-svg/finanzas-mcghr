# Lecciones aprendidas — proyecto Finanzas MCGHR
**Reglas que aplican a TODOS los chats futuros**

---

## Antes de escribir codigo

1. **SIEMPRE leer el repo completo antes de escribir una sola linea.** Usar web_fetch sobre el repo publico o project_knowledge_search. Nunca asumir la estructura.

2. **SIEMPRE verificar que los modelos SQLAlchemy reales coinciden con lo que se va a usar.** El modelo Categoria NO tiene relationship "hijos" — el arbol se construye manualmente.

3. **SIEMPRE verificar el Base correcto:** los modelos usan `backend/models/base.py`, no `backend/core/database.py`.

4. **El conftest.py de tests DEBE importar todos los modelos explicitamente antes de create_all**, o las tablas no se crean en la DB en memoria.

---

## Entorno y configuracion

1. **`postcss.config.js` es REQUERIDO para Tailwind v3 + Vite.** Si no existe, ninguna clase Tailwind compila. El archivo debe estar en `frontend/` (no en la raiz del repo).

2. **Las variables `VITE_*` NO van en `.env.dev`** (las lee Python/pydantic y falla con "extra inputs not permitted"). Van en `frontend/.env.local`.

3. **Siempre activar venv antes de cualquier comando Python:**
   ```powershell
   venv\Scripts\activate
   ```

4. **Scripts `.ps1` en Windows requieren:**
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```

---

## Flujo de desarrollo

1. **El flujo es:** claude.ai genera codigo -> PC ejecuta y valida -> si hay error, diagnostico en PC -> fix en claude.ai -> nunca al reves.

2. **Cada entrega de archivos debe incluir un script instalador `.ps1`** con `$SRC = $PSScriptRoot` para que funcione sin importar donde esten los archivos.

3. **Los archivos con el mismo nombre** (maestros.py x3) deben entregarse con nombres diferenciados (`backend_schemas_maestros.py`, etc.)

4. **Nunca usar caracteres especiales (tildes, enye) en ningun archivo** — ni comentarios, ni strings, ni docs dentro del codigo. Solo ASCII puro.

---

## Stack y patrones del repo

1. **El frontend usa Tailwind puro.** NO usar CSS custom ni variables `--color-*`. Las clases de color custom disponibles son: `primary-{50,500,600,700,900}`, `danger-{500,100}`, `warning-{500,100}`, `success-{500,100}`.

2. **Los modulos nuevos van en `frontend/src/modules/NombreModulo/index.jsx`.** NO en `pages/`.

3. **Toast notifications:** `react-hot-toast` (ya instalado). `import toast from 'react-hot-toast'`.

4. **El Layout (sidebar + header) ya existe en `Layout.jsx`.** Los modulos van dentro del main — no necesitan su propio layout.

5. **El patron de repo es: nunca borrado fisico.** Solo soft-delete (`activa = False`).

---

## Bugs conocidos y resueltos

1. **`backend/models/__init__.py`** importaba `Regla` pero la clase es `ReglaClasificacion`. Ya corregido.

2. **El Dashboard real** estaba en `pages/Dashboard.jsx` pero `App.jsx` importaba de `modules/Dashboard` (placeholder). Ya migrado a `modules/`.

3. **`postcss.config.js`** no existia en el repo — Tailwind no compilaba. Ya agregado.
