-- schema_finanzas_v1_2c.sql
-- Agrega columnas que estaban en el modelo SQLAlchemy pero no en la DB real.
--
-- Ejecutar:
--   cd C:\Users\ghriz\finanzas-mcghr
--   Get-Content "schema\finanzas_v1_2c.sql" | sqlite3 "C:\Users\ghriz\OneDrive\Finanzas MCGHR\Generales\finanzas.db"

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- Canal de origen de la transaccion
-- email | pdf | mobile | manual
ALTER TABLE transacciones ADD COLUMN origen TEXT DEFAULT NULL;

-- Persona titular de la transaccion (GHR | MC)
-- Distinto de quien_pago — quien_pago es FK a personas, id_persona tambien
ALTER TABLE transacciones ADD COLUMN id_persona TEXT DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_tx_origen
    ON transacciones(origen)
    WHERE origen IS NOT NULL;
