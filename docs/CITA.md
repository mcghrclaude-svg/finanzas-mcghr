# CITA -- Common Issues To Avoid
# Finanzas MCGHR

Registro de errores repetidos en el proyecto y como prevenirlos.
Actualizado automaticamente por cerrar-sesion.ps1 al cierre de cada sesion.

Nivel de prevencion:
  1-AUTOMATIZADO  El artefacto mismo detecta y bloquea el error
  2-HOOK          cerrar-sesion.ps1 o un git hook lo verifica
  3-CONTEXTO      Solo en contexto: reduce frecuencia, no garantiza prevencion

Senal de alarma: lo que Hernan puede observar sin conocimiento tecnico
para detectar que este error esta ocurriendo.

---

## CITA-001 -- Omitir Set-ExecutionPolicy en instrucciones de scripts PS1

**Frecuencia:** 4+ veces en multiples chats
**Nivel:** 1-AUTOMATIZADO

**Error:**
El agente entrega scripts PS1 o instrucciones de ejecucion sin incluir
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass.
El usuario ve "cannot be loaded, not digitally signed" y el script no corre.

**Prevencion automatizada:**
Cada script PS1 generado debe tener en las primeras 3 lineas:
  # INSTRUCCIONES DE EJECUCION:
  #   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  #   .\nombre-del-script.ps1
Y ademas, verificacion en codigo al inicio del script:
  $policy = Get-ExecutionPolicy -Scope Process
  if ($policy -eq "Restricted" -or $policy -eq "AllSigned") { ... exit 1 }

**Senal de alarma para Hernan:**
Si el agente te da un comando de PS1 sin que la primera linea sea
Set-ExecutionPolicy, el paso esta faltando.

---

## CITA-002 -- ErrorActionPreference Stop rompe scripts que corren fuera del repo

**Frecuencia:** 3 veces
**Nivel:** 1-AUTOMATIZADO

**Error:**
$ErrorActionPreference = "Stop" a nivel global hace que un comando git
que falla (porque el script corre fuera del repo) detenga todo el script
antes de llegar al Read-Host de fallback. El usuario ve un error rojo
y no puede ingresar la ruta del repo.

**Prevencion automatizada:**
Nunca usar $ErrorActionPreference = "Stop" a nivel global en scripts PS1.
Patron obligatorio para deteccion del repo:
  $ErrorActionPreference = "Continue"
  try {
      $detected = git rev-parse --show-toplevel 2>$null
      if ($LASTEXITCODE -eq 0 -and $detected) { $RepoPath = $detected }
  } catch {}
  if (-not $RepoPath) {
      $RepoPath = Read-Host "Ruta del repo [C:\Users\ghriz\finanzas-mcghr]"
      if (-not $RepoPath) { $RepoPath = "C:\Users\ghriz\finanzas-mcghr" }
  }

**Senal de alarma para Hernan:**
Si el script muestra un error rojo con "fatal: not a git repository"
y termina sin pedirte la ruta, este error esta ocurriendo.

---

## CITA-003 -- Get-ChildItem sin @() falla con un solo resultado en StrictMode

**Frecuencia:** 2 veces
**Nivel:** 1-AUTOMATIZADO

**Error:**
Get-ChildItem puede devolver un objeto unico (no array) cuando encuentra
un solo archivo. Con Set-StrictMode activo, llamar .Count sobre ese objeto
lanza "The property Count cannot be found on this object".

**Prevencion automatizada:**
Siempre envolver Get-ChildItem en @():
  $archivos = @(Get-ChildItem $ruta -Filter "*.py" -ErrorAction SilentlyContinue)
  $count = $archivos.Count

**Senal de alarma para Hernan:**
Error "The property Count cannot be found on this object" en scripts PS1.

---

## CITA-004 -- Asumir contenido de archivos sin leerlos en el turno actual

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

---

## CITA-005 -- Asumir schema de DB sin verificar la tabla real

**Frecuencia:** 5 veces (genero 4 iteraciones de fix_modelo)
**Nivel:** 3-CONTEXTO

**Error:**
El agente modifica un modelo SQLAlchemy asumiendo que sabe que columnas
tiene la tabla real. La DB real puede tener columnas distintas a las del
modelo (resultado de migraciones parciales, seeds, o decisiones de otros chats).
Resultado: errores de tipo "table has no column named X" o
"categorias.find is not a function" en runtime.

**Prevencion:**
Antes de tocar cualquier modelo, el agente debe pedirte que corras:
  echo "PRAGMA table_info(nombre_tabla);" | sqlite3 "ruta\a\finanzas_dev.db"
Y comparar columna por columna contra el modelo antes de escribir codigo.

**Senal de alarma para Hernan:**
Si aparece un error de columna inexistente en tests o en runtime,
y el agente propone un fix sin haber pedido el PRAGMA table_info primero,
este error esta ocurriendo.

---

## CITA-006 -- Variables VITE_* en .env.dev rompen el backend

