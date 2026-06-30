-- ============================================================================
-- finanzas_v1_4b.sql
-- Migracion de schema -- Plataforma Finanzas MCGHR
-- ============================================================================
-- Version:  1.4b
-- Fecha:    Junio 2026
-- Anterior: finanzas_v1_4.sql
--
-- CAMBIOS EN ESTA VERSION:
--   1. NUEVA TABLA: archivos_mobile_procesados
--      Ancla deterministica del ETL para JSONs de la PWA mobile.
--      Analogo a correos_procesados (que cumple el mismo rol para Gmail).
--      El ETL verifica esta tabla antes de procesar un JSON (paso 3a) y
--      registra el archivo al terminar (paso 3f).
--      Separa la funcion de auditoria de ETL de inbox_mobile, que mantiene
--      su rol original como cola de propuestas de la PWA.
--
-- COMO EJECUTAR (INCREMENTAL -- una sola vez sobre DB con v1.4 aplicado):
--   sqlite3 data\dev\finanzas_dev.db < schema\finanzas_v1_4b.sql
-- ============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS archivos_mobile_procesados (
    nombre_archivo      TEXT    PRIMARY KEY,
    -- Nombre del archivo JSON (ej: "factura_20260615_160000.json").
    -- Es el ancla deterministica: unico por timestamp de dispositivo.
    -- Analogo a id_correo en correos_procesados.

    dispositivo         TEXT    NOT NULL,
    -- Dispositivo origen: "iphone_ghr" o "iphone_mc".
    -- Analogo a cuenta_gmail en correos_procesados.

    fecha_archivo       TEXT    NOT NULL,
    -- fecha_creacion del JSON (campo del archivo, no del procesamiento).
    -- Analogo a fecha_correo en correos_procesados.

    tipo                TEXT,
    -- Tipo de JSON: "foto_factura" u otros que defina la PWA en el futuro.
    -- Analogo a asunto en correos_procesados.

    fecha_procesado     TEXT    NOT NULL,
    -- ISO 8601. Cuando lo proceso el ETL en esta corrida.
    -- Analogo a fecha_procesado en correos_procesados.

    resultado           TEXT    NOT NULL DEFAULT 'ok',
    -- ok        -> se creo una transaccion
    -- sin_datos -> el JSON no tenia datos financieros utiles
    -- error     -> fallo al procesar
    -- duplicado -> el hecho economico ya existia (correlacion exitosa)
    -- Mismos valores que correos_procesados.resultado.

    id_transaccion_creada TEXT
    -- ID de la transaccion creada o enriquecida, si aplica.
    -- NULL si resultado != 'ok'. Sin analogo en correos_procesados
    -- (campo extra util para trazabilidad del JSON -> transaccion).
);

CREATE INDEX IF NOT EXISTS idx_amp_dispositivo_fecha
    ON archivos_mobile_procesados(dispositivo, fecha_archivo);
-- Analogo a idx_cp_cuenta_fecha en correos_procesados.

-- ============================================================================
-- FIN DE MIGRACION v1.4b
-- Tabla nueva: archivos_mobile_procesados
-- ============================================================================
