# Especificación Funcional — Plataforma Financiera MCGHR
## MVP v1

**Proyecto:** Plataforma de gestión financiera familiar  
**Titulares:** Hernan Rizzi (GHR) y Martha (MC)  
**Estado:** Especificación aprobada — pendiente desarrollo  
**Última actualización:** Junio 2026  
**Generado con:** Claude.ai Pro (mcghr.claude@gmail.com)

---

## Principios generales

- La aplicación es para uso familiar, no empresarial. La UX debe ser simple, ágil y predecible.
- El sistema nunca escribe datos financieros directamente — toda la data pasa por el ETL (`finanzas_familia.py`) o por acciones explícitas del usuario en la app.
- Toda clasificación automática requiere confirmación humana antes de considerarse definitiva.
- El sistema aprende de las correcciones humanas, nunca de forma autónoma.
- La app debe poder reemplazarse visualmente sin tocar la lógica de negocio.
- Backup y restore completo con un solo comando, sin dependencias externas.

---

## Módulo 1 — Ingesta de datos

### 1.1 Lectura de correos electrónicos

La app procesa correos de múltiples cuentas (Gmail OAuth, Hotmail/IMAP) buscando eventos financieros:

- Notificaciones de consumo con tarjeta de crédito/débito
- Confirmaciones de compra online
- Facturas con detalle de ítems (Rappi, Uber Eats, marketplaces)
- Cobros de suscripciones digitales (Netflix, Spotify, etc.)
- Avisos de pago, cobro y transferencia
- Extractos bancarios embebidos en el cuerpo del correo

Por cada correo relevante, el ETL propone una transacción preliminar con todos los campos que pudo inferir. La transacción queda en estado `pendiente` hasta confirmación humana. El sistema registra el correo fuente en `correos_procesados` para evitar reprocesamiento.

### 1.2 Lectura de archivos

Una carpeta monitoreada en OneDrive recibe documentos financieros depositados manualmente por los usuarios:

- Extractos bancarios en PDF (Bancolombia, BBVA, Banco de Occidente, InteractiveBrokers)
- Estados de cuenta de tarjetas de crédito
- Facturas en PDF o imagen (JPG, PNG)
- Fotos de tickets o recibos tomadas con el iPhone

El ETL detecta archivos nuevos, extrae texto (pdfplumber para PDFs, OCR para imágenes), y propone transacciones individuales o lotes. Los archivos se clasifican y mueven a su carpeta definitiva en OneDrive según titular, banco y período.

**Regla de clasificación de archivos:**
- Confianza ≥ 0.85 → carpeta definitiva automáticamente
- Confianza 0.60–0.84 → Stage area con sugerencia visible al usuario
- Confianza < 0.60 → Stage area sin clasificar, requiere revisión manual

### 1.3 Ingreso desde app mobile (iPhone)

La PWA mobile permite crear transacciones directamente desde el iPhone:

- Captura rápida: fecha, monto, categoría, descripción (completitud `minimo`)
- Foto de factura que se adjunta a una transacción
- Adición de contrapartes o categorías al catálogo

Los datos se escriben como JSON en una carpeta de OneDrive (`Inbox/`). El ETL los procesa, los registra en `inbox_mobile` con su estado, y los persiste en el schema final. La app web muestra el estado de cada JSON del inbox (pendiente, procesado, error).

### 1.4 Ingreso manual desde la app web

Formulario para registrar movimientos que no llegaron por ninguna fuente automática (efectivo, movimientos no notificados). Campos:

- Fecha, monto, moneda
- Tipo (gasto / ingreso)
- Categoría (hasta 3 niveles)
- Contraparte
- Cuenta / producto financiero
- Persona (GHR / MC / ambos)
- Descripción libre
- ¿Es recurrente?
- ¿Es reembolsable?
- Notas

Las transacciones manuales van directo a estado `confirmado` — no pasan por cola de confirmación.

### 1.5 Aprendizaje por confirmación

Cuando el usuario corrige una clasificación propuesta por el ETL, el sistema guarda la corrección como regla en `reglas_clasificacion`:

- Patrón de remitente / asunto / contenido → categoría, contraparte, cuenta correctas
- Las reglas tienen un score de confianza que sube con cada uso exitoso
- El ETL aplica las reglas automáticamente en futuras lecturas
- Las reglas solo se crean por acción humana explícita, nunca de forma autónoma
- El usuario puede ver, editar y desactivar reglas desde la app

