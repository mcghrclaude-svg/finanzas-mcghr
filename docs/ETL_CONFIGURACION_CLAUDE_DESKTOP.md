# Configuracion ETL -- Tarea Programada Claude Desktop
## Plataforma Financiera MCGHR

**Fecha:** Junio 2026
**Proposito:** Guia paso a paso para activar el ETL automatico diario.

---

## Prerequisitos

Antes de configurar la tarea, verificar que estos MCPs esten activos
en Claude Desktop (Settings -> Integrations):

| MCP | Para que se usa | Estado requerido |
|---|---|---|
| SQLite (finanzas.db) | Leer y escribir transacciones | Activo, apuntando a OneDrive |
| mcp_lector_correos | Leer Gmail hernan y malu | Activo con tokens OAuth |
| Filesystem | Leer PDFs y JSONs de OneDrive | Activo |

Si mcp_lector_correos no tiene tokens OAuth todavia:
- Ir a `C:\Users\ghriz\finanzas-mcghr\mcp_servers\mcp_lector_correos\`
- Seguir las instrucciones de `README.md` para hacer el flujo OAuth

---

## Crear la tarea programada

1. Abrir Claude Desktop
2. Ir a **Tareas programadas** (icono de reloj en el sidebar)
3. Click en **Nueva tarea** (boton arriba a la derecha)
4. Responder las preguntas de configuracion con:
   - **Que queres que haga:** "Procesar automaticamente los datos financieros
     de la familia: leer correos nuevos de hernan y malu, procesar PDFs en
     OneDrive, incorporar fotos de facturas del celular, clasificar todo con
     las reglas aprendidas, y escribir las transacciones en la base de datos."
   - **Cuando:** Todos los dias a las 4:00 AM
   - **Permisos:** Siempre permitido (sin confirmacion manual)

5. Cuando te muestre el borrador del prompt, **reemplazarlo** por el
   contenido completo del archivo `ETL_PROMPT_CLAUDE_DESKTOP.md`
   (esta en la carpeta `docs/` del repo).

6. Confirmar la creacion de la tarea.

---

## Verificar que funciona

Antes de dejar correr automaticamente, probar manualmente:

1. En la pantalla de Tareas programadas, click en **Ejecutar ahora**
2. Esperar que termine (puede tomar 2-5 minutos segun la cantidad de correos)
3. Verificar en la app web (http://localhost:8000) que aparecen transacciones
   nuevas en el inbox
4. Verificar en la DB:
   - En Claude Desktop, preguntarle: "Muestrame los ultimos 5 registros de
     log_ejecuciones en finanzas.db"
   - Debe aparecer una corrida con fecha de hoy y transacciones_nuevas > 0

---

## Monitoreo diario

La forma mas rapida de ver si el ETL corrio bien:

- Abrir la app web -> Dashboard -> el badge del inbox muestra cuantas
  transacciones nuevas hay para revisar
- O preguntarle a Claude Desktop: "Como fue la ultima corrida del ETL
  segun log_ejecuciones?"

---

## Pausar el ETL

Si hay que hacer mantenimiento o migraciones:

1. Ir a Tareas programadas
2. Desactivar el toggle de la tarea "ETL financiero"
3. Reactivarlo cuando termine el mantenimiento

---

## Carpetas de OneDrive que usa el ETL

| Carpeta | Que contiene |
|---|---|
| `Finanzas MCGHR\Extractos\` | PDFs bancarios a procesar |
| `Finanzas MCGHR\Inbox\` | JSONs de la PWA del celular |
| `Finanzas MCGHR\Stage\` | PDFs descargados de correos (temporal) |
| `Finanzas MCGHR\PWA\` | catalogos.json para la PWA |

---

*Documento generado Junio 2026 -- Plataforma Financiera MCGHR*
