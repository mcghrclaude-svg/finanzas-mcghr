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

## PEN-003 -- ETL necesita modo de ejecucion con rango de fechas explicito

**Detectado:** 2026-06-29, sesion chat-etl-desarrollo
**Prioridad:** media (bloquea testing reproducible y carga inicial en produccion)

El ETL hoy solo soporta modo incremental: usa MAX(fecha_inicio) de
log_ejecuciones como marca de agua, y correos_procesados/documentos como
segunda linea de defensa contra duplicados. Falta un modo con rango de
fechas explicito (fecha_desde, fecha_hasta) para tres escenarios:

1. Testing en desarrollo: pruebas acotadas y reproducibles sobre un periodo
   conocido, sin esperar data nueva ni reprocesar todo el historico.
2. Carga inicial en produccion: la primera vez que el ETL corre, no hay
   corridas previas en log_ejecuciones. El rango permite procesar el
   historico de correos desde una fecha definida.
3. Reproceso post-restore: si se restaura la DB desde un backup, los
   eventos posteriores al backup deben reprocesarse. El rango permite
   delimitar exactamente que periodo re-ingestar.

En modo rango, la dedup por message_id/nombre_archivo sigue activa como
proteccion. Si un correo ya esta en correos_procesados (porque el restore
incluia esa entrada), no se duplica. Si no esta (porque el evento es
posterior al backup), se procesa normalmente.

Implicancias a resolver cuando se aborde:
- Requiere parametro explicito en el prompt de Cowork: modo (incremental
  o rango) + fecha_desde + fecha_hasta opcionales.
- El modo incremental sigue siendo el default para corridas automaticas.
- En el escenario post-restore, hay que decidir si limpiar o no
  correos_procesados para el rango afectado antes de reprocesar.

---

## PEN-004 -- ETL propone entidades nuevas del catalogo; UX y backend deben soportarlo

**Detectado:** 2026-06-29, sesion chat-etl-desarrollo
**Prioridad:** alta (sin esto el ETL deja FKs nulas silenciosamente cuando
encuentra contrapartes, categorias, cuentas o personas desconocidas)

Cuando el ETL detecta una entidad del catalogo que no existe (una contraparte
nueva, un medio de pago nuevo, una categoria que no matchea ninguna existente,
una persona no registrada), debe proponerla en lugar de dejar la FK nula o
inventar un ID inexistente. El humano confirma o descarta desde la app web.

Aplica a todas las entidades del catalogo: contrapartes, categorias,
cuentas/medios de pago, personas.

Implicancias a resolver en tres capas:

**Schema / ETL:**
Definir como se persiste una entidad "en potencial". Opciones:
- Agregar campo estado ('activo'|'potencial'|'rechazado') a cada tabla de
  catalogo; el ETL inserta con estado='potencial'.
- O una tabla separada propuestas_catalogo con tipo + datos + estado.
La transaccion queda con la FK apuntando a la entidad potencial, o con
la FK nula y el nombre propuesto en notas -- definir al implementar.

**Backend:**
Las queries que hoy asumen que la FK apunta a una entidad activa deben
manejar el estado 'potencial'. El endpoint GET /inbox no debe filtrar
transacciones con entidades potenciales -- al contrario, deben aparecer
con un flag visible que indique que hay una propuesta pendiente.

**UX:**
- El inbox debe indicar claramente cuando una transaccion tiene entidades
  propuestas sin confirmar.
- Flujo para confirmar (activar en catalogo) o descartar (FK nula) cada
  propuesta, independiente o en el mismo paso que la transaccion.
- Evaluar si hace falta una seccion "catalogo en revision" separada del
  inbox, para gestionar propuestas acumuladas de multiples transacciones.

---

## PEN-005 -- Pantalla de administracion del entorno de dev en la UX

**Detectado:** 2026-06-30, sesion chat-etl-desarrollo
**Prioridad:** media (no bloquea el ETL, pero es necesaria para testing
sistematico en dev; se usa en conjunto con PEN-003 modo rango)

