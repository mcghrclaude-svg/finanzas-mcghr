# Instrucciones post-instalacion
## Plataforma Financiera MCGHR — Junio 2026

Este documento explica los pasos manuales que quedan pendientes
despues de instalar las entregas 3A, 3B y 3C.

---

## Paso 1 — Seed de inbox (datos dummy para ver el Inbox en pantalla)

El seed crea 8 transacciones pendientes con distintos niveles de confianza
para que puedas ver el modulo Inbox funcionando sin esperar al ETL real.

```powershell
cd C:\Users\ghriz\finanzas-mcghr
venv\Scripts\activate
python -m scripts.seed.seed_inbox
```

Despues de correrlo, abri la app en http://localhost:3000/inbox
y vas a ver las transacciones organizadas en tres secciones.

**Nota:** el seed es idempotente — si lo corres dos veces no duplica datos.

---

## Paso 2 — Tokens OAuth Gmail (necesario para el ETL real)

Este paso habilita al ETL para leer los correos de hernan y malu.
Es un proceso de autorizacion que se hace una sola vez.

### 2a. Verificar que el MCP lector correos tiene su venv

```powershell
cd C:\Users\ghriz\finanzas-mcghr\mcp_servers\mcp_lector_correos

# Si no existe el venv:
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2b. Conseguir las credenciales OAuth de Google

1. Ir a https://console.cloud.google.com/
2. Crear un proyecto nuevo (o usar uno existente)
3. Habilitar la Gmail API:
   - APIs y servicios -> Biblioteca -> buscar "Gmail API" -> Habilitar
4. Crear credenciales OAuth:
   - APIs y servicios -> Credenciales -> Crear credenciales -> ID de cliente OAuth 2.0
   - Tipo: Aplicacion de escritorio
   - Descargar el JSON de credenciales
5. Guardar el archivo como:
   `C:\Users\ghriz\.claude\gmail_credentials.json`

### 2c. Hacer el flujo de autorizacion para hernan

```powershell
cd C:\Users\ghriz\finanzas-mcghr\mcp_servers\mcp_lector_correos
venv\Scripts\activate
python auth_gmail.py --cuenta hernan --credentials "C:\Users\ghriz\.claude\gmail_credentials.json"
```

Se va a abrir el browser con la pantalla de autorizacion de Google.
Iniciar sesion con ghrizzi.goog@gmail.com y dar permisos.
El token queda guardado automaticamente.

### 2d. Hacer el flujo de autorizacion para malu

```powershell
python auth_gmail.py --cuenta malu --credentials "C:\Users\ghriz\.claude\gmail_credentials.json"
```

Iniciar sesion con malu82@gmail.com y dar permisos.

### 2e. Verificar que funciona

En Claude Desktop, escribir:
"Busca correos de los ultimos 3 dias en la cuenta de hernan"

Si el MCP responde con correos, los tokens estan bien configurados.

---

## Paso 3 — Configurar la tarea programada del ETL en Claude Desktop

### 3a. Abrir el prompt del ETL

El prompt esta en el repo en:
`C:\Users\ghriz\finanzas-mcghr\docs\ETL_PROMPT_CLAUDE_DESKTOP.md`

Abrir ese archivo con el Bloc de notas o VS Code y copiar TODO el contenido.

### 3b. Crear la tarea en Claude Desktop

1. Abrir Claude Desktop
2. Click en el icono de reloj (Tareas programadas) en el sidebar izquierdo
3. Click en "Nueva tarea" (boton arriba a la derecha)
4. Cuando te pregunte que queres que haga, responder:
   "Quiero configurar una tarea personalizada con un prompt especifico"
5. Pegar el contenido completo del archivo ETL_PROMPT_CLAUDE_DESKTOP.md
6. Cuando pregunte el horario: "Todos los dias a las 4:00 AM"
7. Cuando pregunte permisos: "Siempre permitido"
8. Confirmar la creacion

### 3c. Verificar los MCPs activos

Antes de hacer la primera prueba, verificar en Claude Desktop
(Settings -> Integrations) que estos MCPs esten activos:

- SQLite apuntando a:
  `C:\Users\ghriz\OneDrive\Finanzas MCGHR\Generales\finanzas.db`
- mcp_lector_correos (con tokens OAuth del Paso 2)
- Filesystem

### 3d. Prueba manual antes del primer ciclo automatico

En la pantalla de Tareas programadas, click en "Ejecutar ahora" en la
tarea del ETL. Esperar 3-5 minutos. Verificar:

1. En la app web (http://localhost:3000/inbox) que aparecen transacciones nuevas
2. Preguntarle a Claude Desktop:
   "Mostrame el ultimo registro de log_ejecuciones en finanzas.db"
   Debe mostrar una corrida de hoy con transacciones_nuevas > 0

---

## Paso 4 — Agregar el script de arranque a la barra de tareas

El script `iniciar_finanzas.ps1` arranca el backend y el frontend
con un doble click. Para anclarlo a la barra de tareas de Windows:

### Crear un acceso directo

1. Click derecho en el escritorio -> Nuevo -> Acceso directo
2. En "Ubicacion del elemento" pegar exactamente esto:
   ```
   powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Users\ghriz\finanzas-mcghr\iniciar_finanzas.ps1"
   ```
3. Nombre: "Finanzas MCGHR"
4. Finish

### Cambiar el icono (opcional)

1. Click derecho en el acceso directo -> Propiedades -> Cambiar icono
2. Buscar un icono apropiado en `C:\Windows\System32\shell32.dll`

### Anclar a la barra de tareas

Click derecho en el acceso directo -> Anclar a la barra de tareas

A partir de ahi, un click en el icono arranca backend + frontend
y abre el browser automaticamente.

---

## Paso 5 — Arranque automatico con Windows (opcional)

Si queres que el stack arranque solo cuando enciendas la PC:

1. Presionar Win + R -> escribir `shell:startup` -> Enter
2. Se abre la carpeta de inicio de Windows
3. Copiar el acceso directo de "Finanzas MCGHR" a esa carpeta

La proxima vez que enciendas la PC, el backend y el frontend
van a arrancar solos (en ventanas de PowerShell minimizadas).

---

*Documento generado Junio 2026 -- Plataforma Financiera MCGHR*
