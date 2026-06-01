# Schema Finanzas MCGHR — v1
## Base de datos SQLite con doble entrada contable, multi-moneda, patrimonio neto

Aprobado: Mayo 2026  
Estado: Pendiente implementacion SQL

---

## Principios de diseño

- **Doble entrada contable:** cada movimiento genera debitos y creditos. La suma siempre balancea.
- **Multi-moneda:** cada cuenta tiene su moneda base. Los tramos registran tipo de cambio exacto.
- **Multi-tramo:** una transferencia puede tener N legs (ej: IBKR → Citi → Bancolombia = 3 tramos).
- **Patrimonio neto:** posiciones calculadas desde asientos + valuaciones de mercado para activos.
- **Etiquetas universales:** cualquier entidad del sistema puede ser taggeada con hashtags libres.
- **Timestamps con timezone:** ISO 8601 con offset explícito para campos con hora. DATE simple para fechas sin hora.

---

## Mapa de tablas — 6 grupos

```
GRUPO 1: CATALOGOS
  monedas
  cuentas
  categorias
  personas
  contrapartes
  etiquetas

GRUPO 2: PRESUPUESTO
  presupuestos

GRUPO 3: OBLIGACIONES
  obligaciones
  cuotas_obligacion

GRUPO 4: MOVIMIENTOS (nucleo contable)
  transacciones
  tramos
  asientos

GRUPO 5: ACTIVOS Y PATRIMONIO
  posiciones
  valuaciones

GRUPO 6: DOCUMENTOS Y VINCULOS
  documentos
  etiquetas_entidades
  vinculos

SOPORTE
  correos_procesados
  reglas_clasificacion
  log_ejecuciones
```

---

## GRUPO 1 — Catalogos

### monedas
```
id              TEXT PK        Ejemplos: "COP", "USD", "ARS", "USDT", "EUR"
nombre          TEXT           Ejemplo: "Peso colombiano"
simbolo         TEXT           Ejemplo: "$", "US$", "USDT"
es_crypto       INTEGER        0/1
activa          INTEGER        0/1
```

### cuentas
Cada medio de pago, cuenta bancaria, wallet, o posicion en activo es una cuenta.

```
id              TEXT PK        Ejemplos: "BC_CC_GHR", "IBKR_USD", "BINANCE_USDT"
nombre          TEXT           Ejemplo: "Bancolombia CC Hernan"
tipo            TEXT           checking | savings | credit_card | investment
                               | crypto | cash | loan | fund | rsu_unvested | other
subtipo         TEXT           Libre. Ejemplos: "TC Visa", "Cuenta corriente", "USDT spot"
banco           TEXT           Ejemplos: "Bancolombia", "IBKR", "Binance", "BBVA Argentina"
pais            TEXT           Ejemplos: "CO", "US", "AR"
moneda_base     TEXT FK→monedas
titular         TEXT FK→personas
numero_cuenta   TEXT           Ultimos 4 digitos o identificador
activa          INTEGER        0/1
es_activo       INTEGER        0/1 — cuenta de activos (acciones, crypto, RSU)
es_pasivo       INTEGER        0/1 — cuenta de deuda (TC, credito)
notas           TEXT
```

Nota RSUs: cuentas de tipo rsu_unvested representan unidades prometidas no vested.
Se muestran como "patrimonio potencial futuro", separadas del patrimonio real.

### categorias
Jerarquia de 3 niveles maximo.

```
id              TEXT PK        Ejemplos: "ALIM", "ALIM_REST", "ALIM_REST_DEL"
nombre          TEXT           Ejemplo: "Delivery"
nivel           INTEGER        1, 2 o 3
id_padre        TEXT FK→categorias   NULL si nivel 1
activa          INTEGER        0/1
```

Ejemplo de jerarquia:
```
ALIM               Alimentacion                nivel 1
  ALIM_REST        Restaurantes                nivel 2
    ALIM_REST_DEL    Delivery                  nivel 3
    ALIM_REST_SAL    Salidas                   nivel 3
  ALIM_SUPER       Supermercado                nivel 2
TRANS              Transporte                  nivel 1
  TRANS_UBER         Uber / taxis              nivel 2
VIAJE              Viajes                      nivel 1
  VIAJE_HOTEL        Alojamiento               nivel 2
  VIAJE_TRANSP       Transporte                nivel 2
INGRESO            Ingresos                    nivel 1
  INGRESO_SAL        Salarios                  nivel 2
  INGRESO_INV        Rendimiento inversiones   nivel 2
  INGRESO_PREST      Prestamos recibidos       nivel 2
INVERSION          Inversiones                 nivel 1
  INV_ACCIONES       Acciones                  nivel 2
  INV_CRYPTO         Crypto                    nivel 2
```

### personas
Solo personas fisicas que participan en "quien pago / para quien".

```
id              TEXT PK        Ejemplos: "GHR", "MC", "HIJO1"
nombre          TEXT           Ejemplo: "Hernan Rizzi"
es_titular      INTEGER        0/1 — si tiene cuentas propias en el sistema
activa          INTEGER        0/1
```

