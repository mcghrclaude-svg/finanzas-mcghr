# ETL -- Diseno Funcional
## Plataforma Financiera MCGHR

**Fecha:** Junio 2026
**Estado:** Aprobado -- pendiente implementacion
**Contexto:** Punto 3 del roadmap -- ingesta automatica de datos financieros

---

## Que es el ETL

El ETL (Extract, Transform, Load) es el componente que transforma datos no
estructurados (correos, PDFs, fotos, JSONs del celular) en transacciones
estructuradas en la base de datos SQLite.

**No es un script Python standalone.**
Es una tarea programada de Claude Desktop que usa los MCP tools configurados
en la PC para leer fuentes, razonar sobre los datos, y escribir en la DB.

**Motor de ejecucion:** Claude Desktop con tarea programada via /schedule
**Schedule:** Todos los dias a las 4:00 AM
**MCPs que usa:**
- `mcp__sqlite__*` -- leer y escribir en finanzas.db (OneDrive)
- `mcp__mcp_lector_correos__*` -- leer correos Gmail de hernan y malu
- `mcp__filesystem__*` -- leer PDFs y JSONs de OneDrive, escribir archivos

---

## Fuentes de datos

### 1. Correos Gmail
- **Cuenta hernan:** ghrizzi.goog@gmail.com
- **Cuenta malu:** malu82@gmail.com
- **Que busca:** notificaciones de consumo TC/CC, facturas adjuntas, avisos
  de pago, cobros de suscripciones, transferencias, alertas bancarias
- **Bancos activos:** Bancolombia, BBVA, Banco de Occidente, Nequi
- **No marca correos como leidos**

### 2. PDFs en OneDrive
Carpeta monitoreada: `OneDrive\Finanzas MCGHR\Extractos\`

| Tipo | Banco | Titular | Frecuencia |
|---|---|---|---|
| Extracto TC | Banco de Occidente (5749) | GHR | Mensual |
| Statement | InteractiveBrokers | GHR | Mensual |
| Extracto TC/CC | Bancolombia | GHR | Mensual |
| Extracto TC/CC | BBVA | GHR | Mensual |

Los PDFs pueden tener password. El ETL usa el skill `desproteger_pdf`
antes de intentar leerlos.

### 3. JSONs de la PWA (inbox mobile)
Carpeta monitoreada: `OneDrive\Finanzas MCGHR\Inbox\`

Dos tipos de JSON que puede recibir:

**Tipo A -- Solo foto:**
```json
{
  "tipo": "foto_factura",
  "fecha_creacion": "2026-06-15T16:00:00-05:00",
  "dispositivo": "iphone_ghr",
  "archivo_foto": "factura_20260615_160000.jpg",
  "datos": {
    "fecha_foto": "2026-06-15T16:00:00-05:00"
  }
}
```

**Tipo B -- Foto + catalogacion del humano:**
```json
{
  "tipo": "foto_factura",
  "fecha_creacion": "2026-06-15T16:00:00-05:00",
  "dispositivo": "iphone_ghr",
  "archivo_foto": "factura_20260615_160000.jpg",
  "datos": {
    "fecha_foto": "2026-06-15T16:00:00-05:00",
    "monto": 45000,
    "moneda": "COP",
    "id_categoria": "ALIM-REST",
    "descripcion": "Almuerzo",
    "confirmado_humano": true
  }
}
```

En el Tipo B, los campos marcados con `confirmado_humano: true` se tratan
como firmes -- el ETL los usa como ancla y no los sobreescribe con su analisis.

---

## Modos de ejecucion

El ETL soporta dos modos. El modo se indica al invocar la tarea en Cowork.

### Modo incremental (default)

El ETL lee `MAX(fecha_inicio) FROM log_ejecuciones` para saber desde cuando
buscar correos y documentos nuevos. La dedup por `message_id` y nombre de
archivo en `correos_procesados` / `documentos` actua como segunda linea de
defensa: aunque la fecha desde sea imprecisa, un correo ya registrado no
se vuelve a procesar.

Este es el modo de las corridas automaticas diarias a las 4am.

### Modo rango (explicito)

Se invoca con `fecha_desde` y `fecha_hasta` explicitas. El ETL busca correos
y documentos dentro de ese rango en lugar de usar la ultima corrida.
La dedup sigue activa: si un correo ya esta en `correos_procesados`, no se
duplica aunque caiga dentro del rango.

Tres escenarios validos para este modo:

| Escenario | Por que se usa |
|---|---|
| Testing en desarrollo | Pruebas reproducibles sobre un periodo conocido |
| Carga inicial en produccion | No existe corrida previa en log_ejecuciones |
| Reproceso post-restore de DB | Re-ingestar el periodo posterior al backup |

En el escenario post-restore: si el backup incluia entradas en
`correos_procesados`, esos correos no se reprocesaran (correcto -- ya
estaban en la DB antes del restore). Solo se procesan los correos del
periodo no cubierto por el backup.

---

## Flujo de procesamiento

```
4:00 AM -- Arranca tarea programada Claude Desktop
    |
    +-- PASO 1: Leer estado actual
    |   Lee correos_procesados y inbox_mobile de la DB
    |   para saber que ya fue procesado y no reprocesar
    |
    +-- PASO 2: Correos Gmail (hernan + malu)
    |   Por cada cuenta:
    |     Buscar correos financieros nuevos (desde ultimo procesado)
    |     Por cada correo relevante:
    |       Extraer datos (monto, fecha, comercio, medio de pago)
    |       Descargar adjuntos PDF si los hay
    |       Desproteger PDF si tiene password
    |       Extraer texto del PDF
    |       Registrar en correos_procesados
    |
    +-- PASO 3: PDFs nuevos en OneDrive
    |   Listar archivos en Extractos/ no registrados en documentos
    |   Por cada PDF nuevo:
    |     Desproteger si tiene password
    |     Extraer texto
    |     Identificar banco, tipo, periodo, titular
    |     Extraer movimientos individuales
    |
    +-- PASO 4: JSONs nuevos de la PWA
    |   Listar JSONs en Inbox/ no registrados en inbox_mobile
    |   Por cada JSON nuevo:
    |     Leer datos estructurados del JSON
    |     Si tiene foto adjunta: leer la imagen
    |     Registrar en inbox_mobile
    |
    +-- PASO 5: Clasificar y correlacionar
    |   Para cada evento nuevo (correo / linea de extracto / JSON PWA):
    |     Leer contexto de la DB:
    |       - Ultimas 50 transacciones confirmadas por el humano
    |       - Reglas de clasificacion activas (reglas_clasificacion)
    |       - Catalogo de categorias, contrapartes, cuentas
    |     Clasificar: categoria, contraparte, cuenta, tipo
    |     Intentar correlacionar con transacciones existentes
    |       (ver seccion "Correlacion de eventos")
    |     Si correlaciona: enriquecer transaccion existente
    |     Si no: crear transaccion nueva en estado "pendiente"
    |
    +-- PASO 6: Exportar catalogo para PWA
        Generar JSON de categorias activas
        Escribir en OneDrive\Finanzas MCGHR\PWA\catalogos.json
