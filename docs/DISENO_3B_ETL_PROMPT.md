# ETL Prompt y Schema v1.2 -- Diseno Funcional (Entrega 3B)
## Plataforma Financiera MCGHR

**Fecha:** Junio 2026
**Estado:** Aprobado -- pendiente implementacion
**Entrega:** 3B -- segunda de tres entregas del Punto 3
**Depende de:** Entrega 3A completada y validada

---

## Que incluye esta entrega

1. Migracion SQL `schema/finanzas_v1_2.sql` -- nuevos campos para correlacion
2. Actualizacion del modelo SQLAlchemy `backend/models/transaccion.py`
3. Prompt de la tarea programada de Claude Desktop (el "ETL real")
4. Documento de instrucciones para configurar la tarea en Claude Desktop

---

## Migracion schema v1.2

Agrega dos campos a la tabla `transacciones`:

```sql
-- finanzas_v1_2.sql
-- Migracion incremental sobre v1.1
-- Ejecutar UNA SOLA VEZ sobre una DB que ya tiene v1.1 aplicado

ALTER TABLE transacciones ADD COLUMN
    id_evento TEXT;
    -- Hash determinista para agrupar eventos del mismo hecho economico.
    -- Generado por el ETL. Formato: "EVT_" + 16 chars hex.
    -- Permite correlacionar: notificacion TC + factura adjunta + linea extracto.
    -- NULL para transacciones manuales o pre-v1.2.

ALTER TABLE transacciones ADD COLUMN
    estado_enriquecimiento TEXT DEFAULT 'inicial';
    -- inicial     -> primer evento registrado, puede llegar mas data
    -- enriquecido -> tiene datos adicionales (factura, items, descripcion)
    -- completo    -> extracto confirmo el evento, ciclo contable cerrado

CREATE INDEX IF NOT EXISTS idx_tx_id_evento
    ON transacciones(id_evento)
    WHERE id_evento IS NOT NULL;
```

---

## Modelo SQLAlchemy actualizado

`backend/models/transaccion.py` agrega los dos campos nuevos al modelo
`Transaccion` existente. Sin romper compatibilidad hacia atras.

---

## Prompt de la tarea programada

El prompt es el "codigo" del ETL en este enfoque. Se configura una sola vez
en Claude Desktop como tarea programada con schedule diario a las 4:00 AM.

### Estructura del prompt

El prompt tiene cinco secciones:

**Seccion 1 -- Identidad y contexto**
Le dice a Claude Desktop que rol tiene, que herramientas puede usar,
y que reglas debe respetar (no marcar correos como leidos, no borrar archivos,
escribir solo en la DB de produccion en OneDrive).

**Seccion 2 -- Paso a paso del procesamiento**
Instrucciones detalladas de cada paso: como leer correos, como identificar
si son financieros, como extraer datos, como correlacionar eventos, como
escribir en la DB.

**Seccion 3 -- Criterios de clasificacion**
Explica como usar el catalogo y las reglas existentes. Como calcular
confianza. Cuando crear transaccion confirmada vs pendiente.

**Seccion 4 -- Formato de escritura en DB**
Los INSERT exactos que debe ejecutar via MCP sqlite, con todos los campos
requeridos.

**Seccion 5 -- Resumen final**
Que escribir en log_ejecuciones al terminar.

### Borrador del prompt (a refinar en implementacion)

```
Sos el ETL financiero de la familia Rizzi (GHR y MC).
Tu trabajo es procesar automaticamente las fuentes de datos financieras
y convertirlas en transacciones estructuradas en la base de datos.

HERRAMIENTAS DISPONIBLES:
- mcp__sqlite: leer y escribir en finanzas.db
- mcp__mcp_lector_correos: buscar y leer correos Gmail
- mcp__filesystem: leer archivos de OneDrive

REGLAS CRITICAS:
- Nunca marques correos como leidos
- Nunca borres archivos de OneDrive
- Solo escribi en la DB de produccion:
  C:\Users\ghriz\OneDrive\Finanzas MCGHR\Generales\finanzas.db
- Si hay duda entre crear transaccion nueva o enriquecer una existente,
  busca por id_evento antes de insertar

PASO 1 -- CONTEXTO INICIAL
Ejecuta estas queries para entender el estado actual:

  SELECT MAX(fecha_procesado) FROM correos_procesados;
  -- Usas esta fecha como "desde" para buscar correos nuevos

  SELECT patron_remitente, patron_asunto, id_categoria, usos
  FROM reglas_clasificacion
  WHERE activa = 1
  ORDER BY creada_por DESC, usos DESC
  LIMIT 50;
  -- Estas son las reglas de clasificacion. Las del humano tienen prioridad.

  SELECT t.descripcion, t.id_categoria, cp.nombre as contraparte,
         t.fuente, t.confianza
  FROM transacciones t
  LEFT JOIN contrapartes cp ON t.id_contraparte = cp.id
  WHERE t.revisado_humano = 1
  ORDER BY t.fecha DESC
  LIMIT 50;
  -- Estos son ejemplos reales de como GHR/MC clasificaron transacciones antes.
  -- Usalos como referencia para clasificar los eventos nuevos.

PASO 2 -- CORREOS GMAIL
Busca correos financieros nuevos en ambas cuentas...
[continua en implementacion]
```

El prompt completo se termina de escribir en la entrega 3B, una vez que
3A esta validada y el schema v1.2 esta aplicado.

---

## Instrucciones de configuracion en Claude Desktop

Documento `docs/ETL_CONFIGURACION_CLAUDE_DESKTOP.md` que explica:

1. Como crear la tarea programada en Claude Desktop via /schedule
2. Que MCP tools deben estar activos (sqlite, mcp_lector_correos, filesystem)
3. Como verificar que la tarea corrio correctamente (log_ejecuciones)
4. Como probar manualmente antes de activar el schedule automatico
5. Como pausar el ETL si hay que hacer mantenimiento

---

## Tests requeridos

La entrega 3B no tiene tests automatizados en pytest porque el ETL es
un prompt de lenguaje natural ejecutado por Claude Desktop.

Lo que si se valida manualmente antes de activar el schedule:

1. Correr el prompt manualmente una vez con `--dry-run` implicito
   (pidiendole que describa lo que haria sin escribir)
2. Correr con datos reales y verificar en la app web que las transacciones
   aparecen en el inbox correctamente
3. Verificar log_ejecuciones que el registro quedo bien
4. Verificar que no se crearon duplicados

---

*Documento generado Junio 2026 -- Plataforma Financiera MCGHR*
*Leer junto con: docs/ETL_DISENO_FUNCIONAL.md, docs/DISENO_3A_INBOX_BACKEND.md*
