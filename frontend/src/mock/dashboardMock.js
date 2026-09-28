/**
 * Datos mock del dashboard — dos escenarios:
 *
 *   CON_HISTORIAL:  velocidad_historica disponible → riesgo por velocidad funciona
 *   SIN_HISTORIAL:  primer período del sistema, vel_hist=null → dashboard neutro
 *
 * Escenario activo: VITE_MOCK_SCENARIO=con_historial | sin_historial
 * Default: con_historial
 *
 * Re-exporta EJECUCION_MOCK = CON_HISTORIAL para backward compatibility.
 */

// ── Resumen (mismo para ambos escenarios) ─────────────────────────────────

export const RESUMEN_MOCK = {
  periodo: {
    id: '2026-06',
    fecha_inicio: '2026-05-25',
    fecha_fin_tentativa: '2026-06-24',
    fecha_fin_real: null,
    estado: 'abierto',
    dias_transcurridos: 15,
    dias_totales: 30,
  },
  ingresos_acreditados: 23_000_000,
  gastos_acumulados: 8_400_000,
  saldo_disponible_hoy: 14_600_000,
  saldo_proyectado_cierre: 6_200_000,
  patrimonio_neto: 284_000_000,
  variacion_patrimonio_mes_anterior: 4_100_000,
  inbox_pendiente_count: 7,
}

// ── Escenario A: CON histórico ─────────────────────────────────────────────
// vel_hist != null → riesgo calculado, línea punteada visible

export const EJECUCION_CON_HISTORIAL = {
  periodo: RESUMEN_MOCK.periodo,
  items: [
    {
      id_categoria: 'VIDA-REST',
      nombre: 'Restaurantes',
      tipo_patron_gasto: 'variable_frecuente',
      color: '#D85A30',
      monto_presupuestado: 600_000,
      gasto_acumulado: 435_000,
      velocidad_actual: 29_000,
      velocidad_historica: 16_205,        // promedio de 2026-04 y 2026-05
      ratio_riesgo: 1.79,
      nivel_riesgo: 'critico',
      pct_consumido: 0.725,
      pct_esperado_hoy: 0.405,
      monto_proyectado: 870_000,
      proximo_vencimiento: null,
    },
    {
      id_categoria: 'VIDA-TRANS',
      nombre: 'Transporte',
      tipo_patron_gasto: 'variable_frecuente',
      color: '#378ADD',
      monto_presupuestado: 500_000,
      gasto_acumulado: 280_000,
      velocidad_actual: 18_667,
      velocidad_historica: 15_825,
      ratio_riesgo: 1.18,
      nivel_riesgo: 'alto',
      pct_consumido: 0.56,
      pct_esperado_hoy: 0.475,
      monto_proyectado: 560_000,
      proximo_vencimiento: null,
    },
    {
      id_categoria: 'VIDA-MKT',
      nombre: 'Mercado',
      tipo_patron_gasto: 'variable_frecuente',
      color: '#1D9E75',
      monto_presupuestado: 1_800_000,
      gasto_acumulado: 738_000,
      velocidad_actual: 49_200,
      velocidad_historica: 49_500,
      ratio_riesgo: 0.99,
      nivel_riesgo: 'ok',
      pct_consumido: 0.41,
      pct_esperado_hoy: 0.413,
      monto_proyectado: 1_476_000,
      proximo_vencimiento: null,
    },
    {
      id_categoria: 'HOGAR-ARR',
      nombre: 'Arriendo',
      tipo_patron_gasto: 'fijo_unico',
      color: '#534AB7',
      monto_presupuestado: 3_200_000,
      gasto_acumulado: 0,
      velocidad_actual: 0,
      velocidad_historica: null,
      ratio_riesgo: null,
      nivel_riesgo: 'fijo',
      pct_consumido: 0,
      pct_esperado_hoy: 0,
      monto_proyectado: 3_200_000,
      proximo_vencimiento: '2026-06-17',
    },
    {
      id_categoria: 'HOGAR-SERV',
      nombre: 'Servicios públicos',
      tipo_patron_gasto: 'fijo_recurrente',
      color: '#888780',
      monto_presupuestado: 450_000,
      gasto_acumulado: 151_000,
      velocidad_actual: 10_067,
      velocidad_historica: 11_200,
      ratio_riesgo: 0.90,
      nivel_riesgo: 'ok',
      pct_consumido: 0.336,
      pct_esperado_hoy: 0.373,
      monto_proyectado: 302_000,
      proximo_vencimiento: null,
    },
    {
      id_categoria: 'SALUD-CONS',
      nombre: 'Salud',
      tipo_patron_gasto: 'variable_esporadico',
      color: '#D4537E',
      monto_presupuestado: 450_000,
      gasto_acumulado: 90_000,
      velocidad_actual: 6_000,
      velocidad_historica: 2_500,
      ratio_riesgo: 2.4,
      nivel_riesgo: 'ok',    // esporadico: umbral más tolerante en backend
      pct_consumido: 0.20,
      pct_esperado_hoy: 0.083,
      monto_proyectado: 180_000,
      proximo_vencimiento: null,
    },
  ],
}

