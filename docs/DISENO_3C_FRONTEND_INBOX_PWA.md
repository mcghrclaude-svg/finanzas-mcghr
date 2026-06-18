# Frontend Inbox y Exportacion PWA — Diseño Funcional (Entrega 3C)
## Plataforma Financiera MCGHR

**Fecha:** Junio 2026
**Estado:** Aprobado — pendiente implementacion
**Entrega:** 3C — tercera de tres entregas del Punto 3
**Depende de:** Entregas 3A y 3B completadas y validadas

---

## Que incluye esta entrega

1. Pantalla Inbox en React (`frontend/src/modules/Inbox/`)
2. Endpoint de exportacion de catalogos para la PWA
3. Formato del JSON de catalogos que la PWA lee de OneDrive

---

## Pantalla Inbox

### Ubicacion
`frontend/src/modules/Inbox/index.jsx`
Reemplaza el placeholder actual (`<div>en desarrollo</div>`).

### Layout general

```
+--------------------------------------------------+
| INBOX                              [12 pendientes]|
| Ordenado por: necesitan atencion primero          |
+--------------------------------------------------+
| [Filtros: Todos | Email | PDF | Mobile | Manual]  |
+--------------------------------------------------+
| ALTA PRIORIDAD (confianza < 0.60)                 |
| +----------------------------------------------+ |
| | ? Transferencia bancaria       COP 1.200.000  | |
| |   Bancolombia CC -> ?          15 jun 2026    | |
| |   Sin categoria asignada       confianza: 45% | |
| |   [Editar y confirmar]  [Descartar]           | |
| +----------------------------------------------+ |
|                                                  |
| PARA REVISAR (confianza 0.60 - 0.84)             |
| +----------------------------------------------+ |
| | ~ Rappi                        COP 45.000     | |
| |   Bancolombia TC GHR           15 jun 2026    | |
| |   Alimentacion > Delivery      confianza: 78% | |
| |   [Confirmar]  [Editar]  [Descartar]          | |
| +----------------------------------------------+ |
|                                                  |
| LISTOS PARA CONFIRMAR (confianza >= 0.85)        |
| +----------------------------------------------+ |
| | v Netflix                      COP 42.900     | |
| |   BBVA TC GHR                  22 jun 2026    | |
| |   Ocio > Suscripciones         confianza: 96% | |
| |   [Confirmar]  [Editar]  [Descartar]          | |
| +----------------------------------------------+ |
|                                                  |
| [Confirmar todos los listos (3)]                 |
+--------------------------------------------------+
```

### Comportamiento por seccion

**Alta prioridad** (confianza < 0.60):
- Badge rojo con "!" en el icono
- El ETL no pudo clasificar bien — requiere decision del humano
- No tiene boton "Confirmar" directo — debe pasar por "Editar y confirmar"

**Para revisar** (0.60 - 0.84):
- Badge amarillo con "~"
- El ETL tiene una propuesta pero no esta seguro
- Puede confirmarse directo o editarse primero

**Listos para confirmar** (>= 0.85):
- Badge verde con "v"
- El ETL esta bastante seguro
- Boton "Confirmar" prominente
- Boton "Confirmar todos los listos" al pie para confirmar el lote

### Modal de edicion

Al presionar "Editar" o "Editar y confirmar" se abre un panel lateral
(no un modal — para poder ver la lista al mismo tiempo en desktop):

```
+---------------------------+
| EDITAR TRANSACCION        |
+---------------------------+
| Fecha:  [15 jun 2026   ]  |
| Monto:  [45.000        ]  |
| Moneda: [COP           ]  |
|                           |
| Categoria:                |
| [Alimentacion > Delivery] |
|                           |
| Contraparte:              |
| [Rappi                 ]  |
|                           |
| Cuenta:                   |
| [Bancolombia TC GHR    ]  |
|                           |
| Descripcion:              |
| [Pedido Rappi          ]  |
|                           |
| [_] Es reembolsable       |
|                           |
| Origen: email (ver raw)   |
|                           |
| [Confirmar] [Cancelar]    |
+---------------------------+
```

### Undo

Cada confirmacion o descarte es reversible hasta que el usuario cierra
la pantalla o navega a otro modulo. El stack de Undo de Zustand registra
cada accion.

Indicador visible: "3 acciones pendientes de guardar — [Deshacer]"

### Reglas de Tailwind — consistencia con el resto de la app

- Misma paleta que el resto: slate para texto, emerald para acciones
  positivas, amber para advertencias, rose para descartar
- Sin CSS custom, sin variables --color-*
- Cards con `rounded-lg border border-slate-200 bg-white shadow-sm`
- Botones con `rounded-md px-3 py-1.5 text-sm font-medium`

---

## Endpoint exportacion catalogos para PWA

### GET /api/v1/catalogos/export/pwa

Genera el JSON de catalogos y lo escribe en OneDrive.
La PWA lee ese archivo desde OneDrive — no llama a este endpoint
directamente.

**Cuando se llama:**
- Automaticamente cada vez que el humano modifica el catalogo
  (nueva categoria, nueva contraparte, etc.)
- Manualmente desde la pantalla de Catalogos con boton
  "Actualizar datos del celular"

**Response:**
```json
{
  "ok": true,
  "ruta_archivo": "C:/Users/ghriz/OneDrive/Finanzas MCGHR/PWA/catalogos.json",
  "generado_en": "2026-06-15T10:30:00-05:00",
  "categorias": 25,
  "contrapartes": 22
}
```

### Formato del archivo catalogos.json

```json
{
  "version": "1.0",
  "generado_en": "2026-06-15T10:30:00-05:00",
  "categorias": [
    {
      "id": "ALIM",
      "nombre": "Alimentacion",
      "nivel": 1,
      "hijos": [
        {
          "id": "ALIM-SUPER",
          "nombre": "Supermercado",
          "nivel": 2,
          "tipo_patron_gasto": "variable_frecuente"
        },
        {
          "id": "ALIM-REST",
          "nombre": "Restaurantes",
          "nivel": 2,
          "tipo_patron_gasto": "variable_frecuente"
        }
      ]
    }
  ],
  "contrapartes": [
    {
      "id": "CP_rappi",
      "nombre": "Rappi",
      "tipo": "COMERCIO"
    }
  ],
  "cuentas": [
    {
      "id": "BCO-TC-GHR",
      "nombre": "Bancolombia TC",
      "tipo": "TC",
      "titular": "GHR"
    }
  ]
}
```

Solo incluye categorias, contrapartes y cuentas activas.
La PWA usa este JSON para mostrar los selectores de categoria y
contraparte cuando el humano quiere catalogar una foto antes de subirla.

---

## Sobre la PWA

La PWA en si (el codigo que corre en el iPhone) es una entrega futura
separada. Esta entrega 3C solo prepara la infraestructura del lado del
backend/servidor que la PWA necesitara:

- El endpoint de exportacion de catalogos
- El formato del JSON de catalogos
- El formato de los JSONs que la PWA debe escribir en OneDrive
  (ya documentado en ETL_DISENO_FUNCIONAL.md)

El codigo de la PWA (React instalable en iPhone via Safari) se diseña
e implementa como Entrega 4.

---

*Documento generado Junio 2026 — Plataforma Financiera MCGHR*
*Leer junto con: docs/ETL_DISENO_FUNCIONAL.md, docs/DISENO_3A_INBOX_BACKEND.md*