```

---

## Correlacion de eventos

El mismo hecho economico puede llegar al ETL por multiples canales en momentos
distintos. El ETL debe reconocer que son el mismo hecho y no duplicarlos.

### Ejemplo concreto
1. Martes 10:00 -- llega correo de Bancolombia: "Compra con TC por COP 45.000
   en RAPPI"
2. Martes 10:05 -- llega correo de Rappi: factura adjunta con detalle de la
   orden, total COP 45.000
3. Fin de mes -- extracto TC Bancolombia tiene la linea: "RAPPI COP 45.000"

Los tres eventos describen un unico gasto. El ETL los debe unificar en una
sola transaccion enriquecida progresivamente.

### Mecanismo: ancla deterministica + busqueda por rango

La correlacion funciona en dos capas separadas con responsabilidades distintas.

**Capa 1 -- Deduplicacion de fuente (deterministica)**
Cada fuente tiene un ID natural que no cambia entre corridas:
- Correos Gmail: el `message_id` asignado por Gmail
- PDFs en OneDrive: el nombre del archivo (unico por banco y periodo)
- JSONs de la PWA: el nombre del archivo (unico por timestamp)

Antes de procesar cualquier evento, el ETL verifica si ese ID ya fue
registrado en `correos_procesados` (correos) o `documentos` (PDFs/fotos).
Si ya existe, lo saltea sin ejecutar ningun razonamiento. Esto garantiza
idempotencia: aunque el ETL corra dos veces sobre los mismos datos, no
crea duplicados.

**Capa 2 -- Correlacion entre fuentes (razonamiento LLM)**
Solo para eventos genuinamente nuevos (que pasaron la Capa 1), el ETL
busca si el hecho economico ya existe en la DB por un canal distinto.
Consulta transacciones con:
- Mismo titular
- Fecha dentro de +/- 3 dias
- Monto dentro de +/- 1%

Si hay candidatos, razona si alguno es el mismo hecho (ej: la notificacion
del banco y la factura de Rappi del mismo monto el mismo dia). Si decide
que si es el mismo, enriquece la transaccion existente y le asigna
un `id_evento` compartido. Si no hay match, crea una nueva con un
`id_evento` fresco.

El campo `id_evento` sigue existiendo en `transacciones` como ancla
que agrupa eventos del mismo hecho, pero ya no es un hash pre-calculado
-- es asignado por el ETL cuando decide que dos eventos son el mismo.

### Estado de enriquecimiento

Campo `estado_enriquecimiento` en `transacciones`:

| Estado | Descripcion |
|---|---|
| `inicial` | Solo tiene datos del primer evento (notificacion basica) |
| `enriquecido` | Tiene factura o detalle adicional, pero puede llegar mas |
| `completo` | Tiene extracto -- el ciclo contable esta cerrado |

### Casos de correlacion

**Caso 1 -- Notificacion + Factura (mismo dia)**
El ETL procesa el correo de Bancolombia (message_id nuevo: lo registra
y crea la transaccion). Luego procesa el correo de Rappi con la factura
adjunta (message_id nuevo tambien). Busca candidatos en la DB: misma
fecha, mismo monto 45.000, mismo titular GHR. Encuentra la transaccion
de Bancolombia. Razona: "RAPPI en Bancolombia + factura de Rappi por el
mismo monto el mismo dia = mismo hecho". Enriquece con la categoria
(ALIM-RAPPI) y los items del pedido. Estado pasa a `enriquecido`.

**Caso 2 -- Gasto no notificado, aparece en extracto**
El extracto de fin de mes tiene una linea que no estaba en la DB.
El ETL la crea como transaccion nueva con `estado_enriquecimiento = completo`
(porque vino del extracto, que es la fuente mas confiable).

**Caso 3 -- Extracto confirma gasto ya registrado**
El extracto tiene una linea que correlaciona con una transaccion existente.
El ETL actualiza `estado_enriquecimiento = completo` y confirma que el
medio de pago y monto son correctos. No crea transaccion nueva.

**Caso 4 -- Pago del extracto TC**
El pago del extracto de TC es una transferencia de CC a TC.
El ETL lo registra como `tipo = transferencia` entre las dos cuentas.
Este es el momento en que el gasto "sale de caja" -- hasta este punto
solo existia como deuda con el banco.

---

## Clasificacion con contexto

Antes de clasificar cada evento, el ETL lee de la DB:

1. **Reglas de clasificacion activas** -- patrones regex con categoria y
   contraparte asignados. Las reglas creadas por el humano tienen prioridad
   sobre las del sistema.

2. **Ultimas 50 transacciones confirmadas** -- ejemplos reales de como el
   humano clasifico eventos similares en el pasado. Estos se incluyen en
   el prompt de Claude Desktop como "few-shot examples".

3. **Catalogo completo** -- lista de categorias, contrapartes y cuentas
   disponibles para que Claude asigne IDs validos, no texto libre.

La clasificacion es un razonamiento de Claude Desktop, no un algoritmo
deterministico. Puede incluir logica del estilo: "este comercio lo clasifiqui
antes como ALIM-REST, pero el monto es 450.000 que es inusualmente alto para
un restaurante, podria ser una cena de negocios -- asigno confianza 0.70".

### Calculo de confianza

| Situacion | Confianza tipica |
|---|---|
| Regla exacta del humano matchea | 0.90 - 0.98 |
| Patron conocido, sin regla explicita | 0.75 - 0.89 |
| Comercio visto antes, datos distintos | 0.60 - 0.74 |
| Comercio desconocido, datos parciales | 0.40 - 0.59 |
| Datos muy incompletos | < 0.40 |

### Destino segun confianza

Toda transaccion va siempre a `pendiente` con `revisado_humano = 0`,
sin excepcion. El humano confirma todo manualmente desde el inbox.

La confianza sirve para dos cosas: ordenar la cola (mayor confianza
primero, para que el humano llegue rapido a los casos faciles) y
mostrar visualmente que tan seguro esta el ETL de su clasificacion.
No determina el estado final de ninguna transaccion.

---

## Aprendizaje por confirmacion

Cuando el humano confirma una transaccion en la app web y corrige la
categoria sugerida por el ETL, el sistema registra esa correccion en
`reglas_clasificacion` con `creada_por = 'humano'`.

En la siguiente ejecucion del ETL, esa regla ya esta disponible como
contexto. El ETL la ve en la lista de reglas activas y la aplica.

Las reglas del humano tienen siempre mas peso que las del sistema.
El campo `usos` en `reglas_clasificacion` sube con cada aplicacion exitosa,
lo que permite identificar las reglas mas confiables.

---

## Vinculacion de documentos

Todo documento relacionado con una transaccion se vincula en la tabla
`vinculos` con su tipo explicito. El ETL crea vinculos en tres situaciones:

| Documento | Origen | tipo_vinculo |
|---|---|---|
| PDF adjunto en correo (factura) | Gmail | `factura` |
| Foto de factura del celular | PWA JSON | `factura` |
| PDF de extracto TC/CC | OneDrive/Extractos | `extracto` |
| PDF statement IBKR | OneDrive/Extractos | `extracto` |

Cada vinculo referencia el `id` del documento en `documentos` y el `id`
de la transaccion en `transacciones`. Un extracto puede vincular multiples
transacciones (una por linea de movimiento).

---

## Registro de actividad

Por cada ejecucion el ETL escribe en `log_ejecuciones`:
- Fecha inicio y fin
- Cantidad de correos leidos por cuenta
- Cantidad de PDFs procesados
- Cantidad de JSONs de PWA procesados
- Transacciones nuevas creadas
- Transacciones enriquecidas
- Errores encontrados

Por cada correo procesado escribe en `correos_procesados`:
- ID del correo (para no reprocesarlo)
- Resultado: `ok | sin_datos | error | duplicado`

Por cada JSON de PWA procesado escribe en `inbox_mobile`:
- Nombre del archivo JSON
- Estado: `procesado | error`
- ID de la transaccion creada si aplica

---

## Cambios requeridos en el schema (v1.2)

La tabla `transacciones` necesita dos campos nuevos para soportar la
correlacion de eventos:

```sql
ALTER TABLE transacciones ADD COLUMN
    id_evento TEXT;
    -- Asignado por el ETL cuando decide que dos o mas eventos son el mismo
    -- hecho economico llegado por multiples canales (notificacion + factura
    -- + extracto). No es un hash precalculado.

