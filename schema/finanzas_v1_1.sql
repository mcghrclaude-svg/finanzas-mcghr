-- ============================================================================
-- finanzas_v1_1.sql
-- Migracion de schema — Plataforma Finanzas MCGHR
-- ============================================================================
-- Version:  1.1
-- Fecha:    Junio 2026
-- Anterior: finanzas_v1.sql (v1.0)
--
-- CAMBIOS EN ESTA VERSION:
--   1. transacciones: +completitud, +es_reembolsable, +estado_reembolso,
--                     +id_transaccion_reembolso
--   2. documentos:    +origen_dispositivo
--   3. cuentas:       +es_corporativa
--   4. NUEVA TABLA:   items_transaccion
--   5. NUEVA TABLA:   inbox_mobile
--
-- COMO EJECUTAR:
--   Este script es INCREMENTAL — modifica la BD existente sin borrar datos.
--   Ejecutar UNA SOLA VEZ sobre una BD que ya tiene finanzas_v1.sql aplicado.
--
--   Desde Claude Desktop (Cowork):
--   "Ejecuta el archivo finanzas_v1_1.sql en finanzas.db usando el MCP sqlite."
--
--   Desde terminal:
--   sqlite3 "C:\Users\ghriz\OneDrive\Finanzas MCGHR\Generales\finanzas.db" < finanzas_v1_1.sql
-- ============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;


-- ============================================================================
-- CAMBIO 1: transacciones — nuevas columnas
-- ============================================================================

-- completitud: estado de llenado del registro.
--   minimo    → solo fecha, monto y cuenta (captura rapida desde mobile)
--   parcial   → tiene categoria y contraparte, faltan items o documentos
--   completo  → revisado con todos los campos relevantes llenos
ALTER TABLE transacciones ADD COLUMN
    completitud             TEXT    NOT NULL DEFAULT 'completo';
    -- Los registros existentes se marcan completo por defecto.
    -- La app mobile crea registros con completitud = 'minimo'.

-- es_reembolsable: checkbox "este gasto lo reembolsa el empleador".
--   Cuando es 1, el gasto aparece en reportes con flag visible
--   y puede excluirse de los analisis de gastos personales.
ALTER TABLE transacciones ADD COLUMN
    es_reembolsable         INTEGER NOT NULL DEFAULT 0;

-- estado_reembolso: ciclo de vida del reembolso.
--   NULL        → no aplica (es_reembolsable = 0)
--   pendiente   → hay que gestionar el reembolso
--   gestionado  → se gestiono, esperando el dinero
--   reembolsado → el dinero llegó, ciclo cerrado
ALTER TABLE transacciones ADD COLUMN
    estado_reembolso        TEXT    DEFAULT NULL;
    -- CHECK omitido en ALTER TABLE (SQLite no lo soporta en ADD COLUMN
    -- con expresiones). Se valida en la aplicacion.

-- id_transaccion_reembolso: apunta al ingreso que cerro el reembolso.
--   Permite rastrear "este almuerzo corporativo fue reembolsado por
--   esta transferencia del 15 de junio".
ALTER TABLE transacciones ADD COLUMN
    id_transaccion_reembolso TEXT   DEFAULT NULL
    REFERENCES transacciones(id);

-- Indice para el dashboard de reembolsos pendientes
CREATE INDEX IF NOT EXISTS idx_tx_reembolso
    ON transacciones(es_reembolsable, estado_reembolso)
    WHERE es_reembolsable = 1;


-- ============================================================================
-- CAMBIO 2: documentos — nueva columna
-- ============================================================================

-- origen_dispositivo: distingue el canal de origen del documento.
--   pc          → subido desde la PC (flujo normal)
--   iphone_ghr  → foto subida desde el iPhone de Hernan
--   iphone_mc   → foto subida desde el iPhone de Martha
--   automatico  → descargado automaticamente por Claude Desktop
ALTER TABLE documentos ADD COLUMN
    origen_dispositivo      TEXT    DEFAULT 'automatico';


