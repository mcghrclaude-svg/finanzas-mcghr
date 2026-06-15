-- Migración 002: tablas requeridas por el dashboard de presupuesto
-- Ejecutar sobre finanzas.db después de 001_initial.sql
-- Fecha: 2026-06-15
-- Autor: Claude (sesión dashboard Jun-2026)

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────────────────────
-- 1. periodos_financieros
--    Período financiero familiar: salario ~25 mes anterior → ~24 mes corriente.
--    fecha_fin_tentativa se muestra en itálica en el dashboard.
--    fecha_fin_real se escribe cuando el ETL detecta el ingreso SALARIO del período siguiente.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS periodos_financieros (
    id                      TEXT PRIMARY KEY,     -- '2026-06'
    anio                    INTEGER NOT NULL,     -- 2026
    mes                     INTEGER NOT NULL,     -- 6
    fecha_inicio            DATE    NOT NULL,     -- 2026-05-25
    fecha_fin_tentativa     DATE    NOT NULL,     -- 2026-06-24  (mostrar en itálica)
    fecha_fin_real          DATE,                -- NULL hasta confirmar salario
    estado                  TEXT    NOT NULL DEFAULT 'abierto',  -- abierto | cerrado
    dia_acreditacion_salario INTEGER,            -- 25 (varía 23–27)
    notas                   TEXT,
    CONSTRAINT ck_estado CHECK (estado IN ('abierto', 'cerrado')),
    CONSTRAINT ck_mes    CHECK (mes BETWEEN 1 AND 12)
);

-- ─────────────────────────────────────────────────────────────
-- 2. Agregar tipo_patron_gasto a categorias (si no existe)
-- ─────────────────────────────────────────────────────────────
ALTER TABLE categorias
    ADD COLUMN tipo_patron_gasto TEXT NOT NULL DEFAULT 'variable_frecuente'
    CHECK (tipo_patron_gasto IN (
        'fijo_unico',         -- arriendo, cuota préstamo: 1 pago/período, badge de vencimiento
        'fijo_recurrente',    -- Netflix, Spotify, Claro: cobro automático en fecha conocida
        'variable_frecuente', -- mercado, Rappi, transporte: muchos gastos distribuidos
        'variable_esporadico' -- salud, viajes, ropa: pocos gastos irregulares
    ));

-- ─────────────────────────────────────────────────────────────
-- 3. Agregar id_periodo a presupuestos (si no existe)
-- ─────────────────────────────────────────────────────────────
ALTER TABLE presupuestos
    ADD COLUMN id_periodo TEXT REFERENCES periodos_financieros(id);

-- ─────────────────────────────────────────────────────────────
-- 4. velocidad_historica
--    Velocidad de gasto diaria por categoría y período.
--    Se calcula al cierre de cada período (cuando fecha_fin_real es seteada).
--    Base para el cálculo de riesgo y proyección del dashboard.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS velocidad_historica (
    id                TEXT PRIMARY KEY,
    id_categoria      TEXT NOT NULL REFERENCES categorias(id),
    id_periodo        TEXT NOT NULL REFERENCES periodos_financieros(id),
    monto_total       NUMERIC(18,4) NOT NULL,  -- gasto total del período
    dias_periodo      INTEGER NOT NULL,         -- duración real del período
    velocidad_diaria  NUMERIC(18,4) NOT NULL,  -- monto_total / dias_periodo
    dias_con_gasto    INTEGER DEFAULT 0,        -- días activos (útil para esporádicos)
    calculado_en      DATE,
    UNIQUE (id_categoria, id_periodo)
);

CREATE INDEX IF NOT EXISTS idx_vel_hist_cat_periodo
    ON velocidad_historica (id_categoria, id_periodo);

CREATE INDEX IF NOT EXISTS idx_transacciones_periodo
    ON transacciones (id_categoria, fecha);

-- ─────────────────────────────────────────────────────────────
-- 5. Seed inicial de períodos (3 meses para tener histórico desde arranque)
--    Los montos de velocidad_historica se poblarán con datos reales
--    una vez cargadas las transacciones históricas.
-- ─────────────────────────────────────────────────────────────
INSERT OR IGNORE INTO periodos_financieros
    (id, anio, mes, fecha_inicio, fecha_fin_tentativa, fecha_fin_real, estado, dia_acreditacion_salario)
VALUES
    ('2026-04', 2026, 4, '2026-03-25', '2026-04-24', '2026-04-26', 'cerrado', 26),
    ('2026-05', 2026, 5, '2026-04-26', '2026-05-24', '2026-05-25', 'cerrado', 25),
    ('2026-06', 2026, 6, '2026-05-25', '2026-06-24', NULL,          'abierto', NULL);
