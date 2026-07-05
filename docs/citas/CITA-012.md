# CITA-012 -- Divergencia silenciosa entre .claude\skills y el repo

**Frecuencia:** 1 vez detectada (2026-06-29, mcp_lector_correos/server.py)
**Nivel:** 3-CONTEXTO

**Error:**
Claude Desktop usa los archivos en C:\Users\ghriz\.claude\skills\ directamente.
Cuando se itera sobre un skill en Claude Desktop (mejoras a docstrings, mensajes
de error, comentarios inline), los cambios quedan solo en .claude\skills\ y
nunca se propagan al repo. El repo queda atrasado sin que nadie lo note.

**Lo que paso esta vez:**
server.py del repo tenia 453 lineas (commit 450a758).
La copia en .claude\skills\ tenia 504 lineas con:
- Docstrings mas completos en las 3 herramientas (ejemplos, tipos, descripcion de campos)
- ~15 comentarios inline explicando pasos internos
- Mensajes de error mas informativos en descargar_adjunto (PermissionError, error_red)
La divergencia era de 51 lineas pero ninguna era regresion -- .claude\skills era
un superconjunto estricto del repo.

**Resolucion:**
1. Leer ambos archivos completos en el mismo turno
2. Comparar: identificar cual es la version mas avanzada y si hay cambios
   en ambas direcciones (en este caso solo habia avances en .claude\skills)
3. Copiar la version mas avanzada al repo (Write del archivo en mcp_servers/)
4. Commitear en branch tematico

**Prevencion:**
No hay automatizacion hoy. Estrategia manual:
- Al cerrar una sesion de Claude Desktop donde se modifico un skill,
  abrir Claude Code y propagar el cambio al repo en el mismo momento.
- Al iniciar un chat de Claude Code que toque mcp_servers/, comparar
  la copia del repo con la de .claude\skills\ antes de editar.
- Ruta de referencia siempre: C:\Users\ghriz\.claude\skills\<nombre>\server.py

**Senal de alarma para Hernan:**
Si el repo tiene menos lineas en un server.py que la copia en .claude\skills\,
hay divergencia. Verificar con:
  (Get-Content "C:\Users\ghriz\.claude\skills\mcp_lector_correos\server.py").Count
  (Get-Content "mcp_servers\mcp_lector_correos\server.py").Count