ALTER TABLE transacciones ADD COLUMN
    estado_enriquecimiento TEXT DEFAULT 'inicial';
    -- inicial    -> primer evento registrado, puede llegar mas data
    -- enriquecido -> tiene datos adicionales (factura, detalle)
    -- completo   -> extracto confirmo el evento, ciclo cerrado
```

Estos cambios van en `schema/finanzas_v1_2.sql` como migracion incremental.

---

## Propuesta de entidades nuevas del catalogo

Cuando el ETL encuentra en un correo, PDF o foto una entidad que no existe
en el catalogo (una contraparte desconocida, un medio de pago no registrado,
una categoria que no matchea ninguna existente, una persona nueva), no deja
la FK nula silenciosamente ni inventa un ID. La propone para revision humana.

Aplica a todas las entidades del catalogo:
- `contrapartes` -- comercios o entidades nunca vistas
- `cuentas` -- medios de pago o cuentas bancarias nuevas
- `categorias` -- si el ETL cree que el gasto no encaja en ninguna existente
- `personas` -- titular o beneficiario no registrado

### Comportamiento del ETL (implementado -- ver PEN-004)

El mecanismo real no inserta la entidad propuesta directamente en la
tabla de catalogo correspondiente. Usa una tabla separada,
`entidades_potenciales` (columnas: id, tipo, valor_propuesto,
id_transaccion, estado, creado_en, resuelto_en -- definida en
`backend/models/catalogo.py`).

1. Detecta que la entidad no existe en el catalogo activo.
2. Crea un registro en `entidades_potenciales` con `estado = 'pendiente'`,
   `tipo` (contraparte | cuenta | categoria) y `valor_propuesto`, referenciando
   la transaccion via `id_transaccion`.
3. La transaccion queda en estado `pendiente` como siempre; la existencia
   de una EntidadPotencial asociada es lo que indica que tiene una
   propuesta sin confirmar.

### Comportamiento de la UX (implementado -- ver PEN-004)

El inbox muestra visualmente que la transaccion tiene una entidad
propuesta. El humano confirma o descarta la propuesta desde la app web,
resuelto por `backend/services/entidades_potenciales_service.py` y
expuesto en `backend/api/v1/routers/catalogos.py`:
- `GET /catalogos/pendientes` -- lista EntidadPotencial en estado pendiente
- `POST /catalogos/pendientes/{ep_id}/confirmar` -- crea la entrada real
  en el catalogo (Contraparte/Cuenta/Categoria) y confirma toda EP
  pendiente con el mismo tipo + valor_propuesto
- `POST /catalogos/pendientes/{ep_id}/descartar` -- descarta la propuesta

El fix del Issue #47 confirma este flujo en uso real (persistencia de
`id_contraparte` al confirmar una EP).

---

## Lo que el ETL NO hace

- No confirma transacciones automaticamente -- todo queda en pendiente
  para revision humana, sin excepcion independientemente de la confianza
- No modifica correos en Gmail (nunca marca como leido)
- No borra archivos de OneDrive
- No toca la DB de dev -- solo escribe en la DB de produccion en OneDrive
- No llama a Claude API -- usa Claude Desktop como motor de razonamiento

---

*Documento generado Junio 2026 -- Plataforma Financiera MCGHR*
*Leer junto con: docs/architecture.md, docs/schema_v1.md, docs/DISENO_3A_INBOX_BACKEND.md*
