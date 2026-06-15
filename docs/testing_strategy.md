# Estrategia de Entornos y Pruebas — Plataforma Financiera MCGHR

**Versión:** 1.0  
**Última actualización:** Junio 2026  
**Generado con:** Claude.ai Pro (mcghr.claude@gmail.com)

---

## Principios

- **Nunca usar datos reales en pruebas.** Los datos financieros reales (GHR/MC) solo existen en el entorno de producción.
- **Entornos reproducibles.** Cualquier entorno de prueba puede crearse desde cero con un solo comando y destruirse limpiamente.
- **Datos realistas.** Los datos dummy deben parecerse lo suficiente a datos reales para que las pruebas sean significativas (montos en COP, bancos colombianos, categorías reales, patrones de gasto familiares).
- **Aislamiento total.** Cada entorno usa su propia base de datos, su propia carpeta de archivos y su propio puerto. No comparten nada.
- **Sin credenciales reales.** Los entornos de prueba usan credenciales mock — nunca tokens OAuth de Gmail reales, nunca API keys de producción.

---

## Los tres entornos

### `dev` — Desarrollo local
**Propósito:** El desarrollador (o la IA) prueba funcionalidades mientras las construye. Datos mínimos, reinicio frecuente.

- Puerto backend: `8001`
- Puerto frontend: `3001`
- BD: `data/dev/finanzas_dev.db`
- Carpeta documentos: `data/dev/onedrive/`
- Volumen de datos: ~50 transacciones, 2 meses de historia
- Vida útil: se resetea con cada sesión de desarrollo o cuando el dev lo necesite

**Cuándo usarlo:** al implementar un endpoint nuevo, al construir un componente de UI, al probar el ETL con un correo específico.

### `test` — Pruebas automatizadas
**Propósito:** Tests unitarios y de integración que corren en CI/CD. Datos controlados y deterministas — los mismos siempre, para que los tests sean reproducibles.

- Puerto backend: `8002`
- Puerto frontend: no levanta (los tests de backend no necesitan UI)
- BD: en memoria (`:memory:`) o `data/test/finanzas_test.db` (se recrea en cada test run)
- Carpeta documentos: `data/test/onedrive/` (fixtures estáticos)
- Volumen de datos: exactamente el necesario para cada test — ni más, ni menos
- Vida útil: se crea al inicio del test suite y se destruye al final

**Cuándo usarlo:** automáticamente en cada `git push` via GitHub Actions (futuro), manualmente antes de hacer un merge.

### `staging` — Pre-producción
**Propósito:** Validación end-to-end con volumen y complejidad realistas antes de pasar a producción. Simula un año completo de finanzas familiares.

- Puerto backend: `8003`
- Puerto frontend: `3003`
- BD: `data/staging/finanzas_staging.db`
- Carpeta documentos: `data/staging/onedrive/`
- Volumen de datos: ~500 transacciones, 12 meses de historia, datos de todos los módulos
- Vida útil: se recrea para cada validación mayor (antes de releases), puede mantenerse por semanas

**Cuándo usarlo:** antes de deployar una versión nueva a producción, para validar el flujo completo de usuario, para hacer demos.

---

## Estructura de carpetas

```
finanzas-mcghr/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  ← fixtures compartidos de pytest
│   │
│   ├── unit/                        ← tests sin BD ni HTTP
│   │   ├── test_clasificador.py     ← reglas de clasificación
│   │   ├── test_presupuesto.py      ← cálculos de proyección
│   │   ├── test_patrimonio.py       ← cálculo de patrimonio neto
│   │   └── test_backup.py           ← lógica de backup/restore
│   │
│   ├── integration/                 ← tests con BD real (SQLite en memoria)
│   │   ├── test_api_transacciones.py
│   │   ├── test_api_presupuestos.py
│   │   ├── test_api_catalogos.py
│   │   └── test_etl_correos.py      ← ETL con correos mock
│   │
│   └── e2e/                         ← tests end-to-end (staging)
│       └── test_flujo_confirmacion.py
│
├── fixtures/                        ← Datos estáticos para tests
│   ├── correos/                     ← Correos de ejemplo por banco
│   │   ├── bancolombia_consumo.eml
│   │   ├── bbva_transferencia.eml
│   │   ├── rappi_factura.eml
│   │   └── netflix_cobro.eml
│   ├── pdfs/                        ← PDFs de ejemplo (anonimizados)
│   │   ├── extracto_bc_ejemplo.pdf
│   │   └── extracto_occidente_ejemplo.pdf
│   └── json/                        ← JSONs de inbox mobile de ejemplo
│       ├── tx_nuevo_efectivo.json
│       └── doc_foto_factura.json
│
├── scripts/
│   ├── env/
│   │   ├── create_env.py            ← Crea un entorno desde cero
│   │   ├── destroy_env.py           ← Destruye un entorno limpiamente
│   │   ├── reset_env.py             ← Destruye y recrea (= destroy + create)
│   │   └── list_envs.py             ← Lista entornos activos con su estado
│   │
│   └── seed/
│       ├── seed.py                  ← Orquestador: llama a los seeders en orden
│       ├── seed_catalogos.py        ← Siembra catálogos maestros
│       ├── seed_transacciones.py    ← Genera transacciones dummy
│       ├── seed_presupuestos.py     ← Genera presupuestos mensuales
│       ├── seed_obligaciones.py     ← Genera obligaciones y cuotas
│       ├── seed_inversiones.py      ← Genera posiciones y valuaciones
│       └── seed_inbox.py            ← Genera JSONs de inbox mobile pendientes
│
└── .env.dev                         ← Variables de entorno para dev
    .env.test                        ← Variables de entorno para test
    .env.staging                     ← Variables de entorno para staging
```

