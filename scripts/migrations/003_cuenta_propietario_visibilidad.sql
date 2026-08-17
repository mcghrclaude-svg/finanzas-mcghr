-- Migracion 003: propietario y visibilidad PWA en cuentas
-- Ejecutar sobre finanzas.db despues de 002_dashboard_schema.sql
-- Fecha: 2026-08-17
-- Autor: Claude (sesion Catalogo de Cuentas -- propietario/visibilidad/moneda opcional)

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────────────────────
-- 1. propietario: quien es dueno de la cuenta -- GHR, MC o Ambos.
--    Default 'Ambos' para no romper cuentas existentes.
-- ─────────────────────────────────────────────────────────────
ALTER TABLE cuentas ADD COLUMN propietario TEXT NOT NULL DEFAULT 'Ambos'
    CHECK (propietario IN ('GHR', 'MC', 'Ambos'));

-- ─────────────────────────────────────────────────────────────
-- 2. visible_pwa: si la cuenta aparece en el dropdown de medio de pago
--    de la PWA. Default true para no hacer desaparecer nada existente.
--    Cuentas como una de inversion (ej. IBKR) se marcan false a mano.
-- ─────────────────────────────────────────────────────────────
ALTER TABLE cuentas ADD COLUMN visible_pwa BOOLEAN NOT NULL DEFAULT 1;

-- Nota: cuentas.moneda ya era nullable a nivel de columna (verificado con
-- PRAGMA table_info antes de esta migracion) -- el default 'COP' era solo
-- del lado del ORM y se saca en el modelo, sin necesidad de ALTER aca.
