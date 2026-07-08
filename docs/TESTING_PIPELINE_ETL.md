# Testing del Pipeline ETL Gmail (dev)

Pipeline deterministico (regex + reglas heuristicas, sin LLM) que cubre
la fuente Gmail del ETL descrito en `docs/ETL_DISENO_FUNCIONAL.md`. Vive
en `scripts/etl/` y solo escribe en `data/dev/finanzas_dev.db` -- nunca en
la DB de produccion (OneDrive). Cada script que escribe en la DB valida
que el path contenga "dev" antes de conectar y aborta si no.

Las fuentes PDF (extractos OneDrive) y JSON (PWA mobile) tienen la
estructura del CLI preparada (`--fuente pdf|json` en `extraccion.py`) pero
su logica no esta implementada en esta entrega -- levantan
`NotImplementedError` con una referencia a donde esta el diseno.

Ver [ESCENARIOS_PRUEBA_ETL.md](ESCENARIOS_PRUEBA_ETL.md) para el detalle
y resultado esperado de cada escenario de prueba.

---

## Requisitos

```
venv\Scripts\pip install -r requirements.txt
```

`extraccion.py` necesita las credenciales OAuth de Gmail ya autorizadas
en `C:\Users\ghriz\.gmail-mcp\tokens\{hernan,malu}.json` (se reusan, no
hace falta re-autenticar). Los demas scripts (`correlacion.py`,
`reset_pipeline_dev.py`, `inspeccionar_pipeline.py`,
`generar_datos_prueba.py`) no tocan Gmail -- solo la DB de dev y archivos
en `staging/`.

---

## 1. extraccion.py -- manual

Lee correos reales de Gmail (hernan + malu) en un rango de fechas y
produce un JSON de staging con los candidatos. NUNCA marca correos como
leidos ni escribe en la DB.

```
venv\Scripts\python.exe scripts\etl\extraccion.py --fecha-desde 2026-06-01 --fecha-hasta 2026-06-30
```

`--fecha-desde` y `--fecha-hasta` son SIEMPRE obligatorios -- el script
falla si faltan, no hay rango por default.

**Que esperar:** por consola, cuantos correos encontro por cuenta y
cuantos candidatos quedaron descartables vs. a correlacionar. Se genera
`staging/candidatos_2026-06-01_2026-06-30.json` -- una lista de objetos
con `message_id`, `cuenta`, `fecha`, `remitente`, `asunto`,
`monto_detectado`, `snippet_o_cuerpo`, `necesito_lectura_completa`,
`descartable`, `motivo`.

Para debuggear un correo puntual sin tocar toda la ventana, abrir el JSON
generado y mirar el campo `motivo` de cada candidato (`monto_en_snippet`,
`monto_en_cuerpo_completo`, `remitente_marketing`, `sin_patron_monto`,
`sin_monto_ni_en_cuerpo_completo`).

Otras cuentas u opciones:
```
venv\Scripts\python.exe scripts\etl\extraccion.py --fecha-desde 2026-06-01 --fecha-hasta 2026-06-30 --cuentas hernan
venv\Scripts\python.exe scripts\etl\extraccion.py --fecha-desde 2026-06-01 --fecha-hasta 2026-06-30 --output staging\mi_corrida.json
```

---

## 2. correlacion.py -- manual

Recibe el JSON de `extraccion.py` (o de `generar_datos_prueba.py`) y hace
dedup + correlacion + insercion en la DB de dev.

```
venv\Scripts\python.exe scripts\etl\correlacion.py --input staging\candidatos_2026-06-01_2026-06-30.json
```

**Que esperar:** una linea de resumen por consola --
`Candidatos: N. Nuevas: N. Enriquecidas: N. Descartadas: N. Ambiguas: N. Ya procesadas (dedup): N. Entidades potenciales: N. Errores: N.`
Esa misma linea (mas el detalle de errores puntuales, si los hubo) queda
en `log_ejecuciones.notas` y `log_ejecuciones.alertas` (JSON con
`stats` + `errores`). Si hubo casos ambiguos, se escribe/actualiza
`staging/ambiguos_<mismo-sufijo-que-el-input>.json`.

Para inspeccionar el resultado sin escribir SQL a mano, usar
`inspeccionar_pipeline.py` (seccion 4).

Correr `correlacion.py` dos veces con el mismo `--input` es seguro --
la Capa 1 (dedup por `correos_procesados`) evita duplicar transacciones
(ver escenario e).

