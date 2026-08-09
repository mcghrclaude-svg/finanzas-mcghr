import Dexie from 'dexie'

// Sin campo de estado: la sola presencia de un registro en gastosPendientes
// significa "pendiente de subir". Se borra apenas la subida tiene exito.
export const db = new Dexie('gastos-mcghr')

db.version(1).stores({
  gastosPendientes: '++localId, id, fecha',
  catalogosCache: 'key',
})

export default db