### 1.6 Gestión de datos maestros

ABM completo (alta, baja lógica, edición) para:

- **Categorías:** jerarquía de hasta 3 niveles (ej: Alimentación > Restaurantes > Delivery). Sin borrado físico — solo inactivación.
- **Cuentas / productos financieros:** cuenta corriente, tarjeta de crédito, cuenta de ahorro, cuenta de inversión, wallet digital. Con titular, banco, moneda base, número (últimos 4 dígitos).
- **Contrapartes:** comercios, bancos, entidades gubernamentales, servicios. Con tipo y país.
- **Personas:** GHR, MC, y cualquier persona adicional que participe en transacciones familiares.
- **Monedas:** COP, USD, ARS y cualquier otra necesaria.

### 1.7 Gastos recurrentes

El sistema identifica y gestiona gastos que ocurren regularmente:

- Marcado manual como recurrente al confirmar o editar una transacción
- Detección automática sugerida cuando el mismo patrón aparece en ≥ 2 meses consecutivos (requiere confirmación humana)
- Agrupación por `id_recurrencia` para análisis de series históricas
- Categorías típicas: alquiler, servicios públicos, suscripciones digitales, impuestos, cuotas de crédito
- Visibilidad separada en reportes: gastos recurrentes vs. gastos variables

---

## Módulo 2 — Gestión de transacciones

### 2.1 Cola de confirmación

Pantalla central del flujo diario. Lista todas las transacciones en estado `pendiente` ordenadas por fecha descendente.

Por cada transacción pendiente se muestra:
- Fecha, descripción, monto, moneda
- Categoría sugerida (nivel 1 y 2)
- Contraparte sugerida
- Cuenta / banco origen
- Persona (GHR / MC)
- Nivel de confianza del ETL (visual: alto / medio / bajo)
- Fuente (correo, PDF, mobile, manual)
- Acceso al correo o documento fuente original

Acciones disponibles por transacción:
- **Confirmar:** acepta todos los campos tal como los propuso el ETL
- **Editar y confirmar:** modifica uno o más campos antes de confirmar
- **Descartar:** descarta la transacción (no se registra)
- **Ver fuente:** abre el correo o documento que originó la propuesta

Todas las acciones son undoables hasta que el usuario grabe explícitamente.

### 2.2 Lista de transacciones confirmadas

Vista completa con filtros combinables:
- Período (mes, rango de fechas)
- Categoría (con herencia de subcategorías)
- Cuenta / banco
- Persona
- Tipo (gasto / ingreso)
- Contraparte
- Estado de reembolso
- Recurrente / no recurrente

Permite editar cualquier transacción confirmada (con Undo). Exportación a Excel para uso en Power BI.

### 2.3 Sistema Undo / Redo

- Stack de acciones en memoria por sesión (no persiste entre sesiones)
- Undo y Redo al estilo Office (Ctrl+Z / Ctrl+Y)
- Al intentar grabar: modal de confirmación — "Vas a guardar los cambios. No podrás deshacerlos una vez grabado. ¿Confirmar?"
- Al intentar cerrar la app con cambios sin grabar: alerta — "Tenés cambios sin guardar. Si salís ahora, los perdés."
- La pila se vacía al grabar exitosamente o al descartar cambios de forma explícita

---

## Módulo 3 — Presupuesto

### 3.1 Definición del presupuesto mensual

- El presupuesto se define por categoría, por mes calendario
- Es familiar: no se segmenta por persona
- Puede variar mes a mes — no hay "copiar del mes anterior" automático (puede ofrecerse como sugerencia)
- Al definir el presupuesto de un mes, la app muestra el gasto histórico real de la misma categoría en los últimos 1, 3 y 6 meses como referencia
- Se pueden presupuestar categorías de nivel 1, 2 o 3 — el sistema agrega correctamente hacia arriba

### 3.2 Control de ejecución presupuestal

Durante el mes, el usuario puede ver:
- Monto presupuestado vs. gastado real a la fecha
- **Proyección de cierre:** si el ritmo de gasto actual continúa, ¿cuánto se gastará al cierre del mes? Calculado como: `gastado / días_transcurridos * días_del_mes`
- Alerta visual en categorías cuya proyección supera el 90% del presupuesto antes del día 20 del mes
- El foco está en las desviaciones, no en los valores absolutos — una categoría dentro del presupuesto no requiere atención visual prominente

