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
