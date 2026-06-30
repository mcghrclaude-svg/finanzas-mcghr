-- ============================================================================
-- finanzas_v1_3.sql
-- Migracion de schema -- Plataforma Finanzas MCGHR
-- ============================================================================
-- Version:  1.3
-- Fecha:    Junio 2026
-- Anterior: finanzas_v1_2.sql + finanzas_v1_2c.sql
--
-- CAMBIOS EN ESTA VERSION:
--   1. NUEVA TABLA: correos_procesados
--      Ancla deterministica del ETL para correos Gmail.
--      Registra el message_id de cada correo procesado para garantizar
--      idempotencia: si el ETL corre dos veces, no reprocesa el mismo correo.
--
--   2. NUEVA TABLA: log_ejecuciones
--      Registro de cada corrida del ETL con contadores y estado.
--      El ETL inserta una fila al inicio (Paso 0) y la actualiza al final (Paso 5).
--
-- COMO EJECUTAR:
--   Este script es INCREMENTAL -- no modifica tablas existentes.
--   Ejecutar UNA SOLA VEZ sobre una DB que ya tiene v1.2 aplicado.
--
--   DB de desarrollo:
--   sqlite3 data\dev\finanzas_dev.db < schema\finanzas_v1_3.sql
--
--   DB de produccion (OneDrive):
--   sqlite3 "C:\Users\ghriz\OneDrive\Finanzas MCGHR\Generales\finanzas.db" < schema\finanzas_v1_3.sql
-- ============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;


-- ============================================================================
-- NUEVA TABLA: correos_procesados
--
-- Proposito: ancla deterministica de la Capa 1 del mecanismo de correlacion.
-- El ETL consulta esta tabla (paso 1b) antes de procesar cualquier correo.
-- Si el message_id ya esta registrado, lo saltea sin ejecutar ninguna logica.
-- Al terminar de procesar un correo, lo registra aqui (paso 1h).
-- ============================================================================
CREATE TABLE IF NOT EXISTS correos_procesados (
    id_correo       TEXT    PRIMARY KEY,
    -- message_id unico asignado por Gmail. Es el ancla deterministica:
    -- no cambia si el ETL se reprocesa. Fuente: campo id del correo devuelto
    -- por mcp_lector_correos.

    cuenta_gmail    TEXT    NOT NULL,
    -- Cuenta que recibio el correo: "hernan" o "malu".
    -- Permite filtrar por titular en analisis de actividad del ETL.

    fecha_correo    TEXT    NOT NULL,
    -- Fecha del correo (DATE, no del procesamiento). Usado para debugging
    -- cuando hay que rastrear que correos de cierta fecha fueron procesados.

    asunto          TEXT,
    -- Asunto del correo. Solo para auditoria -- permite entender que proceso
    -- el ETL sin tener que releer el correo original en Gmail.

    remitente       TEXT,
    -- Direccion del remitente. Util para detectar patrones de remitentes
    -- que generan muchos errores o muchos "sin_datos".

    fecha_procesado TEXT    NOT NULL,
    -- ISO 8601 con offset. Cuando lo proceso el ETL en esta corrida.
    -- Permite saber el lag entre fecha_correo y fecha_procesado.

    resultado       TEXT    NOT NULL DEFAULT 'ok'
    -- Resultado del procesamiento:
    --   ok          -> se extrajo al menos un evento financiero
    --   sin_datos   -> el correo no contenia datos financieros utiles
    --   error       -> fallo al procesar (ver notas en log_ejecuciones)
    --   duplicado   -> el hecho economico ya existia en la DB (correlacion exitosa)
);

CREATE INDEX IF NOT EXISTS idx_cp_cuenta_fecha
    ON correos_procesados(cuenta_gmail, fecha_correo);
-- Indice para la query del ETL que busca el ultimo correo procesado por cuenta.


-- ============================================================================
-- NUEVA TABLA: log_ejecuciones
--
-- Proposito: registro de cada corrida automatica del ETL.
-- Flujo de escritura:
--   Paso 0 del prompt: INSERT con fecha_inicio y contadores en 0.
--   Paso 5 del prompt: UPDATE con fecha_fin y totales reales.
-- Si la corrida falla a mitad, la fila queda con fecha_fin NULL,
-- lo que permite detectar corridas incompletas.
-- ============================================================================
CREATE TABLE IF NOT EXISTS log_ejecuciones (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    -- ID autoincremental. El ETL guarda este id al inicio (paso 0) para
    -- hacer el UPDATE al final (paso 5) con WHERE id = [id_guardado].

    fecha_inicio            TEXT    NOT NULL,
    -- ISO 8601 con offset. Cuando arranco la tarea programada.

    fecha_fin               TEXT,
    -- ISO 8601 con offset. NULL hasta que el ETL completa el paso 5.
    -- Si es NULL, la corrida termino de forma anormal.

    correos_leidos          INTEGER NOT NULL DEFAULT 0,
    -- Total de correos procesados en esta corrida (ambas cuentas, hernan + malu).
    -- Incluye los "sin_datos" -- es un contador de correos revisados, no de
    -- transacciones generadas.

    transacciones_nuevas    INTEGER NOT NULL DEFAULT 0,
    -- Transacciones creadas desde cero en esta corrida (no enriquecimientos).

    transacciones_enriquecidas INTEGER NOT NULL DEFAULT 0,
    -- Transacciones existentes que recibieron datos adicionales (correlacion
    -- exitosa con evento nuevo). Separado de transacciones_nuevas para medir
    -- cuanto del trabajo del ETL es enriquecimiento vs creacion.

    documentos_nuevos       INTEGER NOT NULL DEFAULT 0,
    -- PDFs y fotos registrados en la tabla documentos en esta corrida.

    alertas                 TEXT    NOT NULL DEFAULT '{}',
    -- JSON con alertas generadas durante la corrida. Estructura minima:
    -- {"errores": [], "advertencias": []}
    -- Permite al humano ver que salio mal sin leer el campo notas completo.

    notas                   TEXT
    -- Texto libre con el resumen narrativo de la corrida. El ETL escribe
    -- en el paso 5: "ETL automatico completado. Correos: N. TX nuevas: N.
    -- TX enriquecidas: N. Errores: N."
    -- Si hay errores puntuales, se detallan aqui.
);

-- No se agrega indice adicional: la tabla es chica (una fila por dia)
-- y MAX(fecha_inicio) sobre toda la tabla es eficiente sin indice.


-- ============================================================================
-- FIN DE MIGRACION v1.3
-- Tablas nuevas: correos_procesados, log_ejecuciones
-- ============================================================================