// ── Escenario B: SIN histórico ─────────────────────────────────────────────
// vel_hist=null → nivel_riesgo='sin_datos', sin línea punteada
// Representa el PRIMER MES de uso del sistema

export const EJECUCION_SIN_HISTORIAL = {
  periodo: RESUMEN_MOCK.periodo,
  items: [
    {
      id_categoria: 'VIDA-REST',
      nombre: 'Restaurantes',
      tipo_patron_gasto: 'variable_frecuente',
      color: '#D85A30',
      monto_presupuestado: 600_000,
      gasto_acumulado: 435_000,
      velocidad_actual: 29_000,
      velocidad_historica: null,          // ⇐ primer mes, sin datos
      ratio_riesgo: null,
      nivel_riesgo: 'sin_datos',          // ⇐ nuevo nivel
      pct_consumido: 0.725,
      pct_esperado_hoy: null,             // sin línea punteada
      monto_proyectado: 870_000,          // proyección simple (vel_actual * dias_totales)
      proximo_vencimiento: null,
    },
    {
      id_categoria: 'VIDA-TRANS',
      nombre: 'Transporte',
      tipo_patron_gasto: 'variable_frecuente',
      color: '#378ADD',
      monto_presupuestado: 500_000,
      gasto_acumulado: 280_000,
      velocidad_actual: 18_667,
      velocidad_historica: null,
      ratio_riesgo: null,
      nivel_riesgo: 'sin_datos',
      pct_consumido: 0.56,
      pct_esperado_hoy: null,
      monto_proyectado: 560_000,
      proximo_vencimiento: null,
    },
    {
      id_categoria: 'VIDA-MKT',
      nombre: 'Mercado',
      tipo_patron_gasto: 'variable_frecuente',
      color: '#1D9E75',
      monto_presupuestado: 1_800_000,
      gasto_acumulado: 738_000,
      velocidad_actual: 49_200,
      velocidad_historica: null,
      ratio_riesgo: null,
      nivel_riesgo: 'sin_datos',
      pct_consumido: 0.41,
      pct_esperado_hoy: null,
      monto_proyectado: 1_476_000,
      proximo_vencimiento: null,
    },
    {
      id_categoria: 'HOGAR-ARR',
      nombre: 'Arriendo',
      tipo_patron_gasto: 'fijo_unico',
      color: '#534AB7',
      monto_presupuestado: 3_200_000,
      gasto_acumulado: 0,
      velocidad_actual: 0,
      velocidad_historica: null,
      ratio_riesgo: null,
      nivel_riesgo: 'fijo',              // fijo siempre es fijo, sin importar el hist
      pct_consumido: 0,
      pct_esperado_hoy: null,
      monto_proyectado: 3_200_000,
      proximo_vencimiento: '2026-06-17',
    },
    {
      id_categoria: 'HOGAR-SERV',
      nombre: 'Servicios públicos',
      tipo_patron_gasto: 'fijo_recurrente',
      color: '#888780',
      monto_presupuestado: 450_000,
      gasto_acumulado: 151_000,
      velocidad_actual: 10_067,
      velocidad_historica: null,
      ratio_riesgo: null,
      nivel_riesgo: 'sin_datos',
      pct_consumido: 0.336,
      pct_esperado_hoy: null,
      monto_proyectado: 302_000,
      proximo_vencimiento: null,
    },
  ],
}

// ── Exportaciones ─────────────────────────────────────────────────────

