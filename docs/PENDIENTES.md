# PENDIENTES -- Deuda tecnica y tareas diferidas
# Finanzas MCGHR
#
# Este archivo NO es regenerado por cerrar-sesion.ps1.
# Actualizar manualmente al detectar o resolver cada item.

---

## PEN-001 -- Renombrar tamano_bytes (con enie) a tamano_bytes (ASCII)

**Detectado:** 2026-06-29, sesion chat-sync-mcp-lector-correos
**Causa:** CITA-009 -- atributo del dataclass Adjunto usa caracter no-ASCII
**Prioridad:** baja (no afecta runtime, solo dispara warning del hook)

**Archivos afectados (3):**
1. `skills/lector_correos/lector_correos.py` linea 86 -- definicion del dataclass (raiz)
2. `mcp_servers/mcp_lector_correos/server.py` lineas 432, 546, 552 -- consumidor
3. `src/finanzas_familia.py` linea 392 -- consumidor

**Como resolver:**
1. Renombrar el atributo en la definicion del dataclass (lector_correos.py:86)
2. Propagar el renombre a los dos archivos consumidores
3. Verificar que no haya otras referencias con grep antes de commitear
4. Propagar el cambio tambien a C:\Users\ghriz\.claude\skills\lector_correos\lector_correos.py
   (copia en uso por Claude Desktop)

---

## PEN-002 -- UX para correccion manual de correlaciones ETL

**Detectado:** 2026-06-29, sesion chat-etl-desarrollo
**Prioridad:** media (no bloquea el ETL, mejora la calidad del aprendizaje a largo plazo)

Pantalla en la app web que permita al humano agrupar eventos que el ETL no
correlaciono (ej: un correo de Bancolombia y una foto de factura que son el
mismo gasto) y separar eventos que el ETL correlaciono mal. Cuando el humano
hace una correccion, el sistema registra el patron que la disparo para
alimentar el motor de correlacion en corridas futuras -- analogo a como
las correcciones de categoria alimentan reglas_clasificacion. Disenar junto
con la pantalla de Inbox; probablemente vive como accion secundaria sobre
cada transaccion en la cola de revision.

---

## PEN-003 -- ETL necesita modo de ejecucion con rango de fechas para dev/testing

**Detectado:** 2026-06-29, sesion chat-etl-desarrollo
**Prioridad:** media (bloquea testing reproducible del ETL en desarrollo)

El ETL hoy solo soporta modo incremental: procesa desde la ultima corrida
usando correos_procesados y documentos como marca de agua. Falta un modo
alternativo, solo para entornos de desarrollo, donde se pueda invocar con
un rango de fechas explicito (ej: "procesa correos entre el 1 y el 7 de
junio") para hacer pruebas acotadas y reproducibles sin esperar data nueva
ni reprocesar todo el historico.

Implicancias a resolver cuando se aborde:
- El modo por rango de fechas NUNCA debe correr contra la DB de produccion.
  Si no respeta la logica de dedup, puede reprocesar eventos ya registrados
  y crear duplicados en finanzas.db.
- Requiere un parametro o flag explicito en el prompt de Cowork (ademas
  del modo incremental por defecto), para que la distincion sea intencional
  y no accidental.
- Posiblemente necesita una DB de dev limpia con datos de seed representativos
  en lugar de depender de correos reales de Gmail.
