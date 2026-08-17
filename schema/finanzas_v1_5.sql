-- ============================================================================
-- finanzas_v1_5.sql
-- Migracion de schema -- Plataforma Finanzas MCGHR
-- ============================================================================
-- Version:  1.5
-- Fecha:    Agosto 2026
-- Anterior: finanzas_v1_4b.sql
--
-- CAMBIOS EN ESTA VERSION:
--   1. NUEVA TABLA: monedas
--      Catalogo real de moneda (antes era un string suelto en cuentas.moneda
--      y tramos.moneda_origen/destino, sin catalogo).
--
--   2. NUEVA TABLA: archivos_mobile_procesados
--      Ya estaba diseñada en finanzas_v1_4b.sql pero esa migracion nunca se
--      aplico sobre data/dev/finanzas_dev.db (verificado con .tables el
--      2026-08-09). Se incluye aqui para no depender de una migracion
--      historica que quedo sin ejecutar.
--
--   3. NUEVA TABLA: log_ejecuciones_mobile
--      Historial de corridas del script de importacion de gastos PWA
--      (scripts/import_pwa_gastos.py). Separada de log_ejecuciones porque
--      esa tabla es especifica del ETL de correos (columnas correos_leidos,
--      transacciones_enriquecidas, etc. no aplican aqui).
--
--   4. NUEVA TABLA: config_pwa_import
--      Fila unica (id=1) con la configuracion editable desde la pantalla
--      de escritorio: intervalo, carpetas de gastos, carpeta de catalogos,
--      carpeta de resumen mensual. El toggle encendido/apagado NO se guarda
--      aqui -- la fuente de verdad es la Tarea Programada de Windows.
--
-- COMO EJECUTAR (INCREMENTAL):
--   sqlite3 data\dev\finanzas_dev.db < schema\finanzas_v1_5.sql
-- ============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS monedas (
    codigo      VARCHAR(3)  NOT NULL PRIMARY KEY,
    -- Codigo ISO 4217 en mayusculas (ej. "COP", "USD"). Es el id del catalogo,
    -- igual que en categorias/cuentas/contrapartes el id es un slug legible.

    simbolo     VARCHAR(5),
    -- Simbolo para mostrar en UI (ej. "$", "US$").

    nombre      VARCHAR     NOT NULL,
    -- Nombre descriptivo (ej. "Peso colombiano").

    activa      BOOLEAN
    -- Soft delete, igual que el resto de los catalogos.
);


CREATE TABLE IF NOT EXISTS archivos_mobile_procesados (
    nombre_archivo      TEXT    PRIMARY KEY,
    -- Nombre del archivo JSON (ej: "gasto_<uuid>.json"). Ancla deterministica:
    -- unico por archivo. Analogo a id_correo en correos_procesados.

    dispositivo         TEXT    NOT NULL,
    -- "iphone_ghr" o "iphone_mc", derivado del campo "quien" del JSON.

    fecha_archivo       TEXT    NOT NULL,
    -- fecha_creacion del JSON (campo del archivo, no del procesamiento).

    tipo                TEXT,
    -- Tipo de JSON: "foto_factura" u otros que defina la PWA en el futuro.

    fecha_procesado     TEXT    NOT NULL,
    -- ISO 8601. Cuando lo proceso el script en esta corrida.

    resultado           TEXT    NOT NULL DEFAULT 'ok',
    -- ok        -> se creo una transaccion
    -- sin_datos -> el JSON no tenia datos financieros utiles
    -- error     -> fallo al procesar (JSON invalido o insercion fallida)
    -- duplicado -> el id del JSON ya existia como transaccion

    id_transaccion_creada TEXT
    -- ID de la transaccion creada, si aplica. NULL si resultado != 'ok'.
);

CREATE INDEX IF NOT EXISTS idx_amp_dispositivo_fecha
    ON archivos_mobile_procesados(dispositivo, fecha_archivo);


CREATE TABLE IF NOT EXISTS log_ejecuciones_mobile (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,

    fecha_inicio            TEXT    NOT NULL,
    -- ISO 8601 con offset. Cuando arranco la corrida (manual o via Tarea Programada).

    fecha_fin               TEXT,
    -- ISO 8601 con offset. NULL hasta que el script termina. Si queda NULL,
    -- la corrida termino de forma anormal.

    archivos_leidos         INTEGER NOT NULL DEFAULT 0,
    -- Total de JSONs revisados en pendientes/ en esta corrida (todas las carpetas).

    transacciones_nuevas    INTEGER NOT NULL DEFAULT 0,
    -- Transacciones creadas exitosamente en esta corrida.

    duplicados              INTEGER NOT NULL DEFAULT 0,
    -- JSONs saltados porque ya estaban en archivos_mobile_procesados.

    errores                 INTEGER NOT NULL DEFAULT 0,
    -- JSONs invalidos o que fallaron al insertar (quedan en pendientes/).

    alertas                 TEXT    NOT NULL DEFAULT '{}',
    -- JSON con detalle de errores: {"errores": [{"archivo": "...", "motivo": "..."}]}

    notas                   TEXT
    -- Texto libre con el resumen narrativo de la corrida.
);


CREATE TABLE IF NOT EXISTS config_pwa_import (
    id                          INTEGER PRIMARY KEY CHECK (id = 1),
    -- Fila unica -- CHECK fuerza id=1, no hace falta mas de una fila de config.

    intervalo_minutos           INTEGER NOT NULL DEFAULT 60,

    carpetas_gastos             TEXT    NOT NULL DEFAULT '[]',
    -- JSON array de rutas locales de OneDrive (una o mas carpetas padre).

    carpeta_catalogos           TEXT,
    -- Carpeta donde se escribe catalogos.json.

    carpeta_resumen_mensual     TEXT,
    -- Carpeta donde se dejara (a futuro) el JSON de resumen mensual. Solo el
    -- campo de configuracion por ahora -- sin logica de generacion todavia.

    actualizado_en              TEXT
);

INSERT OR IGNORE INTO config_pwa_import (id, intervalo_minutos, carpetas_gastos)
VALUES (1, 60, '[]');

-- ============================================================================
-- FIN DE MIGRACION v1.5
-- Tablas nuevas: monedas, archivos_mobile_procesados, log_ejecuciones_mobile,
--                config_pwa_import
-- ============================================================================
