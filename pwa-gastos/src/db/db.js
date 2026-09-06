import Dexie from 'dexie'

// Sin campo de estado: la sola presencia de un registro en gastosPendientes
// significa "pendiente de subir". Se borra apenas la subida tiene exito.
export const db = new Dexie('gastos-mcghr')

db.version(1).stores({
  gastosPendientes: '++localId, id, fecha',
  catalogosCache: 'key',
})

// Tabla de diagnostico para errores de autenticacion MSAL (sesion de
// OneDrive que se corta a las pocas horas) -- ver src/utils/authLog.js.
db.version(2).stores({
  gastosPendientes: '++localId, id, fecha',
  catalogosCache: 'key',
  logSync: '++id, timestamp, errorCode',
})

// Reemplaza el uso activo de gastosPendientes (que queda deprecada, no se
// borra todavia): "gastos" guarda TODOS los gastos, no solo los pendientes
// de subir -- un registro sincronizado se actualiza a estado='sincronizado'
// en vez de borrarse, y solo se purga si tiene mas de 7 dias Y esta
// sincronizado (nunca si esta en 'pendiente' o 'error'). Ver utils/sync.js
// y modules/Actividad.
db.version(3).stores({
  gastosPendientes: '++localId, id, fecha',
  catalogosCache: 'key',
  logSync: '++id, timestamp, errorCode',
  gastos: '++localId, id, fecha, estado',
})

export default db
