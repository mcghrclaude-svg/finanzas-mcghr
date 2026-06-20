-- ============================================================================
-- finanzas_v1_2.sql
-- Migracion de schema -- Plataforma Finanzas MCGHR
-- ============================================================================
-- Version:  1.2
-- Fecha:    Junio 2026
-- Anterior: finanzas_v1_1.sql (v1.1)
--
-- CAMBIOS EN ESTA VERSION:
--   1. transacciones: +id_evento, +estado_enriquecimiento
--
-- PROPOSITO:
--   Permite al ETL (tarea programada Claude Desktop) correlacionar el
--   mismo hecho economico que llega por multiples canales en momentos
--   distintos:
--     - Notificacion de consumo TC (dia del gasto)
--     - Factura adjunta en correo (mismo dia o horas despues)
--     - Linea en extracto mensual (4 semanas despues)
--
--   En lugar de crear 3 transacciones duplicadas, el ETL agrupa los 3
--   eventos bajo el mismo id_evento y enriquece la transaccion existente.
--
-- COMO EJECUTAR:
--   Este script es INCREMENTAL -- modifica la BD existente sin borrar datos.
--   Ejecutar UNA SOLA VEZ sobre una BD que ya tiene finanzas_v1_1.sql aplicado.
--
--   Desde terminal (DB de produccion en OneDrive):
--   sqlite3 "C:\Users\ghriz\OneDrive\Finanzas MCGHR\Generales\finanzas.db" < schema/finanzas_v1_2.sql
--
--   Desde terminal (DB de dev):
--   sqlite3 data/dev/finanzas_dev.db < schema/finanzas_v1_2.sql
-- ============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;


-- ============================================================================
-- CAMBIO 1: transacciones -- campo id_evento
-- ============================================================================

-- id_evento: hash determinista generado por el ETL para identificar
-- el mismo hecho economico llegado por distintos canales.
--
-- Formato: "EVT_" + 16 caracteres hex (sha256 truncado de monto+cuenta+fecha+titular)
-- Tolerancia de fecha: +/- 3 dias para absorber diferencias entre la fecha
-- de notificacion y la fecha real del cargo.
--
-- NULL para:
--   - Transacciones manuales (el humano las crea directamente)
--   - Transacciones migradas de antes de v1.2
--   - Ingresos (no tienen correlacion multi-canal tipicamente)
ALTER TABLE transacciones ADD COLUMN
    id_evento TEXT DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_tx_id_evento
    ON transacciones(id_evento)
    WHERE id_evento IS NOT NULL;


-- ============================================================================
-- CAMBIO 2: transacciones -- campo estado_enriquecimiento
-- ============================================================================

-- estado_enriquecimiento: ciclo de vida de la completitud de una transaccion
-- desde el punto de vista del ETL.
--
-- inicial     -> primer evento registrado (notificacion basica)
--               Tiene: monto, cuenta, fecha aproximada
--               Le falta: categoria confirmada, factura, extracto
--
-- enriquecido -> llego informacion adicional que completo la transaccion
--               Tiene: categoria sugerida, contraparte, items (si Rappi/Exito)
--               Le puede faltar: confirmacion del extracto
--
-- completo    -> el extracto confirmo el evento
--               El ciclo contable queda cerrado.
--               Este es el estado mas confiable -- vino de la fuente definitiva.
ALTER TABLE transacciones ADD COLUMN
    estado_enriquecimiento TEXT DEFAULT 'inicial';
    -- inicial | enriquecido | completo


-- ============================================================================
-- FIN DE MIGRACION v1.2
-- Tablas modificadas: transacciones (+2 columnas)
-- Indices nuevos:     idx_tx_id_evento
-- ============================================================================
