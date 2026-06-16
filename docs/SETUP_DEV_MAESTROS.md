# INSTRUCCIONES DE CONFIGURACIÓN EN PC
## Puntos 1 y 2: Backend + Frontend Datos Maestros + Seed
**Fecha:** Junio 2026  
**Destino:** C:\Users\ghriz\finanzas-mcghr\

---

## PASO 0 — Actualizar el repo local desde GitHub

```powershell
cd C:\Users\ghriz\finanzas-mcghr
git pull origin main
```

---

## PASO 1 — Instalar dependencias del backend

```powershell
cd C:\Users\ghriz\finanzas-mcghr
venv\Scripts\activate
pip install -r requirements.txt
```

Verificá que la instalación no tuvo errores. Ignorá el aviso de upgrade de pip.

---

## PASO 2 — Crear el entorno dev aislado

Este comando crea `finanzas_dev.db` en la raíz del repo (NO en OneDrive).  
La base de datos de producción en OneDrive NO es tocada.

```powershell
cd C:\Users\ghriz\finanzas-mcghr
venv\Scripts\activate
python scripts/env/reset_env.py --env dev --action create
```

Esperás ver:
```
📦 Creando entorno 'dev' → finanzas_dev.db
✅ Tablas creadas en finanzas_dev.db
```

---

## PASO 3 — Cargar los datos maestros iniciales (Punto 2)

```powershell
python scripts/env/reset_env.py --env dev --action seed
```

Esperás ver algo como:
```
🌱 Seeding → sqlite+aiosqlite:///./finanzas_dev.db
✅ Seed de datos maestros completado.
   Monedas:      5
   Personas:     2
   Cuentas:      12
   Categorías:   55
   Contrapartes: 25
```

---

## PASO 4 — Correr los tests automáticos

```powershell
cd C:\Users\ghriz\finanzas-mcghr
venv\Scripts\activate
pytest tests/unit/ tests/integration/ -v
```

Todos los tests deben pasar en verde. El output esperado es:
```
tests/unit/test_schemas.py::TestMonedaSchema::test_id_valido PASSED
tests/unit/test_schemas.py::TestMonedaSchema::test_id_minusculas_rechazado PASSED
... (todos verdes)
tests/integration/test_maestros_api.py::TestMonedas::test_listar_vacio PASSED
... (todos verdes)
PASSED 40+ tests
```

Si algún test falla, copiá el error y pasámelo.

---

## PASO 5 — Levantar el backend

```powershell
cd C:\Users\ghriz\finanzas-mcghr
venv\Scripts\activate
uvicorn backend.main:app --reload --port 8000
```

Verificá:
- `http://localhost:8000/health` → `{"status":"ok","env":"dev"}`
- `http://localhost:8000/docs` → Swagger UI con todos los endpoints

---

## PASO 6 — Abrir la interfaz de datos maestros

Con el backend corriendo, abrí en el browser:

```
C:\Users\ghriz\finanzas-mcghr\frontend\maestros.html
```

O simplemente doble-click en el archivo desde Explorer.

Vas a ver la interfaz con los datos cargados:
- Sidebar con 6 secciones (Monedas, Personas, Cuentas, Categorías, Contrapartes, Obligaciones)
- Cuentas ya pre-cargadas (BC_CC_GHR, IBKR_USD, etc.)
- Árbol de categorías con todos los niveles
- Botón "Nuevo" para agregar registros
- Edición y desactivación inline

---

## VALIDACIONES MANUALES

Una vez levantado todo, verificá estos flujos:

### 1. Crear una moneda nueva
- Click en "Monedas" en el sidebar
- Click "+ Nuevo"
- Completar: ID=`BTC`, Nombre=`Bitcoin`, Símbolo=`₿`, marcar "Es criptomoneda"
- Click "Crear" → debe aparecer en la tabla

### 2. Desactivar una cuenta
- Click en "Cuentas"
- Hovear sobre NEQUI_GHR → aparece 🚫
- Click 🚫 → confirmar → la cuenta queda marcada como inactiva (no se borra)

### 3. Navegar el árbol de categorías
- Click en "Categorías"
- Ver el árbol ALIM → ALIM_REST → ALIM_REST_DEL
- Click en ▸/▾ para expandir/colapsar

### 4. Editar una cuenta
- Hovear sobre BC_CC_GHR → ✏️
- Cambiar el número de cuenta a "1234"
- Guardar → verificar el cambio

---

## DESTRUIR EL ENTORNO DE PRUEBAS

Cuando quieras borrar todo:

```powershell
cd C:\Users\ghriz\finanzas-mcghr
venv\Scripts\activate
python scripts/env/reset_env.py --env dev --action destroy
```

Esto borra `finanzas_dev.db` y sus archivos WAL. La DB de OneDrive no es afectada.

---

## TROUBLESHOOTING

**Error: "Module not found: backend"**
→ Asegurate de correr desde la raíz del repo (`cd C:\Users\ghriz\finanzas-mcghr`)

**Error: "venv not found"**  
→ `py -3.12 -m venv venv` y luego `pip install -r requirements.txt`

**El HTML no conecta al backend**  
→ Verificar que el backend esté corriendo en puerto 8000  
→ Revisar consola del browser (F12) por errores CORS

**pytest: "no tests found"**
→ Verificar que estás en la raíz del repo con el venv activado
