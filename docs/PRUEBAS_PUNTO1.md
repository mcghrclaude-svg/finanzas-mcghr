# INSTRUCCIONES DE PRUEBA EN PC — Punto 1
## Módulo de gestión de datos maestros
**Antes de hacer commit al repo. Todos los pasos en orden.**

---

## Archivos nuevos en esta entrega

Descargá la carpeta `punto1/` y copiá los archivos a estas rutas en el repo local:

```
punto1/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Maestros.jsx          → frontend/src/pages/Maestros.jsx
│   │   │   └── Maestros.css          → frontend/src/pages/Maestros.css
│   │   ├── components/
│   │   │   └── maestros/
│   │   │       ├── MaestrosUI.jsx    → frontend/src/components/maestros/MaestrosUI.jsx
│   │   │       └── MaestrosForms.jsx → frontend/src/components/maestros/MaestrosForms.jsx
│   │   ├── hooks/
│   │   │   └── useMaestros.js        → frontend/src/hooks/useMaestros.js
│   │   ├── mock/
│   │   │   └── maestrosMock.js       → frontend/src/mock/maestrosMock.js
│   │   └── tests/
│   │       ├── maestros.test.js      → frontend/src/tests/maestros.test.js
│   │       └── setup.js              → frontend/src/tests/setup.js
│   └── vitest.config.js              → frontend/vitest.config.js
└── backend/
    ├── main.py                       → backend/main.py
    ├── core/
    │   ├── config.py                 → backend/core/config.py
    │   └── database.py               → backend/core/database.py
    ├── models/
    │   └── maestros.py               → backend/models/maestros.py
    ├── schemas/
    │   └── maestros.py               → backend/schemas/maestros.py
    ├── repositories/
    │   └── maestros.py               → backend/repositories/maestros.py
    └── api/v1/routers/
        └── maestros.py               → backend/api/v1/routers/maestros.py
```

---

## PARTE A — Backend (Python)

### A1. Crear el entorno dev aislado

```powershell
cd C:\Users\ghriz\finanzas-mcghr
venv\Scripts\activate
pip install -r requirements.txt
python scripts/env/reset_env.py --env dev --action reset
```

Esperás:
```
📦 Creando entorno 'dev' → finanzas_dev.db
✅ Seed de datos maestros completado.
   Monedas:      5
   Personas:     2
   Cuentas:      12
   Categorías:   55
   Contrapartes: 25
```

### A2. Correr los tests del backend

```powershell
pytest tests/unit/ tests/integration/ -v
```

Todos deben estar en verde. Si hay algún fallo, copiá el error.

### A3. Levantar el backend

```powershell
uvicorn backend.main:app --reload --port 8000
```

Verificar:
- `http://localhost:8000/health` → `{"status":"ok","env":"dev"}`
- `http://localhost:8000/docs` → Swagger UI con el router `/maestros`

---

## PARTE B — Frontend (React)

### B1. Instalar dependencias de testing