---

## Comandos de ciclo de vida

Todos los comandos reciben el entorno como parámetro: `dev`, `test` o `staging`.

```bash
# Crear un entorno desde cero
python scripts/env/create_env.py --env dev

# Sembrar datos en un entorno existente
python scripts/seed/seed.py --env dev --volume minimal
python scripts/seed/seed.py --env staging --volume full

# Resetear un entorno (destroy + create + seed)
python scripts/env/reset_env.py --env dev --volume minimal

# Destruir un entorno
python scripts/env/destroy_env.py --env dev

# Listar entornos activos
python scripts/env/list_envs.py
```

### Niveles de volumen de datos (`--volume`)

| Nivel | Transacciones | Meses | Uso |
|---|---|---|---|
| `minimal` | ~50 | 2 | Desarrollo diario, pruebas rápidas |
| `standard` | ~200 | 6 | Tests de integración, validaciones |
| `full` | ~500 | 12 | Staging, validación pre-release |

---

## Qué siembra cada seeder

### `seed_catalogos.py`
Datos maestros base — siempre los mismos en todos los entornos:

**Personas:** GHR_TEST, MC_TEST  
**Monedas:** COP, USD, ARS  
**Cuentas:**
- `BC_CC_TEST` — Bancolombia Cuenta Corriente (GHR_TEST)
- `BC_TC_TEST` — Bancolombia Tarjeta de Crédito (GHR_TEST)
- `BBVA_CC_TEST` — BBVA Cuenta Corriente (GHR_TEST)
- `OCC_TC_TEST` — Banco de Occidente TC Visa (GHR_TEST)
- `IBKR_USD_TEST` — InteractiveBrokers USD (GHR_TEST)
- `NEQUI_TEST` — Nequi (GHR_TEST)

**Categorías** (completas, 3 niveles):
```
ALIM > ALIM_SUPER, ALIM_REST > ALIM_REST_DEL, ALIM_REST_SAL
TRANS > TRANS_UBER, TRANS_GASOLINA
VIVIENDA > VIV_ARRIENDO, VIV_SERVICIOS > VIV_SERV_LUZ, VIV_SERV_AGUA, VIV_SERV_INTERNET
SALUD > SAL_FARMACIA, SAL_MEDICO
EDU > EDU_COLEGIO, EDU_CURSOS
ENTRETEN > ENT_SUSCRIPCIONES, ENT_SALIDAS
INGRESO > ING_SALARIO, ING_FREELANCE, ING_INVERSION
INVERSION > INV_ACCIONES, INV_INMUEBLE
```

**Contrapartes:**
- Supermercados: Éxito, Carulla, D1, Jumbo
- Delivery: Rappi, Uber Eats
- Transporte: Uber, InDriver, Terpel
- Servicios: Netflix, Spotify, Disney+, Claro, EPM
- Bancos: Bancolombia, BBVA, Banco de Occidente
- Otros: DIAN, Secretaría de Hacienda

**Reglas de clasificación** (15 reglas base que cubren los patrones más comunes):
- remitente `alertasynotificaciones@notificaciones.bancolombia.com.co` → banco Bancolombia
- remitente `bbvanet@bbva.com.co` → banco BBVA
- asunto contiene `Rappi` → categoría ALIM_REST_DEL, contraparte Rappi
- asunto contiene `Netflix` → categoría ENT_SUSCRIPCIONES, contraparte Netflix
- etc.

### `seed_transacciones.py`
Genera transacciones con patrones realistas de una familia colombiana de clase media-alta:

**Gastos fijos mensuales (recurrentes):**
- Arriendo: $4.500.000 COP el día 5 de cada mes
- Claro internet + TV: $180.000 el día 10
- EPM servicios: varía entre $200.000 y $350.000 el día 15
- Netflix: $42.900 el día 22
- Spotify: $17.900 el día 22
- Disney+: $32.900 el día 22