-- ============================================================================
-- CAMBIO 3: cuentas — nueva columna
-- ============================================================================

-- es_corporativa: identifica tarjetas y cuentas del empleador.
--   Las transacciones con cuentas corporativas se excluyen
--   automaticamente de los analisis de gastos personales.
ALTER TABLE cuentas ADD COLUMN
    es_corporativa          INTEGER NOT NULL DEFAULT 0;


-- ============================================================================
-- NUEVA TABLA: items_transaccion
-- Detalle a nivel de item de facturas itemizadas (Rappi, Exito, Carulla).
-- Solo se llena cuando hay factura con detalle — no es obligatorio.
-- Permite analisis como "cuanto gaste en aguacates" o
-- "comparar precio de leche entre Exito y Carulla".
-- ============================================================================
CREATE TABLE IF NOT EXISTS items_transaccion (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_transaccion      TEXT    NOT NULL REFERENCES transacciones(id)
                                ON DELETE CASCADE,
    descripcion         TEXT    NOT NULL,   -- "Aguacate Hass x3", "Domicilio Rappi"
    cantidad            REAL    NOT NULL DEFAULT 1,
    unidad              TEXT,               -- "kg", "unidad", "litro", "servicio"
    precio_unitario     REAL,               -- Precio por unidad
    monto_total         REAL    NOT NULL,   -- cantidad * precio_unitario (o total si no hay desglose)
    moneda              TEXT    NOT NULL DEFAULT 'COP' REFERENCES monedas(id),
    id_categoria        TEXT    REFERENCES categorias(id),   -- Puede diferir de la transaccion padre
    id_contraparte      TEXT    REFERENCES contrapartes(id), -- Para items de marketplaces
    notas               TEXT
);

CREATE INDEX IF NOT EXISTS idx_items_transaccion
    ON items_transaccion(id_transaccion);

CREATE INDEX IF NOT EXISTS idx_items_descripcion
    ON items_transaccion(descripcion);     -- Para buscar "aguacate" en todos los registros

CREATE INDEX IF NOT EXISTS idx_items_contraparte
    ON items_transaccion(id_contraparte);  -- Para comparar precios por comercio


-- ============================================================================
-- NUEVA TABLA: inbox_mobile
-- Registro de JSONs generados por la app mobile y su estado de procesamiento.
-- La app mobile escribe JSONs en OneDrive/Generales/Inbox/.
-- Claude Desktop los procesa y registra aqui el resultado.
-- Evita reprocesar el mismo archivo si Claude Desktop corre varias veces.
--
-- Tipos de JSON que maneja el Inbox:
--   tx_nuevo      → transaccion nueva (minimo o parcial)
--   catalogo_add  → agregar contraparte, categoria u otro elemento al catalogo
--   tx_edicion    → edicion de una transaccion existente
--   doc_foto      → foto de factura para vincular a una transaccion
-- ============================================================================
CREATE TABLE IF NOT EXISTS inbox_mobile (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_archivo      TEXT    NOT NULL UNIQUE,  -- Nombre del JSON en OneDrive/Inbox/
    tipo                TEXT    NOT NULL,
                        -- tx_nuevo | catalogo_add | tx_edicion | doc_foto
    fecha_creacion      TEXT    NOT NULL,          -- ISO 8601 con offset (cuando lo creo la app)
    fecha_procesado     TEXT,                      -- ISO 8601 con offset (cuando lo proceso Claude)
    estado              TEXT    NOT NULL DEFAULT 'pendiente',
                        -- pendiente | procesado | error | descartado
    id_entidad_creada   TEXT,                      -- ID de la transaccion u objeto creado
    error_detalle       TEXT,                      -- Descripcion del error si estado = 'error'
    contenido_json      TEXT                       -- Copia del JSON procesado (para auditoria)
);

CREATE INDEX IF NOT EXISTS idx_inbox_estado
    ON inbox_mobile(estado)
    WHERE estado = 'pendiente';  -- Solo indexa pendientes para procesamiento rapido


