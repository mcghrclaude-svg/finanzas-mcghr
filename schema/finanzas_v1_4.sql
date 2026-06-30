-- ============================================================================
-- finanzas_v1_4.sql
-- Migracion de schema -- Plataforma Finanzas MCGHR
-- ============================================================================
-- Version:  1.4
-- Fecha:    Junio 2026
-- Anterior: finanzas_v1_3.sql
--
-- CAMBIOS EN ESTA VERSION:
--   1. NUEVA TABLA: vinculos
--      Vincula documentos (PDFs, fotos) a transacciones.
--      Creada por el ETL en pasos 1i (correos), 2d (PDFs OneDrive), 3g (PWA).
--
--   2. TABLA transacciones: agregar DEFAULT y CHECK en completitud
--      SQLite no soporta ALTER COLUMN -- requiere recreacion de la tabla.
--      completitud TEXT CHECK IN ('minimo','parcial','completo') DEFAULT 'minimo'
--      Todos los valores existentes (8 filas) son compatibles -- verificado
--      con SELECT el 2026-06-30 antes de aplicar esta migracion.
--
-- COMO EJECUTAR (INCREMENTAL -- una sola vez sobre DB con v1.3 aplicado):
--   sqlite3 data\dev\finanzas_dev.db < schema\finanzas_v1_4.sql
-- ============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

-- ============================================================================
-- PARTE 1: Recrear transacciones con CHECK + DEFAULT en completitud
-- ============================================================================

CREATE TABLE transacciones_new (
    id                          VARCHAR     NOT NULL PRIMARY KEY,
    fecha                       VARCHAR     NOT NULL,
    fecha_hora                  VARCHAR,
    tipo                        VARCHAR(20) NOT NULL,
    descripcion                 TEXT,
    para_quien                  VARCHAR,
    estado                      VARCHAR(20),
    confianza                   FLOAT,
    revisado_humano             INTEGER,
    completitud                 VARCHAR     NOT NULL DEFAULT 'minimo'
                                    CHECK(completitud IN ('minimo', 'parcial', 'completo')),
    id_categoria                VARCHAR,
    id_categoria2               VARCHAR,
    id_contraparte              VARCHAR,
    quien_pago                  VARCHAR,
    id_persona                  VARCHAR,
    es_recurrente               INTEGER,
    id_recurrencia              VARCHAR,
    es_reembolsable             INTEGER,
    estado_reembolso            VARCHAR,
    id_transaccion_reembolso    VARCHAR,
    fuente                      VARCHAR(30),
    id_correo                   VARCHAR,
    origen                      VARCHAR(20),
    id_evento                   VARCHAR,
    estado_enriquecimiento      VARCHAR(20),
    notas                       TEXT,
    fecha_procesado             VARCHAR,
    creado_en                   DATETIME,
    actualizado_en              DATETIME
);

INSERT INTO transacciones_new SELECT * FROM transacciones;

DROP TABLE transacciones;

ALTER TABLE transacciones_new RENAME TO transacciones;

-- ============================================================================
-- PARTE 2: Nueva tabla vinculos
-- ============================================================================

CREATE TABLE IF NOT EXISTS vinculos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    id_documento    TEXT    NOT NULL,
    id_transaccion  TEXT    NOT NULL,
    tipo_vinculo    TEXT    NOT NULL
                        CHECK(tipo_vinculo IN ('factura', 'extracto')),
    confianza       FLOAT,
    fecha_vinculo   TEXT    NOT NULL,
    creado_por      TEXT    NOT NULL DEFAULT 'claude',
    UNIQUE(id_documento, id_transaccion, tipo_vinculo)
);

CREATE INDEX IF NOT EXISTS idx_vinculos_transaccion
    ON vinculos(id_transaccion);

COMMIT;

PRAGMA foreign_keys = ON;

-- ============================================================================
-- FIN DE MIGRACION v1.4
-- Tabla nueva: vinculos
-- Tabla modificada: transacciones (completitud con DEFAULT y CHECK)
-- ============================================================================