// Backward compat: lo que antes era EJECUCION_MOCK sigue siendo con historial
export const EJECUCION_MOCK = EJECUCION_CON_HISTORIAL

export const INGRESOS_MOCK = [
  { id: 'ING-SAL',  nombre: 'Salarios',                 monto: 23_000_000, estado: 'acreditado',    fecha: '2026-05-25' },
  { id: 'ING-ACC',  nombre: 'Venta acciones IBKR',      monto: null,       estado: 'no_registrado', fecha: null },
  { id: 'ING-ARR',  nombre: 'Arriendo recibido',        monto: null,       estado: 'no_registrado', fecha: null },
  { id: 'ING-INT',  nombre: 'Intereses / rendimientos', monto: null,       estado: 'no_registrado', fecha: null },
]

export const OBLIGACIONES_MOCK = [
  { id: 'OBL-1', nombre: 'Arriendo',       fecha_vencimiento: '2026-06-17', dias_restantes: 2,  monto: 3_200_000, estado: 'pendiente'  },
  { id: 'OBL-2', nombre: 'Cuota préstamo', fecha_vencimiento: '2026-06-20', dias_restantes: 5,  monto: 1_800_000, estado: 'pagado'     },
  { id: 'OBL-3', nombre: 'Internet Claro', fecha_vencimiento: '2026-06-25', dias_restantes: 10, monto:    89_000, estado: 'por_vencer' },
  { id: 'OBL-4', nombre: 'Netflix',        fecha_vencimiento: '2026-06-28', dias_restantes: 13, monto:    45_000, estado: 'por_vencer' },
]

// -- Mocks para el Home v1 (variante D) --------------------------------

export const INBOX_STATS_MOCK = {
  pendientes: 7,
  alta_prioridad: 2,
  confirmados_hoy: 3,
  pendientes_sms: 3,
}

export const HOME_CONFIG_MOCK = {
  insight_visible: true,
  patrimonio_visible: true,
  ask_visible: true,
}

export const TRANSACCIONES_RECIENTES_MOCK = {
  items: [
    { id: 'TX-1', fecha: '2026-06-15', tipo: 'gasto', descripcion: 'Éxito Calle 80',
      estado: 'confirmado', id_categoria: 'VIDA-MKT', id_contraparte: 'CP-EXITO',
      quien_pago: 'GHR', notas: '', monto: 142_300, moneda: 'COP',
      tramos: [{ id_cuenta_origen: 'CTA-BC-DEB' }] },
    { id: 'TX-2', fecha: '2026-06-14', tipo: 'gasto', descripcion: 'Rappi',
      estado: 'pendiente', id_categoria: 'VIDA-REST', id_contraparte: 'CP-RAPPI',
      quien_pago: 'MC', notas: '', monto: 68_500, moneda: 'COP',
      tramos: [{ id_cuenta_origen: 'CTA-NEQUI' }] },
    { id: 'TX-3', fecha: '2026-06-14', tipo: 'gasto', descripcion: 'Uber',
      estado: 'confirmado', id_categoria: 'VIDA-TRANS', id_contraparte: 'CP-UBER',
      quien_pago: 'GHR', notas: '', monto: 23_400, moneda: 'COP',
      tramos: [{ id_cuenta_origen: 'CTA-BC-CRED' }] },
    { id: 'TX-4', fecha: '2026-06-13', tipo: 'gasto', descripcion: 'Netflix',
      estado: 'confirmado', id_categoria: 'HOGAR-SERV', id_contraparte: 'CP-NETFLIX',
      quien_pago: 'Unknown', notas: '', monto: 45_000, moneda: 'COP',
      tramos: [{ id_cuenta_origen: 'CTA-BC-CRED' }] },
    { id: 'TX-5', fecha: '2026-06-12', tipo: 'gasto', descripcion: 'Farmatodo',
      estado: 'confirmado', id_categoria: 'SALUD-CONS', id_contraparte: 'CP-FARMATODO',
      quien_pago: 'MC', notas: '', monto: 90_000, moneda: 'COP',
      tramos: [{ id_cuenta_origen: 'CTA-NEQUI' }] },
  ],
  next_cursor: null,
  total: 5,
}

