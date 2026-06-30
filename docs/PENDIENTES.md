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
