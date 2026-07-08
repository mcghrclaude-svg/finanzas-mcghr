# Escenarios de prueba -- Pipeline ETL Gmail (dev)

Cubre los 7 escenarios minimos del pipeline `scripts/etl/` (extraccion +
correlacion), verificados en esta sesion sobre `data/dev/finanzas_dev.db`.
Ver [TESTING_PIPELINE_ETL.md](TESTING_PIPELINE_ETL.md) para como correr
cada script manualmente.

Generar la data de cada escenario:
```
python scripts/etl/generar_datos_prueba.py --escenario <letra>
```
Esto escribe `staging/candidatos_escenario_<letra>.json` (y para el
escenario g, ademas siembra 2 transacciones existentes en la DB).

---

## Decision de diseno importante: "cero candidatos" NO es ambiguo

La correlacion (Capa 2) busca transacciones existentes por mismo titular,
monto +/-1% y fecha +/-3 dias. Si esa busqueda no encuentra NINGUN
candidato, se crea una transaccion nueva directamente -- es el caso normal
de un hecho economico visto por primera vez (la inmensa mayoria de los
casos). El bucket de ambiguos es solo para MULTIPLES candidatos sin forma
de decidir cual es el correcto (ver escenario g). Si "cero candidatos"
tambien fuera a ambiguos, todo primer evento quedaria trabado esperando
resolucion manual.

---

## a) Correo de marketing puro

**Entrada:** remitente `promociones@tiendagenerica.com`, sin patron de
monto en el texto.

**Resultado esperado:** se descarta (`descartable=true`, motivo
`remitente_marketing`). No genera transaccion. Queda registrado en
`correos_procesados` con `resultado='descartado'`.

**Verificado:** `correlacion.py` -> Nuevas: 0, Descartadas: 1.

---

## b) Correo de comercio con monto en el snippet

**Entrada:** `tests/fixtures/correos/bancolombia_gasto_ejemplo.eml` --
"Transaccion aprobada por $45,900 en SUPERMERCADOS EXITO".

**Resultado esperado:** transaccion pendiente, monto detectado
directamente en el snippet (`necesito_lectura_completa=false`), la
contraparte "Exito" resuelve contra el catalogo real (fila `EXITO` en
`contrapartes`) -- sin entidad potencial.

**Verificado:** transaccion nueva, `confianza=0.65` (base de correo de
comercio, sin penalizaciones -- la banda mas alta que produce este
pipeline heuristico para un correo sin ambiguedad), `completitud=parcial`
(fecha + monto + cuenta resueltos = 3/4 campos; `id_categoria` no se
clasifica en este pipeline, ver nota abajo), contraparte = Exito,
0 entidades potenciales.

---

## c) "Order Programada" -- monto fuera del snippet (regla B)

