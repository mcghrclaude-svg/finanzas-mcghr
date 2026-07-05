# CITA-004 -- Asumir contenido de archivos sin leerlos en el turno actual

**Frecuencia:** 3+ veces (causa de los errores mas costosos del proyecto)
**Nivel:** 3-CONTEXTO

**Error:**
El agente genera codigo que modifica un archivo sin haber hecho web_fetch
de ese archivo en el turno actual. Usa el contenido de la memoria de la
conversacion, que puede estar desactualizado por commits de otros chats.
Resultado: modelos con columnas que no existen, imports incorrectos,
convenciones distintas a las del repo real.

**Prevencion:**
Regla en Custom Instructions del proyecto:
"Antes de modificar cualquier archivo, mostrar el output de web_fetch
de ese archivo. Si no hay output de lectura en este turno, no escribir codigo."

**Senal de alarma para Hernan:**
Si el agente te entrega codigo sin haber mostrado antes el contenido
leido de algun archivo del repo en ese mismo mensaje, frenar y preguntar:
"leiste el archivo real primero?".