---

## Módulo 4 — Obligaciones

### 4.1 Registro de obligaciones

Una obligación es cualquier compromiso de pago periódico conocido de antemano:

- **Deudas financieras:** préstamos personales, créditos hipotecarios, créditos de vehículo. Con capital original, tasa de interés, plazo, cuotas totales. Cada cuota tiene desglose de capital e intereses.
- **Obligaciones recurrentes no financieras:** alquiler, servicios públicos (agua, gas, electricidad, internet), impuestos periódicos. Con monto estimado y fecha de vencimiento mensual.
- **Suscripciones y membresías:** servicios digitales, seguros, membresías. Con monto fijo y fecha de cobro.

### 4.2 Control de pagos

- Cada obligación tiene un calendario de vencimientos
- Cuando llega una transacción confirmada que corresponde al pago de una obligación, el sistema la vincula automáticamente (o sugiere el vínculo)
- Si una obligación llega a su fecha de vencimiento sin pago registrado, genera una alerta visible en el dashboard
- Para deudas financieras: visualización de evolución del capital pagado, capital pendiente, intereses pagados acumulados y proyección de cancelación

### 4.3 Recordatorios

- Alertas en el dashboard cuando una obligación está próxima a vencer (configurable: 3, 5 o 7 días antes)
- Alertas cuando una obligación venció sin pago confirmado
- Las alertas se muestran en el dashboard y en la pantalla de obligaciones

### 4.4 Base para análisis futuros

El registro de obligaciones provee la base para que Claude pueda recomendar (en el módulo de analítica):
- Optimización del orden de pago de deudas (avalancha vs. bola de nieve)
- Proyección de flujo de caja mensual considerando obligaciones fijas
- Alertas de meses con picos de obligaciones

---

## Módulo 5 — Inversiones

### 5.1 Registro de inversiones

Registro básico de activos financieros del hogar:

- **Cuentas de ahorro / plazo fijo:** saldo, moneda, tasa de rendimiento, entidad
- **Acciones y ETFs (brokerage):** cuenta en Interactive Brokers u otro broker, posición por instrumento (ticker, cantidad de unidades, precio promedio de compra), moneda
- **Inmuebles en construcción (pozo):** precio de compra pactado, cuotas pagadas, cuotas pendientes, fecha estimada de entrega, valuación de mercado si disponible
- **Otros activos:** cualquier activo valorizable no contemplado en las categorías anteriores

### 5.2 Seguimiento de inversiones

Por cada inversión:
- Capital invertido acumulado (cuánto dinero real entró)
- Valuación actual (ingresada manualmente o desde extractos de brokerage)
- ROI calculado: `(valuación_actual - capital_invertido) / capital_investido * 100`
- Flujo generado: ingresos asociados a la inversión (alquileres, dividendos, intereses)
- Comparación vs. objetivo o plan original si fue definido

### 5.3 Trazabilidad ingreso-inversión

Cuando llega un ingreso que corresponde a una inversión (alquiler de un inmueble, dividendo de acciones), el usuario puede vincularlo a la inversión correspondiente. Esto permite:
- Ver el rendimiento real incluyendo flujos generados
- Excluir esos ingresos del análisis de gastos personales si se desea
- Proyectar rendimiento futuro con base en flujos históricos

### 5.4 Patrimonio neto

Calculado como: `activos (inversiones + saldos de cuentas) - pasivos (saldo de deudas)`.
Disponible como indicador en el dashboard. Calculado desde las posiciones y valuaciones registradas — no es ingresado manualmente.

### 5.5 Obligaciones asociadas a inversiones

Una inversión en pozo u otro activo financiado genera automáticamente una obligación vinculada (las cuotas mensuales). La app mantiene la trazabilidad inversión ↔ obligación ↔ transacciones de pago.

---

## Módulo 6 — Dashboard

### 6.1 Pantalla de inicio (PC y iPhone)

La pantalla de bienvenida en ambos dispositivos muestra:

**Sección superior — alertas activas:**
- Transacciones pendientes de confirmar (con contador)
- Obligaciones próximas a vencer o vencidas sin pago
- Categorías de presupuesto con proyección de desvío