### contrapartes
Empresas, comercios y entidades con las que se transacciona.

```
id              TEXT PK        Ejemplos: "RAPPI", "NETFLIX", "DIAN", "BANCOLOMBIA"
nombre          TEXT           Ejemplo: "Rappi Colombia"
tipo            TEXT           comercio | banco | gobierno | inversion | otro
pais            TEXT           "CO", "US", etc.
activa          INTEGER        0/1
notas           TEXT
```

### etiquetas
Hashtags libres aplicables a cualquier entidad del sistema.

```
id              INTEGER PK autoincrement
nombre          TEXT UNIQUE    Ejemplos: "viajeCTGJunio2026", "almuerzoPareja"
color           TEXT           Para visualizacion en app web
fecha_creacion  TEXT           DATE
```

---

## GRUPO 2 — Presupuesto

### presupuestos
```
id              INTEGER PK autoincrement
anio            INTEGER        Ejemplo: 2026
mes             INTEGER        Ejemplo: 6
id_categoria    TEXT FK→categorias
monto_cop       REAL           Presupuesto en COP
monto_usd       REAL           Opcional, para categorias en USD
notas           TEXT
```

Nota: los presupuestos pueden tener etiquetas via etiquetas_entidades.
Ejemplo: presupuesto de alimentacion general + presupuesto de alimentacion con etiqueta viajeCTG2026.

---

## GRUPO 3 — Obligaciones

### obligaciones
```
id              TEXT PK        Ejemplo: "CRED_BC_AUTO_2024"
nombre          TEXT           Ejemplo: "Credito auto Bancolombia"
tipo            TEXT           mortgage | personal | auto | credit_card | other
id_cuenta       TEXT FK→cuentas
capital_original REAL
moneda          TEXT FK→monedas
tasa_interes    REAL           Porcentaje anual
fecha_inicio    TEXT           DATE
fecha_fin       TEXT           DATE
cuotas_total    INTEGER
estado          TEXT           activo | pagado | refinanciado
notas           TEXT
```

### cuotas_obligacion
```
id              INTEGER PK autoincrement
id_obligacion   TEXT FK→obligaciones
numero_cuota    INTEGER
fecha_vencimiento TEXT         DATE
monto_total     REAL
capital         REAL
interes         REAL
seguro          REAL
otros_cargos    REAL
fecha_pago      TEXT           ISO 8601 con offset. NULL si no pagada.
id_transaccion  TEXT FK→transacciones
estado          TEXT           pendiente | pagado | vencido
```

---

## GRUPO 4 — Movimientos (nucleo contable)

### transacciones
Cabecera del evento economico. Puede tener multiples tramos.

```
id              TEXT PK        UUID o hash
fecha           TEXT           DATE — fecha del evento (no del procesamiento)
fecha_hora      TEXT           ISO 8601 con offset. Ejemplo: "2026-06-15T16:00:00-05:00"
tipo            TEXT           gasto | ingreso | transferencia | ajuste
                               | inversion | devolucion
descripcion     TEXT           Ejemplo: "Almuerzo Andres Carne de Res"
id_categoria    TEXT FK→categorias    NULL para transferencias puras
id_categoria2   TEXT FK→categorias    Segunda categoria opcional
id_contraparte  TEXT FK→contrapartes
quien_pago      TEXT FK→personas
para_quien      TEXT           "GHR" | "MC" | "ambos" | "HIJO1"
es_recurrente   INTEGER        0/1
id_recurrencia  TEXT           Agrupa pagos recurrentes del mismo tipo
estado          TEXT           confirmado | pendiente | rechazado | anulado
confianza       REAL           0.0-1.0
revisado_humano INTEGER        0/1
fuente          TEXT           "gmail_hernan" | "sms_bc" | "manual" | "foto_factura"
id_correo       TEXT           ID del correo fuente en Gmail
notas           TEXT
fecha_procesado TEXT           ISO 8601 con offset
```

### tramos
```
id              INTEGER PK autoincrement
id_transaccion  TEXT FK→transacciones
numero_orden    INTEGER        1, 2, 3... orden en la cadena
id_cuenta_origen    TEXT FK→cuentas   NULL si es ingreso externo
id_cuenta_destino   TEXT FK→cuentas   NULL si es gasto externo
monto_origen    REAL
moneda_origen   TEXT FK→monedas
monto_destino   REAL
moneda_destino  TEXT FK→monedas
tipo_cambio     REAL           monto_destino / monto_origen
comision        REAL
moneda_comision TEXT FK→monedas
fecha_tramo     TEXT           ISO 8601 con offset
descripcion     TEXT
estado          TEXT           confirmado | pendiente | rechazado
```

### asientos
```
id              INTEGER PK autoincrement
id_tramo        INTEGER FK→tramos
id_cuenta       TEXT FK→cuentas
tipo            TEXT           debito | credito
monto           REAL           Siempre positivo
moneda          TEXT FK→monedas
fecha           TEXT           ISO 8601 con offset
```