```powershell
cd C:\Users\ghriz\finanzas-mcghr\frontend
npm install --save-dev vitest @vitejs/plugin-react @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

### B2. Agregar script de test al package.json

Abrí `frontend/package.json` y agregá en `"scripts"`:

```json
"test": "vitest run",
"test:watch": "vitest"
```

### B3. Correr los tests del frontend

```powershell
cd C:\Users\ghriz\finanzas-mcghr\frontend
npm run test
```

Esperás ver todos los tests en verde:
```
✓ maestrosMock — integridad de datos (8 tests)
✓ formatCOP (4 tests)
✓ SECCION_META (1 test)
✓ TIPO_CUENTA_LABEL (1 test)
```

### B4. Agregar la ruta en App.jsx

Abrí `frontend/src/App.jsx` y verificá que tiene esta línea en los imports:

```jsx
import Maestros from '@/modules/Maestros'
```

Si usa `@/modules/`, el archivo va en `frontend/src/modules/Maestros.jsx` (que re-exporta desde pages).
Si usa `@/pages/`, apunta directo a `Maestros.jsx`.

Verificá también que la ruta `/catalogos/*` esté declarada:

```jsx
<Route path="/catalogos/*" element={<Maestros />} />
```

### B5. Levantar el frontend en modo mock

```powershell
cd C:\Users\ghriz\finanzas-mcghr\frontend
npm run dev
```

Abrí `http://localhost:5173` (o el puerto que muestre Vite).

---

## VALIDACIONES MANUALES (con mock)

Con `VITE_USE_MOCK=true` (default), validá estos flujos sin necesitar el backend:

### ✅ Validación 1 — Navegación entre secciones
- Hacé click en cada sección del nav (Monedas, Personas, Cuentas, etc.)
- Cada una debe cargar datos distintos
- El badge del nav muestra el total de registros

### ✅ Validación 2 — Tabla de Cuentas
- Debés ver las 12 cuentas de GHR/MC
- Hover sobre una fila → aparecen botones ✏️ y 🚫
- El filtro de tipo debe funcionar (ej: "Tarjeta crédito" → solo TCs)

### ✅ Validación 3 — Árbol de Categorías
- Click en "Categorías" → ver árbol jerárquico
- Click en ▸ para expandir / ▾ para colapsar
- Hover sobre una fila → botones de acción

### ✅ Validación 4 — Crear registro (mock)
- Click en "+ Nuevo" en Monedas
- Completar: ID=`BTC`, Nombre=`Bitcoin`, Símbolo=`₿`, marcar "Es criptomoneda"
- Click "Crear" → toast verde "✅ Creado correctamente"
- *Nota: en mock el registro no persiste al refrescar — es expected*

### ✅ Validación 5 — Editar registro (mock)
- Hover sobre Bancolombia CC en Cuentas → ✏️
- Cambiar el banco a "Bancolombia S.A."
- "Guardar cambios" → toast verde

### ✅ Validación 6 — Desactivar registro (mock)
- Hover sobre cualquier moneda → 🚫
- Confirmar en el diálogo
- Toast "🚫 Desactivado"

### ✅ Validación 7 — Búsqueda
- En Contrapartes, escribir "banco" en el buscador
- Solo deben aparecer registros que contienen "banco"

---

## VALIDACIONES CON API REAL

Una vez validado el mock, cambiar a API real:

```powershell
# En frontend/.env.dev
VITE_USE_MOCK=false
```

Repetir las validaciones 1-7 con el backend corriendo. Esta vez los cambios deben persistir.

Verificar en Swagger (`http://localhost:8000/docs`):
- `GET /api/v1/maestros/cuentas` → 12 cuentas del seed
- `GET /api/v1/maestros/categorias` → árbol de categorías
- `POST /api/v1/maestros/monedas` → crear BTC

---

## DESTRUIR EL ENTORNO

Cuando terminés las pruebas:

```powershell
cd C:\Users\ghriz\finanzas-mcghr
venv\Scripts\activate
python scripts/env/reset_env.py --env dev --action destroy
```

---

## TROUBLESHOOTING

**"Cannot find module '../api/client'"**
→ Verificar que `frontend/src/api/client.js` existe (viene del desarrollo anterior)

**Tests fallan con "VITE_USE_MOCK is not defined"**
→ `vi.stubEnv` requiere Vitest >= 0.30. Actualizar: `npm install vitest@latest --save-dev`

**La ruta /catalogos no carga Maestros**
→ Verificar App.jsx: la ruta debe apuntar a `Maestros` (no al módulo vacío anterior)

**Árbol de categorías vacío**
→ La API de categorías devuelve árbol solo para el endpoint `/categorias` (sin `/flat`).
   Verificar que `VITE_USE_MOCK=true` para evitar dependencia del backend.

**CORS error en API real**
→ Verificar que el backend corre en puerto 8000 y que `VITE_API_URL=http://localhost:8000`
