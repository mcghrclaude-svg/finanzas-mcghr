import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Config del dispositivo: folder IDs de las 3 carpetas + usuario default.
// Son pocos valores simples -- localStorage via zustand/persist alcanza,
// no hace falta una tabla de Dexie para esto.
export const useSettingsStore = create(
  persist(
    (set) => ({
      carpetaGastos: null, // { driveId, itemId, nombre }
      carpetaCatalogos: null,
      carpetaResumen: null,
      usuarioDispositivo: 'GHR', // 'GHR' | 'MC'
      monedaDefault: null, // id del catalogo, o null si no se configuro
      medioPagoDefault: null, // id del catalogo, o null si no se configuro

      setCarpetaGastos: (carpeta) => set({ carpetaGastos: carpeta }),
      setCarpetaCatalogos: (carpeta) => set({ carpetaCatalogos: carpeta }),
      setCarpetaResumen: (carpeta) => set({ carpetaResumen: carpeta }),
      setUsuarioDispositivo: (usuario) => set({ usuarioDispositivo: usuario }),
      setMonedaDefault: (id) => set({ monedaDefault: id }),
      setMedioPagoDefault: (id) => set({ medioPagoDefault: id }),
    }),
    { name: 'pwa-gastos:settings' }
  )
)
