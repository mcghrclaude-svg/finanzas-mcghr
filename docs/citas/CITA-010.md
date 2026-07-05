# CITA-010 -- Loop de fix sin diagnostico previo

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
