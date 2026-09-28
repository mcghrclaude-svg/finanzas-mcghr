-- ============================================================================
-- finanzas_v1_8.sql
-- Migracion de schema -- Plataforma Finanzas MCGHR
-- ============================================================================
-- Version:  1.8
-- Fecha:    Septiembre 2026
-- Anterior: finanzas_v1_7.sql
--
-- CAMBIOS EN ESTA VERSION:
--   1. obligaciones: nueva columna "saldo_pendiente" (carga manual por ahora
--      -- Obligacion solo tenia capital_inicial, el monto original del
--      prestamo, sin forma de saber cuanto falta pagar hoy). El diseno final
--      es que este saldo se derive de los pagos reales vinculados a la
--      obligacion (ver POST /obligaciones/{id}/registrar-pago), no de una
--      amortizacion teorica -- por eso arranca como campo editable a mano.
--   2. saldo_obligacion_historico: tabla nueva, una fila por cada vez que se
--      actualiza saldo_pendiente. Da una serie temporal real (aunque sea
--      rala) para el widget "Evolucion patrimonio" del Home, sin construir
--      amortizacion todavia.
--   3. config_home_widgets: tabla de configuracion de fila unica (mismo
--      criterio que config_pwa_import -- sin modelo SQLAlchemy, se lee/
--      escribe con SQL directo) para la preferencia "que widgets se ven" del
--      Home. Vive en el backend, no en localStorage.
--
-- COMO EJECUTAR (INCREMENTAL):
--   sqlite3 data\dev\finanzas_dev.db < schema\finanzas_v1_8.sql
-- ============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

ALTER TABLE obligaciones ADD COLUMN saldo_pendiente NUMERIC(18, 4);

CREATE TABLE saldo_obligacion_historico (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    id_obligacion  TEXT NOT NULL REFERENCES obligaciones(id),
    fecha          TEXT NOT NULL,             -- ISO 8601 con offset
    saldo          NUMERIC(18, 4) NOT NULL
);

CREATE INDEX idx_saldo_obligacion_historico_obligacion
    ON saldo_obligacion_historico(id_obligacion, fecha);

CREATE TABLE config_home_widgets (
    id                  INTEGER PRIMARY KEY CHECK (id = 1),
    insight_visible     BOOLEAN NOT NULL DEFAULT 1,
    patrimonio_visible  BOOLEAN NOT NULL DEFAULT 1,
    ask_visible         BOOLEAN NOT NULL DEFAULT 1
);

INSERT INTO config_home_widgets (id, insight_visible, patrimonio_visible, ask_visible)
VALUES (1, 1, 1, 1);

-- ============================================================================
-- FIN DE MIGRACION v1.8
-- Tablas modificadas: obligaciones (+ columna saldo_pendiente)
-- Tablas nuevas: saldo_obligacion_historico, config_home_widgets
-- ============================================================================
