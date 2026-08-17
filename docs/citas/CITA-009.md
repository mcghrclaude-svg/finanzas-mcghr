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

**Excepcion -- emojis usados como iconos de UI/navegacion:**
El frontend de escritorio usa emojis como iconos en Sidebar.jsx,
ModalForm.jsx, categoriaConfig.js y Catalogos/index.jsx (tag, banco,
calendario, lupa, tacho de basura, flecha circular de refresh, reloj de
arena, engranaje, etc.). Es una convencion visual intencional, no texto
con tildes accidental -- no debe marcarse como violacion.

cerrar-sesion.ps1 excluye estos rangos Unicode ANTES de aplicar el chequeo
de ASCII (ver comentario junto al bloque CITA-009 en el script para el
detalle exacto de los rangos):
  - pares subrogados con alto D83C-D83E (pictogramas U+1F000-1FBFF: la
    inmensa mayoria de los emojis estandar)
  - simbolos BMP U+2190-21FF (Arrows)
  - simbolos BMP U+2300-23FF (Misc Technical)
  - simbolos BMP U+25A0-27BF (Geometric Shapes / Misc Symbols / Dingbats) --
    arranca en 25A0 a proposito para NO perdonar Box Drawing (2500-257F),
    que son separadores de comentario, no iconos
  - selector de variacion U+FE0F y ZWJ U+200D (secuencias emoji con modificador)

Estos rangos no se superponen con los caracteres que la regla protege de
verdad (acentos, enie: U+00C0-U+017F aprox.), asi que un archivo con texto
acentuado real sigue disparando el warning aunque tambien tenga emojis.

Nota: otros simbolos no-emoji usados como decoracion (guion largo U+2014,
separadores de comentario en Box Drawing U+2500, comilla angular U+203A,
punto medio U+00B7) siguen sin excepcion y disparan el warning -- son un
caso distinto (puntuacion/tipografia, no iconografia) y quedan fuera de
esta excepcion a proposito.

**Prevencion:**
cerrar-sesion.ps1 corre un grep sobre los archivos commiteados en la sesion
y muestra warning si encuentra caracteres fuera del rango ASCII 32-126
EXCEPTO en lineas JSX que contengan texto visible (entre tags o en atributos
de texto como title= y placeholder=).

**Senal de alarma para Hernan:**
Si ves caracteres como representaciones incorrectas de caracteres especiales
en el output de PowerShell o en archivos del repo (fuera del HTML/JSX),
este error esta ocurriendo.