**Gastos variables (con distribución realista):**
- Supermercado: 4-6 veces/mes, $150.000-$400.000 por compra
- Restaurantes: 3-8 veces/mes, $40.000-$180.000 por salida
- Delivery (Rappi): 5-12 veces/mes, $25.000-$80.000 por pedido
- Uber: 8-15 veces/mes, $15.000-$45.000 por viaje
- Farmacia: 1-3 veces/mes, $20.000-$120.000
- Gasolina: 2-4 veces/mes, $100.000-$200.000

**Ingresos:**
- Salario GHR: ingreso fijo el día 25 de cada mes
- Salario MC: ingreso fijo el día 28 de cada mes

**Mezcla de fuentes:**
- 40% correos Gmail (transacciones con `fuente = 'gmail'`)
- 30% PDFs extractos (transacciones con `fuente = 'pdf_extracto'`)
- 20% mobile inbox (transacciones con `fuente = 'mobile'`)
- 10% manual (transacciones con `fuente = 'manual'`)

**Mezcla de estados:**
- 70% `confirmado` (revisado_humano = 1)
- 20% `pendiente` (revisado_humano = 0, para poblar la cola de confirmación)
- 10% `descartado`

**Variación de confianza:**
- Transacciones de correos conocidos: confianza 0.85-0.98
- Transacciones de PDFs: confianza 0.70-0.90
- Transacciones de mobile: confianza 1.0 (el usuario las cargó)
- Transacciones manuales: confianza 1.0

### `seed_presupuestos.py`
Genera presupuestos para cada mes del período con variación realista:

```
ALIM_SUPER:        $800.000 - $1.000.000/mes
ALIM_REST:         $300.000 - $500.000/mes
TRANS:             $400.000 - $600.000/mes
VIV_ARRIENDO:      $4.500.000/mes (fijo)
VIV_SERVICIOS:     $300.000/mes
ENT_SUSCRIPCIONES: $100.000/mes (fijo)
SALUD:             $200.000/mes
```

### `seed_obligaciones.py`
Genera obligaciones representativas:

- **Crédito vehículo** (si `--volume standard` o `full`): $1.800.000/mes, 36 cuotas, inicio hace 12 meses
- **Arriendo** (recurrente): $4.500.000/mes, vencimiento día 5
- **Servicios públicos** (recurrente): $280.000/mes, vencimiento días 10-15
- **Cuotas de apartamento en pozo** (si `--volume full`): $3.200.000/mes, inicio hace 3 meses

### `seed_inversiones.py`
Solo disponible con `--volume full`:

- Posición en IBKR: acciones de VTI y AAPL con historial de 12 meses
- Apartamento en pozo: inversión inicial + cuotas pagadas + valuación de mercado estimada
- Cuenta de ahorro BBVA con rendimiento bajo

### `seed_inbox.py`
Genera entre 3 y 10 JSONs de inbox mobile en estado `pendiente` para poblar la cola de revisión:

```json
{
  "tipo": "tx_nuevo",
  "fecha_creacion": "...",
  "dispositivo": "iphone_ghr",
  "datos": {
    "fecha": "...",
    "monto": 45000,
    "moneda": "COP",
    "descripcion": "Almuerzo con cliente",
    "completitud": "minimo"
  }
}
```

---

## Datos sensibles — qué NO incluir nunca en seeds ni fixtures

| Dato | Alternativa en tests |
|---|---|
| Emails reales (ghrizzi.goog@gmail.com) | `hernan.test@example.com` |
| Tokens OAuth reales | Mock client que devuelve fixtures estáticos |
| ANTHROPIC_API_KEY real | Variable de entorno apuntando a mock o a una key de test con límite bajo |
| Números de cuenta reales | Números ficticios: `**** 9999`, `**** 8888` |
| RUTs o cédulas reales | IDs ficticios: `GHR_TEST`, `MC_TEST` |
| Montos reales de salario | Montos ficticios pero realistas: $8.500.000, $5.200.000 |

---

## Mock de servicios externos

### Mock de Gmail / IMAP
Para tests y desarrollo, el lector de correos tiene un modo mock que lee desde `fixtures/correos/` en lugar de conectarse a Gmail. Se activa con la variable de entorno:
```bash
MAIL_PROVIDER=mock   # en lugar de gmail o imap
```

### Mock de Claude API
Para tests automatizados, las llamadas a Claude API se interceptan con respuestas predefinidas en `fixtures/claude_responses/`. Esto evita costos de API en cada test run y hace los tests deterministas.
```bash
CLAUDE_PROVIDER=mock   # devuelve respuestas desde fixtures
```

### Mock de OneDrive / sistema de archivos
Los tests usan una carpeta temporal (`/tmp/mcghr_test_XXXX/`) en lugar de OneDrive real:
```bash
ONEDRIVE_PATH=/tmp/mcghr_test   # ruta temporal por entorno
```