**Entrada:** snippet sin monto ("Tu pedido fue programado
exitosamente..."), pero el cuerpo completo si trae "Total de tu pedido:
$128.500".

**Resultado esperado:** `extraccion.py` detecta que el asunto/snippet
matchea palabras clave de regla B ("order programada") y revisa el cuerpo
completo antes de descartar. Encuentra el monto ahi. Transaccion pendiente
igual que un caso normal, pero marcada `necesito_lectura_completa=true`.

**Verificado:** transaccion nueva, `confianza=0.60` (0.65 base - 0.05 de
penalizacion por lectura fallback), `completitud=minimo` (solo
fecha+monto, sin contraparte ni cuenta reconocidas en el texto).

---

## d) Correo de comercio + SMS reenviado que correlacionan

**Entrada:** dos correos en el mismo JSON de candidatos --
1. Correo Bancolombia: "Compra aprobada por $89.900 en RAPPI", 20/06 13:15.
2. SMS reenviado (asunto = codigo corto `891333`, igual que el filtro
   `bancolombia_sms` de `config_correos.json`): mismo monto, 20/06 13:17.

**Resultado esperado:** el primer correo crea la transaccion (cero
candidatos de correlacion todavia). El segundo (SMS) encuentra
exactamente un candidato -- el que acaba de crear el primero -- y
fusiona: le asigna `id_evento`, sube el `estado_enriquecimiento` a
`enriquecido`, y la confianza queda mas alta que si fuera una sola
fuente (un SMS reenviado tiene una base de confianza mayor que un correo
de comercio, mas el bono por correlacion limpia).

**Verificado:** una sola transaccion (no dos), `id_evento` compartido,
`estado_enriquecimiento='enriquecido'`, `confianza=0.95`
(0.80 base SMS + 0.15 bono de correlacion limpia) vs. 0.65 que hubiera
tenido el correo de Bancolombia solo.

**IMPORTANTE:** los dos correos deben ir en el MISMO archivo de entrada
de `correlacion.py` (una sola corrida) para que el segundo encuentre al
primero -- si se corren en corridas separadas, el orden y el commit de
cada INSERT sigue siendo el mismo (SQLite autocommit por sentencia via
`conn.commit()` al final), pero para simplificar la prueba se generan
juntos en `staging/candidatos_escenario_d.json`.

---

## e) Mismo message_id procesado dos veces

**Entrada:** reusa el mismo `message_id` del escenario b
(`test-b-bancolombia-exito`).

**Resultado esperado:** la segunda vez que `correlacion.py` procesa ese
`message_id` (ya sea porque se corrio el escenario b antes, o porque se
corre el escenario e dos veces seguidas), la Capa 1 (dedup contra
`correos_procesados`) lo saltea sin crear una segunda transaccion.

**Verificado:** segunda corrida (y toda corrida subsiguiente) sobre el
mismo `message_id` -> `Ya procesadas (dedup): 1`, `Nuevas: 0`.

---

## f) Contraparte que no existe en el catalogo

**Entrada:** "Compra aprobada por $32.000 en TIENDA NUEVA XYZ" -- ningun
comercio del catalogo (`contrapartes`) matchea ese texto.

**Resultado esperado:** transaccion pendiente igual, mas una fila en
`entidades_potenciales` (`tipo='contraparte'`,
`valor_propuesto='TIENDA NUEVA XYZ'`, `estado='pendiente'`) referenciando
la transaccion via `id_transaccion`. La FK de contraparte en la
transaccion queda `NULL` (pero visible via la entidad potencial, no
"silenciosamente perdida").

**Verificado:** transaccion nueva, 1 entidad potencial tipo `contraparte`,
`confianza=0.55` (0.65 base - 0.10 penalizacion por entidad potencial
generada).

---

## g) Dos candidatos de correlacion posibles (ambiguo)

**Entrada:** `generar_datos_prueba.py --escenario g` primero siembra dos
transacciones existentes en la DB ($150.000 COP, GHR, 25/06 y 26/06 --
ambas dentro de la ventana +/-3 dias de un tercer evento). Despues llega
un correo Bancolombia por el mismo monto el 24/06.

**Resultado esperado:** la busqueda de correlacion encuentra 2 candidatos
limpios (ambos dentro de rango) y no hay forma de decidir cual es el
correcto sin mas contexto -- no se inserta como correlacionado a ciegas.
El caso va a `staging/ambiguos_escenario_g.json` con
`motivo='multiples_candidatos'` y el detalle de los ids candidatos. El
correo queda marcado como procesado (`resultado='ambiguo'`) para no
reintentarlo en la proxima corrida sobre el mismo rango de fechas.

**Verificado:** `Ambiguas: 1`, 0 transacciones nuevas para este correo,
archivo `ambiguos_escenario_g.json` con el caso y sus 2 candidatos.

---

## Nota sobre clasificacion de categoria

Este pipeline heuristico (regex + reglas simples, sin LLM) **no clasifica
`id_categoria` automaticamente** -- queda siempre `NULL`. La clasificacion
por categoria requiere razonamiento contextual (ver
`docs/ETL_DISENO_FUNCIONAL.md`, seccion "Clasificacion con contexto"), que
es trabajo del ETL real de Claude Desktop en produccion, no de este
pipeline de testing. Por esto, la `completitud` calculada por este
pipeline nunca llega a `'completo'` (maximo 3 de 4 campos: fecha, monto,
cuenta -- falta categoria). Esto es esperado y no es un bug.
