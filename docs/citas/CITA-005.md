# CITA-005 -- Asumir schema de DB sin verificar la tabla real

**Frecuencia:** 5 veces (genero 4 iteraciones de fix_modelo)
**Nivel:** 3-CONTEXTO

**Error:**
El agente modifica un modelo SQLAlchemy asumiendo que sabe que columnas
tiene la tabla real. La DB real puede tener columnas distintas a las del
modelo (resultado de migraciones parciales, seeds, o decisiones de otros chats).
Resultado: errores de tipo "table has no column named X" o
"categorias.find is not a function" en runtime.

**Prevencion:**
Antes de tocar cualquier modelo, el agente debe pedirte que corras:
  echo "PRAGMA table_info(nombre_tabla);" | sqlite3 "ruta\a\finanzas_dev.db"
Y comparar columna por columna contra el modelo antes de escribir codigo.

**Senal de alarma para Hernan:**
Si aparece un error de columna inexistente en tests o en runtime,
y el agente propone un fix sin haber pedido el PRAGMA table_info primero,
este error esta ocurriendo.
