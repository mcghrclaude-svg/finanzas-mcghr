-- ============================================================================
-- finanzas_v1_7.sql
-- Migracion de schema -- Plataforma Finanzas MCGHR
-- ============================================================================
-- Version:  1.7
-- Fecha:    Septiembre 2026
-- Anterior: finanzas_v1_6.sql
--
-- CAMBIOS EN ESTA VERSION:
--   1. log_ejecuciones_mobile: nueva columna "actualizadas"
--      import_pwa_gastos.py ahora hace upsert cuando el id de un gasto de
--      la PWA ya existe como Transaccion (edicion re-subida desde la PWA,
--      ver pwa_import_service.py) en vez de solo marcarlo "duplicado" sin
--      tocarlo. Hace falta un contador propio, separado de
--      transacciones_nuevas/duplicados, para reflejar ese resultado en el
--      log de corridas.
--
-- COMO EJECUTAR (INCREMENTAL):
--   sqlite3 data\dev\finanzas_dev.db < schema\finanzas_v1_7.sql
-- ============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

ALTER TABLE log_ejecuciones_mobile ADD COLUMN actualizadas INTEGER NOT NULL DEFAULT 0;

-- ============================================================================
-- FIN DE MIGRACION v1.7
-- Tablas modificadas: log_ejecuciones_mobile (+ columna actualizadas)
-- ============================================================================