---

## Tests — cobertura mínima esperada por módulo

### Tests unitarios (sin BD, sin HTTP)
| Módulo | Qué se testea |
|---|---|
| Clasificador | Que las reglas se aplican correctamente, que el aprendizaje genera la regla correcta |
| Presupuesto | Cálculo de proyección de cierre, cálculo de % ejecutado, alerta de desvío |
| Patrimonio | Suma de activos - pasivos, inclusión/exclusión de RSUs |
| Backup | Que el ZIP contiene todos los archivos requeridos, que el manifest es correcto |
| Undo stack | Push, pop, redo, vaciado al grabar |

### Tests de integración (con BD SQLite en memoria)
| Módulo | Qué se testea |
|---|---|
| API transacciones | CRUD completo, confirmar, descartar, filtros |
| API presupuestos | Crear, editar, cálculo de ejecución en tiempo real |
| API catálogos | ABM categorías con validación de jerarquía, inactivación |
| ETL correos | Que un `.eml` de fixture se convierte en la transacción correcta |
| ETL PDF | Que un PDF de fixture genera las transacciones correctas |

### Tests end-to-end (contra entorno staging)
| Flujo | Qué se testea |
|---|---|
| Flujo de confirmación | Llega transacción pendiente → usuario la edita → graba → aparece en lista |
| Flujo mobile | JSON en inbox → ETL lo procesa → aparece en cola → usuario confirma |
| Flujo presupuesto | Usuario define presupuesto → llegan gastos → dashboard muestra alerta |

---

## Herramientas

| Herramienta | Uso | Por qué |
|---|---|---|
| `pytest` | Test runner principal | Estándar Python, fixtures potentes |
| `pytest-asyncio` | Tests de endpoints async FastAPI | FastAPI es async |
| `httpx` | Cliente HTTP para tests de API | Recomendado por FastAPI para tests |
| `factory_boy` | Generación de objetos de prueba | Alternativa limpia a fixtures manuales |
| `Faker` (python-faker) | Datos dummy realistas | Genera nombres, fechas, montos con distribución realista |
| `pytest-cov` | Cobertura de código | Mide qué porcentaje del código está cubierto por tests |
| `freezegun` | Congelar fecha/hora en tests | Para testear lógica que depende de la fecha actual |

Instalación del entorno de testing:
```bash
pip install pytest pytest-asyncio httpx factory-boy faker pytest-cov freezegun --break-system-packages
```

---

## Variables de entorno por entorno

```bash
# .env.dev
ENV=dev
DB_PATH=data/dev/finanzas_dev.db
ONEDRIVE_PATH=data/dev/onedrive
BACKEND_PORT=8001
FRONTEND_PORT=3001
ANTHROPIC_API_KEY=sk-ant-test-...   # key real con límite bajo, o mock
MAIL_PROVIDER=mock
CLAUDE_PROVIDER=real                # dev puede usar Claude real para probar clasificación

# .env.test
ENV=test
DB_PATH=:memory:
ONEDRIVE_PATH=data/test/onedrive
BACKEND_PORT=8002
ANTHROPIC_API_KEY=mock
MAIL_PROVIDER=mock
CLAUDE_PROVIDER=mock                # tests siempre usan mock

# .env.staging
ENV=staging
DB_PATH=data/staging/finanzas_staging.db
ONEDRIVE_PATH=data/staging/onedrive
BACKEND_PORT=8003
FRONTEND_PORT=3003
ANTHROPIC_API_KEY=sk-ant-test-...   # key real con límite bajo
MAIL_PROVIDER=mock
CLAUDE_PROVIDER=real
```

---

## Flujo de desarrollo recomendado

```
1. Arrancar entorno dev
   python scripts/env/reset_env.py --env dev --volume minimal

2. Desarrollar la funcionalidad
   (backend + frontend)

3. Correr tests unitarios mientras se desarrolla
   pytest tests/unit/ -v

4. Correr tests de integración antes de commitear
   pytest tests/integration/ -v --cov=backend

5. Commitear
   git commit -m "feat: endpoint POST /api/v1/transacciones"

6. Validación en staging antes de release
   python scripts/env/reset_env.py --env staging --volume full
   pytest tests/e2e/ -v

7. Release a producción
   (nunca tocar data/prod/ directamente)
```

---

## Lo que viene después de esta estrategia

- Implementar `scripts/env/create_env.py` y `seed.py` junto con el primer módulo del backend
- Agregar `fixtures/correos/*.eml` con ejemplos reales anonimizados de Bancolombia y BBVA
- Configurar GitHub Actions para correr `pytest tests/unit/ tests/integration/` en cada push
- El primer entorno `dev` se crea cuando el primer módulo del backend esté listo

---

*Documento generado en Junio 2026 — Plataforma Financiera MCGHR*
