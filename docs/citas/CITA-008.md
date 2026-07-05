# CITA-008 -- Commits con git add -A mezclan cambios de chats distintos

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