-- ============================================================================
-- ACTUALIZACION DE VISTAS
-- Las vistas existentes se recrean para incorporar los nuevos campos.
-- ============================================================================

DROP VIEW IF EXISTS v_transacciones_completas;
CREATE VIEW v_transacciones_completas AS
SELECT
    t.id,
    t.fecha,
    t.fecha_hora,
    t.tipo,
    t.descripcion,
    t.para_quien,
    t.estado,
    t.completitud,
    t.confianza,
    t.revisado_humano,
    t.es_reembolsable,
    t.estado_reembolso,
    t.fuente,
    t.notas,
    -- Categoria principal
    c1.nombre           AS categoria,
    c1.id               AS id_categoria,
    -- Categoria secundaria
    c2.nombre           AS categoria2,
    -- Contraparte
    cp.nombre           AS contraparte,
    -- Quien pago
    p.nombre            AS quien_pago,
    -- Es gasto corporativo (cuenta origen es corporativa)
    COALESCE(cu.es_corporativa, 0) AS es_corporativo,
    -- Monto del primer tramo
    tr.monto_origen     AS monto,
    tr.moneda_origen    AS moneda,
    CASE
        WHEN tr.moneda_origen = 'COP' THEN tr.monto_origen
        ELSE tr.monto_origen * tr.tipo_cambio
    END                 AS monto_cop_estimado
FROM transacciones t
LEFT JOIN categorias    c1  ON t.id_categoria   = c1.id
LEFT JOIN categorias    c2  ON t.id_categoria2  = c2.id
LEFT JOIN contrapartes  cp  ON t.id_contraparte = cp.id
LEFT JOIN personas      p   ON t.quien_pago     = p.id
LEFT JOIN tramos        tr  ON t.id             = tr.id_transaccion
                            AND tr.numero_orden = 1
LEFT JOIN cuentas       cu  ON tr.id_cuenta_origen = cu.id;


-- Vista especifica para dashboard de reembolsos pendientes
CREATE VIEW IF NOT EXISTS v_reembolsos_pendientes AS
SELECT
    t.id,
    t.fecha,
    t.descripcion,
    t.estado_reembolso,
    cp.nombre           AS contraparte,
    p.nombre            AS quien_pago,
    cu.nombre           AS cuenta_pago,
    cu.es_corporativa,
    tr.monto_origen     AS monto,
    tr.moneda_origen    AS moneda,
    CASE
        WHEN tr.moneda_origen = 'COP' THEN tr.monto_origen
        ELSE tr.monto_origen * tr.tipo_cambio
    END                 AS monto_cop_estimado,
    t.notas
FROM transacciones t
LEFT JOIN contrapartes  cp  ON t.id_contraparte     = cp.id
LEFT JOIN personas      p   ON t.quien_pago         = p.id
LEFT JOIN tramos        tr  ON t.id                 = tr.id_transaccion
                            AND tr.numero_orden      = 1
LEFT JOIN cuentas       cu  ON tr.id_cuenta_origen  = cu.id
WHERE t.es_reembolsable = 1
  AND t.estado_reembolso IN ('pendiente', 'gestionado')
ORDER BY t.fecha DESC;


-- Vista de inbox pendiente de procesar
CREATE VIEW IF NOT EXISTS v_inbox_pendiente AS
SELECT
    id,
    nombre_archivo,
    tipo,
    fecha_creacion,
    estado
FROM inbox_mobile
WHERE estado = 'pendiente'
ORDER BY fecha_creacion ASC;


-- ============================================================================
-- FIN DE MIGRACION v1.1
-- Tablas modificadas:  transacciones, documentos, cuentas
-- Tablas nuevas:       items_transaccion, inbox_mobile
-- Vistas modificadas:  v_transacciones_completas
-- Vistas nuevas:       v_reembolsos_pendientes, v_inbox_pendiente
-- ============================================================================
