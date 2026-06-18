# Inbox Backend — Diseño Funcional (Entrega 3A)
## Plataforma Financiera MCGHR

**Fecha:** Junio 2026
**Estado:** Aprobado — pendiente implementacion
**Entrega:** 3A — primera de tres entregas del Punto 3

---

## Que es el Inbox

El Inbox es la cola de revision humana. Contiene todas las transacciones
que el ETL propuso pero que todavia no fueron confirmadas ni descartadas
por el humano.

Cada item del inbox representa un evento financiero detectado automaticamente
que necesita la atencion del usuario antes de quedar registrado como
transaccion definitiva en el sistema.

---

## Flujo completo

```
ETL (Claude Desktop, 4am)
    |
    | escribe directo a SQLite via MCP sqlite
    v
tabla: transacciones (estado = "pendiente")
tabla: correos_procesados
tabla: inbox_mobile (registro de JSONs PWA procesados)
    |
    | el backend expone via API REST
    v
GET /api/v1/inbox
    |
    | el frontend (React) presenta la cola al usuario
    v
Usuario ve lista de transacciones pendientes
Usuario confirma / edita / descarta cada item
    |
    +-- Confirma sin cambios
    |       -> estado = "confirmada", revisado_humano = 1
    |
    +-- Confirma con correccion de categoria
    |       -> estado = "confirmada", revisado_humano = 1
    |       -> crea/actualiza regla en reglas_clasificacion
    |
    +-- Descarta
            -> estado = "anulada", revisado_humano = 1
            -> no genera regla (puede ser un caso unico)
```

---

## Endpoints del backend

### GET /api/v1/inbox
Lista transacciones pendientes de revision.

**Query params:**
- `estado` (default: `pendiente`) — pendiente | confirmada | anulada
- `origen` — email | pdf | mobile | manual
- `cursor` — paginacion
- `limit` (default: 50, max: 200)

**Orden:** completitud ASC — las mas incompletas primero (requieren mas atencion)

**Response:**
```json
{
  "items": [
    {
      "id": "TX_abc123",
      "origen": "email",
      "fecha": "2026-06-15",
      "monto": 45000.00,
      "moneda": "COP",
      "descripcion": "Compra con TC Bancolombia",
      "categoria_propuesta": {
        "id": "ALIM-REST",
        "nombre": "Restaurantes"
      },
      "contraparte_propuesta": {
        "id": "CP_rappi",
        "nombre": "Rappi"
      },
      "cuenta_propuesta": {
        "id": "BCO-TC-GHR",
        "nombre": "Bancolombia TC GHR"
      },
      "confianza": 0.82,
      "completitud": 0.75,
      "estado_enriquecimiento": "enriquecido",
      "estado": "pendiente",
      "creado_en": "2026-06-15T04:12:33-05:00"
    }
  ],
  "next_cursor": "TX_xyz789",
  "total_pendientes": 12
}
```

---

### GET /api/v1/inbox/stats
Contadores para el badge de notificacion del Dashboard.

**Response:**
```json
{
  "pendientes": 12,
  "alta_prioridad": 3,
  "confirmados_hoy": 5
}
```

`alta_prioridad` = pendientes con confianza < 0.60 (el ETL no pudo clasificar bien)

---

### GET /api/v1/inbox/{id}
Detalle completo de un item, incluyendo datos raw del ETL.

**Response:** igual que el item de la lista, mas:
- `raw_data` — datos originales del correo/PDF parseados por el ETL
- `regla_aplicada` — si el ETL uso una regla para clasificar, cual fue
- `documentos_vinculados` — facturas o PDFs asociados a esta transaccion

---

### PATCH /api/v1/inbox/{id}
Editar campos antes de confirmar.

**Body (todos opcionales):**
```json
{
  "fecha": "2026-06-15",
  "monto": 45000.00,
  "id_categoria": "ALIM-REST",
  "id_cuenta": "BCO-TC-GHR",
  "id_contraparte": "CP_rappi",
  "descripcion": "Almuerzo con cliente",
  "es_reembolsable": false
}
```

**Response:** el item actualizado

---

### POST /api/v1/inbox/{id}/confirmar
Confirma el item. Lo mueve de "pendiente" a "confirmada".