Una pantalla accesible solo en entorno de desarrollo (no visible en prod)
que permita gestionar la DB de dev para testing del ETL. Operaciones
requeridas, cada una con sus parametros configurables desde la UI:

1. **Reset parcial:** vaciar transacciones, correos_procesados,
   archivos_mobile_procesados, vinculos, documentos, log_ejecuciones
   -- sin tocar el catalogo (categorias, contrapartes, cuentas, personas)

2. **Reset total:** vaciar todas las tablas incluyendo el catalogo
   -- con confirmacion explicita, es destructivo

3. **Backup:** generar un snapshot de la DB dev con nombre y fecha
   -- guardar en una carpeta configurable

4. **Restore:** seleccionar un snapshot previo y restaurarlo
   -- con confirmacion explicita antes de pisar la DB actual

5. **Inspeccion de corridas:** ver log_ejecuciones con filtro por fecha,
   ver correos_procesados y archivos_mobile_procesados de una corrida
   especifica, ver transacciones creadas en esa corrida

6. **Seed controlado:** cargar un conjunto de transacciones de prueba
   conocidas para validar correlacion y clasificacion

Consideraciones:
- Solo visible cuando VITE_ENV=development o equivalente
- Cada operacion destructiva requiere confirmacion explicita en la UI
- El backend necesita endpoints dedicados para estas operaciones
  (no exponer en produccion)
- Relacionado con PEN-003 (modo rango del ETL) -- las dos features
  se usan juntas para testing

---

## PEN-006 -- ABM de reglas de clasificacion y periodos financieros desde la UI

**Detectado:** 2026-07-02, sesion chat-ux-etl-prep
**Prioridad:** media (las tablas existen y el ETL las usa, pero no hay UI
para gestionarlas; hoy solo se pueden editar con SQL directo)

**Reglas de clasificacion:**
Las reglas en reglas_clasificacion pueden volverse obsoletas o conflictivas
con el tiempo (ej: una regla antigua que matchea patrones que hoy se manejan
de otra forma). Se necesita:
- Vista de lista con filtro por estado (activa/inactiva) y por tipo de match
- Edicion y desactivacion (soft delete, no borrado fisico)
- Eliminacion con advertencia sobre transacciones ya clasificadas por esa regla
- Definir comportamiento: eliminar una regla no reclasifica transacciones
  existentes -- queda como decision de diseno al implementar

**Periodos financieros:**
La tabla periodos_financieros existe y tiene schema completo (anio, mes,
fecha_inicio, fecha_fin_tentativa, fecha_fin_real, estado, dia_acreditacion_salario)
pero esta vacia y no hay UI ni endpoints para gestionarla. Se necesita ABM
completo: crear periodo, editar, marcar como cerrado (fecha_fin_real).
El cierre de un periodo tiene implicancias en el dashboard y en analitica
que deben definirse al implementar.

**Ubicacion sugerida:** Settings > Catalogs como tabs adicionales,
o seccion nueva "Settings > Rules & Periods" si el scope lo justifica.

---

## PEN-007 -- Guard de entorno para Tools: mover include_router a bloque condicional

**Detectado:** 2026-07-02, sesion chat-ux-etl-prep
**Prioridad:** baja (el guard funcional con 403 es suficiente por ahora;
se vuelve critico cuando se implemente el pin de seguridad o se despliegue
en un entorno compartido)

Hoy tools.py se registra en main.py incondicionalmente. El guard _guard_dev()
dentro de cada endpoint devuelve 403 si settings.env != 'dev', lo que es
funcionalmente correcto. Sin embargo, el router igual existe en la app en
produccion: sus rutas son descubribles via /docs y el codigo de cada
endpoint esta cargado en memoria.

**Resolucion pendiente:**
Cuando se implemente el pin de seguridad o se prepare un deploy a produccion,
mover el include_router de tools a un bloque condicional en main.py:

    if settings.env == "dev":
        app.include_router(tools.router, ...)

Esto garantiza que en prod el router directamente no existe, sus rutas
no aparecen en /docs y el codigo no se ejecuta bajo ninguna condicion.
