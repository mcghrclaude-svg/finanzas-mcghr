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

export default db