**Body (opcional):**
```json
{
  "id_categoria": "ALIM-REST",
  "notas": "Almuerzo de trabajo"
}
```

Si `id_categoria` en el body difiere de `categoria_propuesta` original,
el servicio crea o actualiza una regla en `reglas_clasificacion`.

**Response:**
```json
{
  "ok": true,
  "id": "TX_abc123",
  "regla_creada": true
}
```

---

### POST /api/v1/inbox/{id}/descartar
Descarta el item. No es una transaccion financiera real.
Ejemplos: correo de confirmacion de login, newsletter bancario,
notificacion que no es un movimiento de dinero.

**Response:**
```json
{
  "ok": true,
  "id": "TX_abc123"
}
```

---

### POST /api/v1/inbox/confirmar-lote
Confirma multiples items a la vez. Util para limpiar la cola rapidamente
cuando hay muchos items de alta confianza.

**Body:**
```json
{
  "ids": ["TX_abc123", "TX_def456", "TX_ghi789"]
}
```

**Response:**
```json
{
  "confirmados": 3,
  "errores": []
}
```

---

## Logica de negocio — reglas de aprendizaje

Cuando el humano confirma con una categoria diferente a la propuesta:

1. Buscar si ya existe una regla en `reglas_clasificacion` que matchea
   el mismo patron (remitente + asunto del correo fuente)
2. Si existe: actualizar `id_categoria` y sumar 1 a `usos`
3. Si no existe: crear nueva regla con `creada_por = 'humano'`,
   `confianza_base = 0.90`, `usos = 1`

Esta regla queda disponible para el ETL en la proxima ejecucion.

---

## Estructura de archivos a implementar

```
backend/
    schemas/
        inbox.py               <- Pydantic models request/response
    repositories/
        inbox_repository.py    <- Acceso a datos (SQLAlchemy async)
    services/
        inbox_service.py       <- Logica de negocio
    api/v1/routers/
        inbox.py               <- Endpoints (reemplaza el actual vacio)

tests/integration/
    test_inbox_api.py          <- Tests de integracion

scripts/seed/
    seed_inbox.py              <- Seed de datos dummy para dev
```

---

## Seed de datos para desarrollo

El seed crea 8 transacciones pendientes con distintas caracteristicas:

| # | Origen | Confianza | Descripcion |
|---|---|---|---|
| 1 | email | 0.92 | Cobro Netflix — regla exacta matchea |
| 2 | email | 0.78 | Rappi — comercio conocido, monto normal |
| 3 | email | 0.55 | Transferencia bancaria — destino desconocido |
| 4 | pdf | 0.85 | Linea de extracto Bancolombia TC |
| 5 | pdf | 0.45 | Linea de extracto con descripcion ambigua |
| 6 | mobile | 1.00 | Foto con catalogacion del humano (datos firmes) |
| 7 | mobile | 0.60 | Solo foto, ETL extrae lo que puede |
| 8 | manual | 1.00 | Ingreso manual (ya confirmado, para probar filtros) |

---

## Tests de integracion requeridos

- GET /inbox retorna lista vacia cuando no hay datos
- GET /inbox retorna items ordenados por completitud ASC
- GET /inbox/stats retorna contadores correctos
- PATCH /inbox/{id} actualiza campos correctamente
- POST /inbox/{id}/confirmar cambia estado a "confirmada"
- POST /inbox/{id}/confirmar con categoria distinta crea regla
- POST /inbox/{id}/confirmar dos veces es idempotente (no duplica)
- POST /inbox/{id}/descartar cambia estado a "anulada"
- POST /inbox/confirmar-lote confirma todos los ids del body
- GET /inbox/{id_inexistente} retorna 404

---

## Dependencias con otras entregas

**3A no depende de:**
- El ETL real (usa seed de datos dummy)
- El frontend (el backend es independiente)

**3B depende de 3A:**
- El prompt del ETL escribe en el schema que 3A implementa

**3C depende de 3A:**
- El frontend consume los endpoints que 3A implementa

---

*Documento generado Junio 2026 — Plataforma Financiera MCGHR*
*Leer junto con: docs/ETL_DISENO_FUNCIONAL.md, docs/DISENO_3B_ETL_PROMPT.md*