**Sección central — presupuesto del mes:**
- Una tarjeta por categoría activa con presupuesto definido
- Cada tarjeta muestra: presupuestado / gastado / proyección
- Color según estado: verde (en orden), amarillo (atención), rojo (desvío)
- El foco visual está en las desviaciones, no en los valores en orden

**Sección inferior — resumen financiero:**
- Ingresos vs. gastos totales del mes
- Indicador de patrimonio neto (cuando módulo de inversiones esté activo)

### 6.2 Adaptación mobile vs. desktop

- **Desktop:** todas las secciones visibles simultáneamente, layout de múltiples columnas, tarjetas más densas en información
- **iPhone:** tarjetas grandes apiladas verticalmente, scroll natural, acción principal siempre visible sin scrollear, optimizado para uso con el pulgar

---

## Módulo 7 — Analítica con Claude

### 7.1 Filosofía

La analítica avanzada no es un dashboard estático — es una conversación con Claude sobre los datos financieros de la familia. Claude tiene acceso de lectura a la base de datos y puede responder preguntas, identificar patrones y hacer recomendaciones.

### 7.2 Capacidades básicas embebidas en la app

- Resumen mensual narrativo: "En junio gastaron $X, un 12% más que el promedio de los últimos 3 meses. El desvío principal fue en restaurantes."
- Detección de gastos inusuales: transacciones que se desvían significativamente del patrón histórico en la misma categoría o contraparte
- Identificación de oportunidades: categorías donde el gasto creció sostenidamente en los últimos 3+ meses

### 7.3 Análisis bajo demanda (conversacional)

El usuario puede desde la app abrir una sesión de Claude con contexto financiero precargado y preguntar en lenguaje natural:
- "¿En qué estamos gastando más de lo que deberíamos?"
- "¿Cómo podemos bajar el gasto en alimentación un 15%?"
- "¿Cuánto tiempo nos falta para pagar el crédito del auto si pagamos $200K extra por mes?"
- "¿Cómo va el ROI de la inversión en el apartamento en pozo?"

### 7.4 Evolución futura

- Recomendaciones proactivas de optimización de flujo de caja
- Proyecciones de patrimonio neto a 12, 24 y 60 meses
- Alertas de concentración de riesgo en inversiones
- Comparación vs. benchmarks de ahorro familiar recomendados

---

## Módulo 8 — Backup y Restore

### 8.1 Filosofía

El backup es siempre completo — no hay backups incrementales. Un solo archivo debe ser suficiente para restaurar la aplicación completa en una PC nueva o un Docker nuevo, sin configuración adicional.

### 8.2 Contenido del backup

El backup incluye absolutamente todo:
- Base de datos SQLite (`finanzas.db`) con todos los datos
- Archivos de configuración (`config_correos.json`, variables de entorno)
- Credenciales OAuth (tokens de Gmail y otras APIs) — cifradas
- PDFs y documentos en OneDrive (extractos, facturas, fotos)
- Código fuente completo (o referencia al commit exacto del repo)
- Reglas de clasificación aprendidas

### 8.3 Operación de backup

- Disponible desde la app web con un botón "Generar backup"
- También ejecutable desde línea de comandos: `python backup.py`
- Genera un único archivo `.zip` con timestamp: `mcghr_backup_YYYYMMDD_HHMMSS.zip`
- El archivo se guarda en una carpeta configurable (local o OneDrive)
- Muestra progreso y tamaño estimado antes de confirmar
- Tiempo estimado visible durante la generación

### 8.4 Operación de restore

- Script standalone que no depende de que la app esté instalada: `python restore.py mcghr_backup_YYYYMMDD.zip`
- El script valida la integridad del backup antes de restaurar
- Restaura todo en la ubicación configurada o pregunta dónde
- Al finalizar, la app queda lista para usar sin pasos adicionales
- El restore pide confirmación explícita antes de sobrescribir datos existentes

### 8.5 Frecuencia recomendada

- Backup automático semanal (configurable) ejecutado por el scheduler del sistema
- Backup manual antes de cualquier migración o actualización mayor
- Los backups se retienen por 90 días por defecto (configurable)

---

## Requisitos no funcionales

### Rendimiento
- El dashboard debe cargar en menos de 2 segundos en condiciones normales
- Las listas de transacciones usan paginación o scroll infinito — nunca cargan toda la tabla de una vez
- Las consultas analíticas pesadas corren en background con indicador de progreso

