-- ============================================================================
-- init_prod_desde_cero.sql
-- Bootstrap de una DB de produccion nueva, vacia (0 tablas).
-- ============================================================================
--
-- NO es un reemplazo de finanzas_v1_1.sql..v1_6.sql -- esos son migraciones
-- INCREMENTALES (ALTER TABLE, incluso un rebuild completo de transacciones
-- en v1_4.sql) que asumen que la tabla ya existe en su forma anterior.
-- Correrlos en orden contra una DB vacia falla en el primer ALTER TABLE.
--
-- El flujo real de arranque para una DB nueva es:
--   1. Levantar el backend apuntando a esta DB (.env.prod) UNA VEZ. El hook
--      de startup (backend/main.py) corre Base.metadata.create_all() y crea
--      TODAS las tablas modeladas en SQLAlchemy (transacciones, tramos,
--      asientos, categorias, cuentas, contrapartes, personas, monedas,
--      entidades_potenciales, presupuestos, periodos_financieros,
--      velocidad_historica, inversiones, valuaciones, obligaciones,
--      documentos, vinculos, inbox_mobile) ya con la forma ACTUAL de cada
--      modelo -- equivalente a tener v1_1..v1_6 aplicados de una, para esas
--      tablas.
--   2. Correr este script. Cubre lo que create_all() NO cubre: tablas y
--      vistas que solo existen como SQL crudo (nunca se modelaron en
--      SQLAlchemy) -- config_pwa_import, archivos_mobile_procesados,
--      log_ejecuciones_mobile, correos_procesados, log_ejecuciones, y las
--      vistas de reportes.
--
-- Ejecutar en ese orden (paso 1 antes que este script) o las vistas de mas
-- abajo fallan -- referencian columnas de transacciones/cuentas/tramos que
-- todavia no existirian.
--
-- Fuentes: schema/finanzas_v1_1.sql (items_transaccion, vistas),
--          schema/finanzas_v1_3.sql (correos_procesados, log_ejecuciones),
--          schema/finanzas_v1_5.sql (archivos_mobile_procesados,
--          log_ejecuciones_mobile), schema/finanzas_v1_6.sql (config_pwa_import,
--          forma final con "raices").
--
-- NOTA: v_reembolsos_pendientes se corrige aca -- la version original en
-- finanzas_v1_1.sql filtraba estado_reembolso IN ('pendiente', 'gestionado'),
-- pero el vocabulario real que quedo implementado en el modulo Transacciones
-- (frontend/src/modules/Transacciones/index.jsx) y en el enum de
-- backend/schemas/transaccion.py es pendiente|solicitado|recibido. Esta
-- vista nunca se consulto en produccion (reportes.py replica la logica en
-- SQLAlchemy en vez de usarla), asi que corregirla aca no rompe nada.
-- ============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;


-- ============================================================================
-- items_transaccion (finanzas_v1_1.sql)
-- ============================================================================
CREATE TABLE IF NOT EXISTS items_transaccion (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_transaccion      TEXT    NOT NULL REFERENCES transacciones(id)
                                ON DELETE CASCADE,
    descripcion         TEXT    NOT NULL,
    cantidad            REAL    NOT NULL DEFAULT 1,
    unidad              TEXT,
    precio_unitario     REAL,
    monto_total         REAL    NOT NULL,
    moneda              TEXT    NOT NULL DEFAULT 'COP' REFERENCES monedas(id),
    id_categoria        TEXT    REFERENCES categorias(id),
    id_contraparte      TEXT    REFERENCES contrapartes(id),
    notas               TEXT
);

CREATE INDEX IF NOT EXISTS idx_items_transaccion
    ON items_transaccion(id_transaccion);
CREATE INDEX IF NOT EXISTS idx_items_descripcion
    ON items_transaccion(descripcion);
CREATE INDEX IF NOT EXISTS idx_items_contraparte
    ON items_transaccion(id_contraparte);


-- ============================================================================
-- correos_procesados + log_ejecuciones (finanzas_v1_3.sql) -- ETL de correo
-- ============================================================================
CREATE TABLE IF NOT EXISTS correos_procesados (
    id_correo       TEXT    PRIMARY KEY,
    cuenta_gmail    TEXT    NOT NULL,
    fecha_correo    TEXT    NOT NULL,
    asunto          TEXT,
    remitente       TEXT,
    fecha_procesado TEXT    NOT NULL,
    resultado       TEXT    NOT NULL DEFAULT 'ok'
);

CREATE INDEX IF NOT EXISTS idx_cp_cuenta_fecha
    ON correos_procesados(cuenta_gmail, fecha_correo);

CREATE TABLE IF NOT EXISTS log_ejecuciones (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_inicio                TEXT    NOT NULL,
    fecha_fin                   TEXT,
    correos_leidos              INTEGER NOT NULL DEFAULT 0,
    transacciones_nuevas        INTEGER NOT NULL DEFAULT 0,
    transacciones_enriquecidas  INTEGER NOT NULL DEFAULT 0,
    documentos_nuevos           INTEGER NOT NULL DEFAULT 0,
    alertas                     TEXT    NOT NULL DEFAULT '{}',
    notas                       TEXT
);


-- ============================================================================
-- archivos_mobile_procesados + log_ejecuciones_mobile (finanzas_v1_5.sql)
-- ============================================================================
CREATE TABLE IF NOT EXISTS archivos_mobile_procesados (
    nombre_archivo          TEXT    PRIMARY KEY,
    dispositivo             TEXT    NOT NULL,
    fecha_archivo           TEXT    NOT NULL,
    tipo                    TEXT,
    fecha_procesado         TEXT    NOT NULL,
    resultado               TEXT    NOT NULL DEFAULT 'ok',
    id_transaccion_creada   TEXT
);

CREATE INDEX IF NOT EXISTS idx_amp_dispositivo_fecha
    ON archivos_mobile_procesados(dispositivo, fecha_archivo);

CREATE TABLE IF NOT EXISTS log_ejecuciones_mobile (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_inicio            TEXT    NOT NULL,
    fecha_fin               TEXT,
    archivos_leidos         INTEGER NOT NULL DEFAULT 0,
    transacciones_nuevas    INTEGER NOT NULL DEFAULT 0,
    duplicados              INTEGER NOT NULL DEFAULT 0,
    errores                 INTEGER NOT NULL DEFAULT 0,
    alertas                 TEXT    NOT NULL DEFAULT '{}',
    notas                   TEXT
);


-- ============================================================================
-- config_pwa_import -- forma final (finanzas_v1_6.sql), sin el historial
-- de migracion carpetas_gastos -> raices (nunca existio en esta DB).
-- ============================================================================
CREATE TABLE IF NOT EXISTS config_pwa_import (
    id                  INTEGER PRIMARY KEY CHECK (id = 1),
    intervalo_minutos   INTEGER NOT NULL DEFAULT 60,
    raices              TEXT    NOT NULL DEFAULT '[]',
    actualizado_en      TEXT
);

INSERT OR IGNORE INTO config_pwa_import (id, intervalo_minutos, raices)
VALUES (1, 60, '[]');


-- ============================================================================
-- Vistas de reportes (finanzas_v1_1.sql)
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
    c1.nombre           AS categoria,
    c1.id               AS id_categoria,
    c2.nombre           AS categoria2,
    cp.nombre           AS contraparte,
    p.nombre            AS quien_pago,
    COALESCE(cu.es_corporativa, 0) AS es_corporativo,
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
  AND t.estado_reembolso IN ('pendiente', 'solicitado')
ORDER BY t.fecha DESC;


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
-- FIN
-- ============================================================================