**Frecuencia:** 2 veces
**Nivel:** 2-HOOK

**Error:**
El agente pone variables VITE_* en .env.dev junto con las del backend.
pydantic-settings rechaza variables desconocidas y el backend no arranca.

**Prevencion:**
cerrar-sesion.ps1 verifica que .env.dev no contenga variables VITE_*.
Si las encuentra, muestra un warning con la linea exacta a mover.
Las variables VITE_* van SIEMPRE en frontend/.env.local.

**Senal de alarma para Hernan:**
Si el backend no arranca y el error menciona "extra inputs are not permitted"
o una variable VITE_*, este error esta ocurriendo.

---

## CITA-007 -- Modulos nuevos creados en pages/ en lugar de modules/

**Frecuencia:** 2 veces
**Nivel:** 2-HOOK

**Error:**
El agente crea un modulo nuevo en frontend/src/pages/ en lugar de
frontend/src/modules/. App.jsx importa desde modules/, asi que
el modulo en pages/ nunca se renderiza aunque el codigo sea correcto.

**Prevencion:**
cerrar-sesion.ps1 detecta archivos .jsx nuevos en src/pages/ y muestra
un warning indicando que probablemente deberian estar en src/modules/.

**Senal de alarma para Hernan:**
Si navegas a una URL y ves el placeholder "en desarrollo" aunque
el agente dijo que implemento el modulo, este error puede estar ocurriendo.

---

## CITA-008 -- Commits con git add -A mezclan cambios de chats distintos

**Frecuencia:** 2 veces
**Nivel:** 1-AUTOMATIZADO

**Error:**
Un git add -A en un chat de backend incluye archivos modificados por
el chat de UX (o viceversa) porque ambos trabajaban sobre main.
El commit mezcla cambios de dos contextos distintos sin que nadie lo decida.

**Prevencion automatizada:**
iniciar-chat-tema.ps1 crea una branch por tema (chat-ux, chat-backend).
chequear-conflictos.ps1 detecta solapamiento antes de mergear.
Los scripts de instalacion nunca usan git add -A: siempre listan
explicitamente los archivos que corresponden a esa entrega.

**Senal de alarma para Hernan:**
Si git status muestra archivos modificados que no corresponden
al tema del chat actual, este error puede estar ocurriendo.

---

## CITA-009 -- Caracteres especiales en codigo generan errores de encoding

**Frecuencia:** 5+ veces en todos los chats
**Nivel:** 2-HOOK

**Error:**
El agente incluye acentos, enie u otros caracteres no-ASCII en comentarios,
strings de logica o nombres de variables/archivos. En Windows con codificacion
CP1252 o en terminales PS1, estos caracteres se corrompen y generan errores
de parsing o caracteres ilegibles en los outputs.

**Excepcion -- texto visible en la UI:**
Los caracteres Unicode en texto visible al usuario dentro de JSX estan
PERMITIDOS. Esto incluye iconos y simbolos en botones, labels y badges
(ejemplos: triangulos de dropdown como v, flechas como arriba/abajo,
refresh como circularArrow, close como X con estilo, checkmarks).
La restriccion aplica exclusivamente a: comentarios, nombres de variables,
strings de logica, nombres de archivo y strings que se loguean o persisten.

**Prevencion:**
cerrar-sesion.ps1 corre un grep sobre los archivos commiteados en la sesion
y muestra warning si encuentra caracteres fuera del rango ASCII 32-126
EXCEPTO en lineas JSX que contengan texto visible (entre tags o en atributos
de texto como title= y placeholder=).

**Senal de alarma para Hernan:**
Si ves caracteres como representaciones incorrectas de caracteres especiales
en el output de PowerShell o en archivos del repo (fuera del HTML/JSX),
este error esta ocurriendo.

---

## CITA-010 -- Loop de fix sin diagnostico previo

**Frecuencia:** 3+ veces (fix_modelo2, fix_modelo3, fix_modelo4, instalar_modelo_final)
**Nivel:** 3-CONTEXTO

**Error:**
Ante un error de tests o runtime, el agente genera un fix inmediato
sin declarar explicitamente: que esperaba, que paso realmente, y por que
ese fix especifico resuelve la causa raiz. El resultado es una cadena
de fixes que resuelven el sintoma del fix anterior, no el problema original.

**Prevencion:**
Regla en Custom Instructions: si un fix no funciona al primer intento,
parar y mostrar diagnostico completo antes de proponer el siguiente intento.
Hernan debe poder aprobar la hipotesis antes de que se genere codigo nuevo.

**Senal de alarma para Hernan:**
Si el agente te entrega un tercer script de fix sin haberte mostrado
un diagnostico explicito del problema raiz, frenar y pedir el diagnostico.

---

## CITA-011 -- Inconsistencia interna entre archivos del mismo entregable

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

---

## CITA-012 -- Divergencia silenciosa entre .claude\skills y el repo

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
