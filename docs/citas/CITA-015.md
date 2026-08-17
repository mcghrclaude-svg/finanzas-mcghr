# CITA-015 -- Tarea Programada de Windows necesita un .bat intermedio

**Frecuencia:** 1 vez detectada (sesion 2026-08-16, backend/services/scheduled_task_service.py)
**Nivel:** 1-AUTOMATIZADO

**Error:**
Al crear la Tarea Programada (`schtasks /Create /TR ...`) para correr
`scripts/import_pwa_gastos.py` periodicamente, la tarea se creaba sin error
pero el script fallaba al ejecutarse. Dos causas distintas, encontradas en
orden:

1. Task Scheduler no hereda el directorio de trabajo del repo -- por defecto
   corre desde la carpeta del ejecutable (`venv\Scripts\`), no desde la raiz
   del repo. `python -m scripts.import_pwa_gastos` necesita el repo como cwd
   para resolver el paquete `scripts`; sin eso falla con `ModuleNotFoundError`.
2. El intento de arreglo obvio -- pasar `cmd.exe /c "cd /d "X" && ..."`
   directo como valor de `/TR` de `schtasks` -- no funciona. Las comillas
   anidadas confunden el parser de `schtasks`, que termina ignorando el
   `cmd.exe /c` y guardando solo el comando de Python pelado (confirmado
   inspeccionando el XML de la tarea creada con `schtasks /Query /XML`).
   Sin el `cd` real, vuelve a fallar por el mismo motivo que el punto 1.

**Resolucion:**
En vez de pelear con el quoting de Windows dentro de `/TR`, `scheduled_task_service._comando_script()`
escribe un `.bat` chico (`scripts/_run_import_pwa.bat`, generado, no
versionado) que hace el `cd /d` y corre el script en dos lineas separadas, y
`/TR` apunta directo a ese `.bat` sin anidamiento de comillas. Ver commit
`526fb0f`.

**Prevencion:**
Al pasar cualquier comando compuesto (`cd &&`, pipes, redirecciones) como
`/TR` de `schtasks`, no confiar en que el quoting anidado sobreviva el
parser -- escribir un `.bat` intermedio y apuntar `/TR` a ese archivo. Es
mas facil de depurar (se puede correr el `.bat` a mano) y evita esta clase
entera de problemas de escaping.

**Nota sobre una sesion anterior (reconciliacion):**
En una sesion previa se habia diagnosticado que Task Scheduler no ejecutaba
nada en esta maquina sin acceso de administrador -- ni un `echo` trivial de
prueba. No quedo registro escrito en el repo de esa sesion (config exacta
probada, mensajes de error), asi que esa causa no se pudo reconstruir con
certeza. Lo que si esta confirmado hoy, verificado en vivo (`schtasks /Query /TN FinanzasMCGHR_ImportPWA /FO LIST /V`)
y contra `logs/task_debug.log` de una corrida real: con `/RL LIMITED` y sin
`/RU` explicito, `schtasks` crea la tarea para el usuario interactivo actual
(`Run As User: ghriz`, `Logon Mode: Interactive only`), sin pedir contrasena
guardada ni privilegios elevados, y la tarea corre visible en la sesion del
usuario. En esa configuracion la tarea ejecuto el import real y proceso 5
archivos (fallo por datos -- categorias inexistentes en 5 de 5 gastos -- no
por no poder ejecutarse). Tratar el estado actual como "funciona en esta
configuracion especifica", no como "quedo resuelto y entendido de punta a
punta".

**Senal de alarma para Hernan:**
Si la tarea aparece en el Programador de tareas de Windows pero nunca corre
(`Last Run Time` no cambia), sospechar del comando (`/TR`) antes que de
permisos. Si corre pero el resultado (`Last Result`) es distinto de 0,
revisar `logs/task_debug.log` -- un `Last Result` de 1 con contenido en ese
log es un fallo de datos (por ejemplo categorias faltantes), no un fallo de
ejecucion.
