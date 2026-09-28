/**
 * Datos mock del Home -- todo en mes calendario (mismo criterio que la PWA
 * y que /presupuestos/resumen-por-categoria en el backend real).
 */

export const RESUMEN_MOCK = {
  periodo: {
    id: null,
    fecha_inicio: '2026-06-01',
    fecha_fin_tentativa: '2026-06-30',
    fecha_fin_real: null,
    estado: 'mes_calendario',
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

export const INGRESOS_MOCK = [
  { id: 'ING-SAL',  nombre: 'Salarios',                 monto: 23_000_000, estado: 'acreditado',    fecha: '2026-06-01' },
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

// Resumen por categoria (mes calendario, todas las categorias con o sin
// presupuesto, lista plana con nivel/id_padre) -- fuente compartida de
// "Presupuesto por categoria" y "Gasto por categoria" (torta): ambos widgets
// hacen drill-down local sobre esta misma lista, sin ida y vuelta al backend.
export const RESUMEN_CATEGORIAS_MOCK = [
  { id_categoria: 'VIDA-REST',  nivel: 1, id_padre: null, nombre: 'Restaurantes',        gasto_acumulado: 435_000, presupuesto: 600_000 },
  { id_categoria: 'VIDA-TRANS', nivel: 1, id_padre: null, nombre: 'Transporte',          gasto_acumulado: 280_000, presupuesto: 500_000 },
  { id_categoria: 'VIDA-MKT',   nivel: 1, id_padre: null, nombre: 'Mercado',             gasto_acumulado: 738_000, presupuesto: 1_800_000 },
  { id_categoria: 'HOGAR-ARR',  nivel: 1, id_padre: null, nombre: 'Arriendo',            gasto_acumulado: 0,       presupuesto: 3_200_000 },
  { id_categoria: 'HOGAR-SERV', nivel: 1, id_padre: null, nombre: 'Servicios públicos',  gasto_acumulado: 151_000, presupuesto: 450_000 },
  { id_categoria: 'SALUD-CONS', nivel: 1, id_padre: null, nombre: 'Salud',               gasto_acumulado: 90_000,  presupuesto: 450_000 },

  { id_categoria: 'VIDA-REST-DOM',  nivel: 2, id_padre: 'VIDA-REST',  nombre: 'Domicilios',        gasto_acumulado: 260_000, presupuesto: 350_000 },
  { id_categoria: 'VIDA-REST-OUT',  nivel: 2, id_padre: 'VIDA-REST',  nombre: 'Cenas afuera',       gasto_acumulado: 135_000, presupuesto: 200_000 },
  { id_categoria: 'VIDA-REST-CAFE', nivel: 2, id_padre: 'VIDA-REST',  nombre: 'Cafés',              gasto_acumulado: 40_000,  presupuesto: 50_000 },
  { id_categoria: 'VIDA-TRANS-APP', nivel: 2, id_padre: 'VIDA-TRANS', nombre: 'Apps (Uber/Didi)',   gasto_acumulado: 190_000, presupuesto: 320_000 },
  { id_categoria: 'VIDA-TRANS-COMB',nivel: 2, id_padre: 'VIDA-TRANS', nombre: 'Combustible',        gasto_acumulado: 90_000,  presupuesto: 180_000 },
]