---

## 3. reset_pipeline_dev.py -- manual

Vuelve la DB de dev a un estado limpio conocido para poder repetir
pruebas. Borra solo lo que este pipeline creo (identificado por el
prefijo de id `gmail-etl-` en `transacciones`, y las filas de
`correos_procesados` con `cuenta_gmail` en `hernan`/`malu`) -- no toca
datos de otros seeders (`scripts/seed/`). Tambien borra todos los JSON en
`staging/`.

```
venv\Scripts\python.exe scripts\etl\reset_pipeline_dev.py
```

Rechaza correr si `--db` no apunta a un path que contenga "dev".

**Que esperar:** por consola, cuantas filas borro de cada tabla y cuantos
archivos de `staging/` elimino.

---

## 4. inspeccionar_pipeline.py -- manual

Reporte de consola del estado completo del pipeline, sin SQL a mano:

```
venv\Scripts\python.exe scripts\etl\inspeccionar_pipeline.py
```

**Que esperar**, en este orden:
1. **Corridas** (`log_ejecuciones`): fecha inicio/fin y resumen de cada
   corrida de `correlacion.py`, con el detalle de errores puntuales si
   los hubo (leidos desde la columna `alertas`).
2. **correos_procesados**: conteo agrupado por cuenta y por `resultado`
   (`ok` / `descartado` / `ambiguo`).
3. **Transacciones pendientes**: cada transaccion creada por el pipeline
   (prefijo `gmail-etl-`) con su confianza, completitud, contraparte
   resuelta y monto.
4. **Entidades potenciales**: conteo por tipo/estado, mas el detalle de
   cada propuesta y a que transaccion referencia.
5. **Bucket de ambiguos**: lee todos los `staging/ambiguos_*.json` y
   agrupa por motivo.

---

## 5. generar_datos_prueba.py -- manual

Genera la data minima de cada escenario sin depender de Gmail real (ver
`docs/ESCENARIOS_PRUEBA_ETL.md` para el detalle de cada uno):

```
venv\Scripts\python.exe scripts\etl\generar_datos_prueba.py --escenario b
venv\Scripts\python.exe scripts\etl\generar_datos_prueba.py --escenario todos
```

Escribe `staging/candidatos_escenario_<letra>.json`. El escenario `g`
ademas siembra dos transacciones existentes directamente en la DB de dev
(necesarias para forzar el caso de correlacion ambigua).

**IMPORTANTE:** correr `reset_pipeline_dev.py` ANTES de
`generar_datos_prueba.py`, no despues -- el reset borra todo `staging/`,
incluida la data recien generada.

---

## Ciclo completo de prueba manual (los 7 escenarios)

```
venv\Scripts\python.exe scripts\etl\reset_pipeline_dev.py
venv\Scripts\python.exe scripts\etl\generar_datos_prueba.py --escenario todos

venv\Scripts\python.exe scripts\etl\correlacion.py --input staging\candidatos_escenario_a.json
venv\Scripts\python.exe scripts\etl\correlacion.py --input staging\candidatos_escenario_b.json
venv\Scripts\python.exe scripts\etl\correlacion.py --input staging\candidatos_escenario_c.json
venv\Scripts\python.exe scripts\etl\correlacion.py --input staging\candidatos_escenario_d.json
venv\Scripts\python.exe scripts\etl\correlacion.py --input staging\candidatos_escenario_f.json
venv\Scripts\python.exe scripts\etl\correlacion.py --input staging\candidatos_escenario_g.json
venv\Scripts\python.exe scripts\etl\correlacion.py --input staging\candidatos_escenario_e.json
venv\Scripts\python.exe scripts\etl\correlacion.py --input staging\candidatos_escenario_e.json

venv\Scripts\python.exe scripts\etl\inspeccionar_pipeline.py
```

(El escenario `e` se corre dos veces a proposito -- es la prueba de
dedup. Tambien deduplica contra el escenario `b`, porque reusa el mismo
`message_id` a proposito.)

---

## Orquestador (extraccion + correlacion sobre Gmail real)

```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\etl\orquestador_pipeline.ps1 -FechaDesde 2026-06-01 -FechaHasta 2026-06-30
```

Corre `extraccion.py` y, solo si termino con exit code 0, corre
`correlacion.py` sobre el JSON que acaba de generar. Si `extraccion.py`
falla, loguea el error y no llama a `correlacion.py`.