export const PATRIMONIO_MOCK = {
  fecha: null,
  activos_total: 238_500_000,
  deudas_total: 34_200_000,
  patrimonio_neto: 204_300_000,
  detalle_activos: [
    { id: 'INV-AH', nombre: 'Ahorros Bancolombia', tipo: 'AHORRO', valor: 42_000_000 },
    { id: 'INV-CDT', nombre: 'CDT Davivienda',      tipo: 'AHORRO', valor: 60_000_000 },
    { id: 'INV-IBKR', nombre: 'IBKR (acciones)',     tipo: 'ACCIONES', valor: 136_500_000 },
  ],
  detalle_deudas: [
    { id: 'OBL-HIP', nombre: 'Crédito hipotecario',  saldo_pendiente: 28_000_000 },
    { id: 'OBL-TC',  nombre: 'Tarjeta Bancolombia',  saldo_pendiente: 6_200_000 },
  ],
}

export const PATRIMONIO_HISTORICO_MOCK = {
  meses: 6,
  puntos: [
    { anio: 2026, mes: 1, activos_total: 226_000_000, deudas_total: 37_000_000 },
    { anio: 2026, mes: 2, activos_total: 229_000_000, deudas_total: 36_400_000 },
    { anio: 2026, mes: 3, activos_total: 232_000_000, deudas_total: 35_800_000 },
    { anio: 2026, mes: 4, activos_total: 234_500_000, deudas_total: 35_200_000 },
    { anio: 2026, mes: 5, activos_total: 236_800_000, deudas_total: 34_700_000 },
    { anio: 2026, mes: 6, activos_total: 238_500_000, deudas_total: 34_200_000 },
  ],
}

// Subcategorias por categoria padre -- mismo shape que items de ejecucion,
// para el drill-down del widget "Presupuesto por categoria".
export const SUBCATEGORIAS_MOCK = {
  'VIDA-REST': {
    id_padre: 'VIDA-REST',
    items: [
      { id_categoria: 'VIDA-REST-DOM', nombre: 'Domicilios', tipo_patron_gasto: 'variable_frecuente',
        monto_presupuestado: 350_000, gasto_acumulado: 260_000, nivel_riesgo: 'ok', pct_consumido: 0.743,
        ratio_riesgo: null, velocidad_actual: null, velocidad_historica: null, pct_esperado_hoy: null,
        monto_proyectado: 260_000, proximo_vencimiento: null },
      { id_categoria: 'VIDA-REST-OUT', nombre: 'Cenas afuera', tipo_patron_gasto: 'variable_frecuente',
        monto_presupuestado: 200_000, gasto_acumulado: 135_000, nivel_riesgo: 'ok', pct_consumido: 0.675,
        ratio_riesgo: null, velocidad_actual: null, velocidad_historica: null, pct_esperado_hoy: null,
        monto_proyectado: 135_000, proximo_vencimiento: null },
      { id_categoria: 'VIDA-REST-CAFE', nombre: 'Cafés', tipo_patron_gasto: 'variable_frecuente',
        monto_presupuestado: 50_000, gasto_acumulado: 40_000, nivel_riesgo: 'ok', pct_consumido: 0.8,
        ratio_riesgo: null, velocidad_actual: null, velocidad_historica: null, pct_esperado_hoy: null,
        monto_proyectado: 40_000, proximo_vencimiento: null },
    ],
  },
  'VIDA-TRANS': {
    id_padre: 'VIDA-TRANS',
    items: [
      { id_categoria: 'VIDA-TRANS-APP', nombre: 'Apps (Uber/Didi)', tipo_patron_gasto: 'variable_frecuente',
        monto_presupuestado: 320_000, gasto_acumulado: 190_000, nivel_riesgo: 'ok', pct_consumido: 0.594,
        ratio_riesgo: null, velocidad_actual: null, velocidad_historica: null, pct_esperado_hoy: null,
        monto_proyectado: 190_000, proximo_vencimiento: null },
      { id_categoria: 'VIDA-TRANS-COMB', nombre: 'Combustible', tipo_patron_gasto: 'variable_frecuente',
        monto_presupuestado: 180_000, gasto_acumulado: 90_000, nivel_riesgo: 'ok', pct_consumido: 0.5,
        ratio_riesgo: null, velocidad_actual: null, velocidad_historica: null, pct_esperado_hoy: null,
        monto_proyectado: 90_000, proximo_vencimiento: null },
    ],
  },
}
