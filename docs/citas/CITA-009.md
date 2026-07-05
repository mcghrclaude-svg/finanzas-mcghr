# CITA-009 -- Caracteres especiales en codigo generan errores de encoding

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
