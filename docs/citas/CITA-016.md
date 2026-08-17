# CITA-016 -- CORS con origenes hardcodeados en vez de settings.cors_origins

**Frecuencia:** 1 vez detectada (sesion 2026-08-16, backend/main.py)
**Nivel:** 3-CONTEXTO

**Error:**
`Settings.cors_origins` (backend/core/config.py) existia desde antes y
estaba pensado como la fuente de verdad de los origenes permitidos por
entorno (dev, staging, prod), configurable via `.env.*`. Pero
`CORSMiddleware` en `backend/main.py` nunca lo usaba: tenia una lista
hardcodeada de tres origenes (`localhost:3000`, `localhost:3003`,
`127.0.0.1:3000`) directamente en el codigo, desconectada de `Settings`.
El bug estuvo latente sin sintoma mientras solo se uso dev/staging (ambos
incluidos por casualidad en la lista hardcodeada). Se manifesto recien al
levantar el entorno de produccion en `:3002` (`frontend/.env.prod` con
`FRONTEND_PORT=3002`): el navegador bloqueaba las llamadas del frontend
prod al backend prod por CORS, porque `:3002` no estaba en la lista
hardcodeada ni en ningun lado que la reflejara.

**Resolucion:**
`CORSMiddleware` ahora usa `allow_origins=settings.cors_origins` directo.
Se agrego `http://127.0.0.1:3000` al default de `Settings.cors_origins`
para no perder ese origen que si estaba en la lista hardcodeada vieja.
`.env.prod` define `CORS_ORIGINS=["http://localhost:3002"]` (pydantic-settings
reemplaza la lista default entera, no la extiende). Ver commit `bd7ece4`.

**Prevencion:**
Cuando un `Settings` field existe pero un valor relacionado sigue
hardcodeado en otro archivo (`main.py`, un router, un script), tratarlo
como sospechoso -- es exactamente el patron de este bug. Antes de agregar
un entorno nuevo (puerto, host), buscar todos los lugares que puedan tener
una lista de origenes/hosts hardcodeada en paralelo a `Settings`, no asumir
que un solo `Settings` field cubre todos los usos.

**Senal de alarma para Hernan:**
Si el frontend carga pero las llamadas a la API fallan en la consola del
navegador con un error que menciona "CORS" o "Access-Control-Allow-Origin",
y el puerto del frontend es distinto de 3000/3001/3003, es probable que sea
esta clase de problema -- el origen nuevo no llego a `Settings.cors_origins`
del entorno que se esta usando.