Regla invariante: para cada tramo, suma de debitos = suma de creditos.

---

## GRUPO 5 — Activos y patrimonio

### posiciones
Vista materializada. Se recalcula desde asientos. No es fuente de verdad.

```
id_cuenta           TEXT PK FK→cuentas
saldo               REAL
moneda              TEXT FK→monedas
cantidad_activo     REAL           Para acciones/crypto: unidades en cartera
precio_promedio     REAL           Precio promedio de compra
fecha_vesting       TEXT           DATE. Solo para rsu_unvested.
ultima_actualizacion TEXT          ISO 8601 con offset
```

### valuaciones
```
id              INTEGER PK autoincrement
id_cuenta       TEXT FK→cuentas
fecha           TEXT           DATE
precio_usd      REAL
precio_cop      REAL
fuente          TEXT           "manual" | "correo_IBKR" | "binance_statement"
```

---

## GRUPO 6 — Documentos y vinculos

### documentos
```
id              TEXT PK        Hash MD5
nombre_original TEXT
ruta_local      TEXT           Ruta en OneDrive
tipo            TEXT           extracto | factura | foto_factura | correo
                               | comprobante | estado_cuenta | otro
mime_type       TEXT
tamano_bytes    INTEGER
hash_md5        TEXT
fecha_documento TEXT           DATE
fecha_descarga  TEXT           ISO 8601 con offset
fuente          TEXT           "gmail_hernan" | "foto_iphone" | "manual"
id_correo       TEXT
estado          TEXT           vinculado | sin_vincular | descartado
notas           TEXT
```

### etiquetas_entidades
Tabla universal. Permite taggear cualquier entidad del sistema.

```
id_etiqueta     INTEGER FK→etiquetas
entidad_tipo    TEXT           "transaccion" | "presupuesto" | "obligacion"
                               | "posicion" | "documento" | "cuenta"
entidad_id      TEXT           ID de la entidad
PRIMARY KEY (id_etiqueta, entidad_tipo, entidad_id)
```

### vinculos
```
id              INTEGER PK autoincrement
id_documento    TEXT FK→documentos
id_transaccion  TEXT FK→transacciones
tipo_vinculo    TEXT           "comprobante" | "extracto" | "factura" | "sms"
confianza       REAL
fecha_vinculo   TEXT           ISO 8601 con offset
creado_por      TEXT           "claude" | "humano"
```

---

## TABLAS DE SOPORTE

### correos_procesados
```
id_correo       TEXT PK
cuenta_gmail    TEXT
fecha_correo    TEXT           DATE
asunto          TEXT
remitente       TEXT
fecha_procesado TEXT           ISO 8601 con offset
resultado       TEXT           "ok" | "sin_datos" | "error" | "duplicado"
```

### reglas_clasificacion
```
id              INTEGER PK autoincrement
patron_remitente TEXT
patron_asunto   TEXT
patron_contenido TEXT
id_categoria    TEXT FK→categorias
id_cuenta       TEXT FK→cuentas
id_contraparte  TEXT FK→contrapartes
confianza_base  REAL
usos            INTEGER
fecha_creacion  TEXT           DATE
creada_por      TEXT           "claude" | "humano"
```

### log_ejecuciones
```
id              INTEGER PK autoincrement
fecha_inicio    TEXT           ISO 8601 con offset
fecha_fin       TEXT           ISO 8601 con offset
correos_leidos  INTEGER
transacciones_nuevas INTEGER
documentos_nuevos INTEGER
alertas         TEXT           JSON con alertas generadas
notas           TEXT
```

---

## Decisiones de diseno registradas

| Decision | Resultado | Razon |
|---|---|---|
| Modelo contable | Doble entrada | Balance patrimonial real y rastreo completo |
| Transferencias | Multi-tramo con legs | Evita doble contabilizacion, trazabilidad completa |
| Binance / IBKR | Mismo modelo | Ambos son cuentas de activos con posiciones |
| RSUs | Cuenta tipo rsu_unvested | Patrimonio potencial separado del real |
| Etiquetas | Tabla universal etiquetas_entidades | Cualquier entidad taggeable |
| Categorias | Jerarquico 3 niveles + categoria2 opcional | Cubre doble categoria sin N:N |
| Personas vs comercios | Tablas separadas | Conceptualmente distintos |
| Timestamps | ISO 8601 con offset | Correcto entre Colombia y Argentina |
| Posiciones | Vista materializada desde asientos | Auditoria recalculable |
| Presupuesto | Variable por categoria con etiquetas | General + por proyecto/viaje |

---

## Proximos pasos

- [ ] Generar SQL de creacion de tablas
- [ ] Definir datos iniciales del catalogo (cuentas, monedas, personas, contrapartes)
- [ ] Disenar prompt de sesion para procesamiento de correos en Claude Desktop
- [ ] Implementar app web local Flask para revision humana (Fase 2)