### Usabilidad
- La app predice la acción más probable del usuario y la presenta como opción principal
- Flujos críticos (confirmar transacción, registrar gasto manual) en máximo 3 toques/clics
- Responsive: misma app en PC y iPhone, layout adaptado a cada dispositivo
- Soporte para uso con un solo pulgar en mobile
- Modo oscuro y modo claro (sigue la preferencia del sistema operativo)

### Arquitectura y código
- Separación estricta UI / lógica de negocio: el frontend nunca accede directamente a la base de datos
- Backend stateless: toda la lógica de negocio en el backend (FastAPI), el frontend solo presenta y envía
- API REST versionada desde el inicio (`/api/v1/`)
- Código documentado en inglés (comentarios, nombres de variables, funciones)
- Commits semánticos: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`
- Tests unitarios para lógica de negocio crítica (clasificación, cálculo de proyecciones, patrimonio neto)
- Sin valores hardcodeados: toda configuración en `config_correos.json` o variables de entorno

### Seguridad
- **Fase 1 (MVP):** seguridad basada en acceso físico al dispositivo. La app corre solo en red local.
- **Fase 2 (futura):** autenticación por usuario con contraseña, encriptación de campos sensibles (credenciales, tokens), HTTPS con certificado self-signed para red local
- Los tokens OAuth de Gmail nunca se loguean ni se incluyen en backups sin cifrado
- La base de datos SQLite no se expone directamente — solo accesible vía API

### Datos y privacidad
- Ningún dato financiero sale de la red local (excepto las llamadas a Claude API, que no incluyen datos de identificación personal)
- Los correos procesados se leen pero no se modifican (no se marcan como leídos)
- Los PDFs originales se conservan siempre — nunca se borran

### Portabilidad y despliegue
- La app debe poder correr en: Windows 11 (desarrollo y uso principal), Docker (Raspberry Pi o cualquier servidor Linux), macOS (desarrollo)
- `docker-compose.yml` incluido para despliegue en un comando
- Variables de entorno documentadas en `.env.example`
- El frontend buildado es un conjunto de archivos estáticos — puede servirse desde nginx sin Node.js

### Documentación
- `CLAUDE.md` en la raíz del repo: contexto completo del proyecto para cualquier herramienta de IA
- `README.md`: instrucciones de instalación, configuración y uso en menos de 10 minutos
- `docs/functional_spec.md`: este documento
- `docs/architecture.md`: decisiones técnicas y estructura del proyecto
- `docs/schema_v1.md`: documentación del schema de base de datos (existente)
- `docs/api.md`: documentación de endpoints REST (a generar)
- Cada módulo Python documentado con docstrings
- Changelog en `CHANGELOG.md` desde la primera versión funcional

### Evolución y mantenibilidad
- Cada módulo nuevo se agrega sin modificar los existentes (principio Open/Closed)
- El schema de BD se migra con scripts incrementales numerados (`schema/finanzas_v1_2.sql`, etc.)
- La UI puede rediseñarse completamente sin tocar el backend
- Los módulos futuros planificados (InversionesBroker, AnalisisGastos, PresupuestoBase0, GestionSemanal) tienen carpeta reservada en la estructura

---

## Fases de desarrollo

### Fase 1 — MVP (prioridad actual)
- Ingesta desde correos y PDFs (ETL ya en desarrollo)
- Cola de confirmación de transacciones
- Ingreso manual de transacciones
- Gestión de datos maestros (catálogos)
- Presupuesto mensual + control de ejecución
- Dashboard básico (presupuesto vs. real + alertas)
- Gastos recurrentes
- Backup y restore completo

### Fase 2 — Extensión
- Obligaciones (deudas, pagos recurrentes, recordatorios)
- Inversiones básicas (registro y seguimiento)
- App mobile PWA mejorada
- Analítica conversacional con Claude

### Fase 3 — Madurez
- Patrimonio neto consolidado
- Recomendaciones proactivas de Claude
- Proyecciones financieras
- Autenticación por usuario
- Encriptación de datos sensibles

---

*Documento generado en Junio 2026 — Plataforma Financiera MCGHR*
*Para continuar el proyecto desde este documento, leer también: `docs/architecture.md`, `docs/schema_v1.md`, `CLAUDE.md`*
