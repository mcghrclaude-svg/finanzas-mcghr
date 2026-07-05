# CITA-011 -- Inconsistencia interna entre archivos del mismo entregable

**Frecuencia:** 1 vez (instalar-todo.ps1 requeria instalar-hook.ps1 que no era necesario)
**Nivel:** 1-AUTOMATIZADO

**Error:**
El agente genera un conjunto de archivos donde uno referencia a otro
que no existe o no es necesario. El usuario descubre la inconsistencia
al correr el instalador, no antes.

**Prevencion automatizada:**
Todo script instalador debe listar los archivos que requiere y verificar
que son exactamente los archivos que se entregan en el mismo conjunto.
Antes de presentar cualquier conjunto de archivos, verificar que:
  - Cada archivo referenciado en un script existe en el entregable
  - Cada archivo del entregable es referenciado o tiene un proposito explicito
  - No hay archivos requeridos que el instalador ya reemplaza

**Senal de alarma para Hernan:**
Si el instalador falla con FAIL Faltan estos archivos y los archivos
que faltan son scripts que el agente genero en sesiones anteriores
o que el propio instalador deberia reemplazar, este error esta ocurriendo.
