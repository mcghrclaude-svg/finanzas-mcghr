-- ============================================================================
-- finanzas_v1_6.sql
-- Migracion de schema -- Plataforma Finanzas MCGHR
-- ============================================================================
-- Version:  1.6
-- Fecha:    Agosto 2026
-- Anterior: finanzas_v1_5.sql
--
-- CAMBIOS EN ESTA VERSION:
--   1. config_pwa_import: raiz unica en vez de 3 carpetas separadas
--      Antes: carpetas_gastos (JSON array), carpeta_catalogos (unico),
--      carpeta_resumen_mensual (unico) -- 3 campos independientes, faciles
--      de desalinear entre si (bug real: catalogos.json se escribia en un
--      solo lugar aunque carpetas_gastos ya soportaba mas de una persona,
--      asi que un celular podia no recibir nunca catalogos actualizados).
--      Ahora: raices (JSON array). Cada raiz es UNA carpeta de OneDrive;
--      pendientes/, procesados/, Catalogos/ y Resumen/ se derivan de ella
--      en tiempo de ejecucion, no se guardan como campos separados. El
--      export de catalogos.json escribe una copia en cada raiz de la lista.
--      Ver ADR-018 para el detalle de la decision.
--
--      Si la tabla vieja existe (dev, con datos de prueba), se migra la
--      fila: raices = carpetas_gastos tal cual, porque en la unica fila
--      real que existe hoy carpeta_catalogos/carpeta_resumen_mensual ya
--      eran subcarpetas de esa misma raiz (no habia desalineamiento que
--      preservar). En produccion la tabla config_pwa_import no existe
--      todavia (la migracion v1.5 nunca se aplico ahi) -- este script la
--      crea directo con el schema nuevo, sin fila que migrar.
--
-- COMO EJECUTAR (INCREMENTAL):
--   sqlite3 data\dev\finanzas_dev.db < schema\finanzas_v1_6.sql
-- ============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- Bootstrap: garantiza que config_pwa_import exista con el shape v1.5 antes
-- de migrarla. En dev no hace nada (la tabla ya existe con datos). En prod
-- (donde v1.5 nunca se aplico) la crea vacia -- mismo patron que uso v1.5
-- para archivos_mobile_procesados, que tampoco se habia aplicado desde
-- v1.4b. Sin este paso, el INSERT...SELECT de abajo fallaria en prod
-- (no se puede referenciar una tabla que no existe, ni siquiera bajo WHERE).
CREATE TABLE IF NOT EXISTS config_pwa_import (
    id                          INTEGER PRIMARY KEY CHECK (id = 1),
    intervalo_minutos           INTEGER NOT NULL DEFAULT 60,
    carpetas_gastos             TEXT    NOT NULL DEFAULT '[]',
    carpeta_catalogos           TEXT,
    carpeta_resumen_mensual     TEXT,
    actualizado_en              TEXT
);

CREATE TABLE config_pwa_import_new (
    id                          INTEGER PRIMARY KEY CHECK (id = 1),
    -- Fila unica -- CHECK fuerza id=1, no hace falta mas de una fila de config.

    intervalo_minutos           INTEGER NOT NULL DEFAULT 60,

    raices                      TEXT    NOT NULL DEFAULT '[]',
    -- JSON array de rutas locales de OneDrive (una por persona: la propia,
    -- la de Martha como carpeta compartida, etc.). Cada raiz trae consigo
    -- pendientes/, procesados/, Catalogos/catalogos.json y Resumen/,
    -- creadas automaticamente si no existen -- no son campos separados.

    actualizado_en              TEXT
);

-- Migra la fila vieja si tenia datos (dev). En prod la tabla bootstrapeada
-- arriba esta vacia, asi que este SELECT no devuelve filas -- sin error.
INSERT INTO config_pwa_import_new (id, intervalo_minutos, raices, actualizado_en)
SELECT id, intervalo_minutos, carpetas_gastos, actualizado_en
FROM config_pwa_import
WHERE id = 1;

DROP TABLE config_pwa_import;
ALTER TABLE config_pwa_import_new RENAME TO config_pwa_import;

INSERT OR IGNORE INTO config_pwa_import (id, intervalo_minutos, raices)
VALUES (1, 60, '[]');

-- ============================================================================
-- FIN DE MIGRACION v1.6
-- Tablas modificadas: config_pwa_import (carpetas_gastos + carpeta_catalogos +
--                      carpeta_resumen_mensual -> raices)
-- ============================================================================
