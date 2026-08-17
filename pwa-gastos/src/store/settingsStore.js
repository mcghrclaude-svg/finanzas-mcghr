import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Config del dispositivo: folder ID de la carpeta raiz + usuario default.
// Son pocos valores simples -- localStorage via zustand/persist alcanza,
// no hace falta una tabla de Dexie para esto.
//
// Hasta la version anterior habia 3 carpetas separadas (carpetaGastos,
// carpetaCatalogos, carpetaResumen); ahora es una sola carpetaRaiz de la
// que se derivan pendientes/, procesados/, Catalogos/ y Resumen/ (ver
// ADR-018). `configuracionMigradaDesdeVieja` se activa via `migrate` cuando
// se detecta un localStorage con el shape viejo y ninguna carpetaRaiz
// todavia -- dispara el aviso de re-configuracion en Configuracion, y se
// apaga solo apenas el usuario elige la raiz nueva.
export const useSettingsStore = create(
  persist(
    (set) => ({
      carpetaRaiz: null, // { driveId, itemId, nombre }
      usuarioDispositivo: 'GHR', // 'GHR' | 'MC'
      monedaDefault: null, // id del catalogo, o null si no se configuro
      medioPagoDefault: null, // id del catalogo, o null si no se configuro
      configuracionMigradaDesdeVieja: false,

      setCarpetaRaiz: (carpeta) => set({ carpetaRaiz: carpeta, configuracionMigradaDesdeVieja: false }),
      setUsuarioDispositivo: (usuario) => set({ usuarioDispositivo: usuario }),
      setMonedaDefault: (id) => set({ monedaDefault: id }),
      setMedioPagoDefault: (id) => set({ medioPagoDefault: id }),
    }),
    {
      name: 'pwa-gastos:settings',
      version: 1,
      migrate: (persisted, version) => {
        if (version === 0) {
          const { carpetaGastos, carpetaCatalogos, carpetaResumen, ...resto } = persisted || {}
          return {
            ...resto,
            carpetaRaiz: null,
            configuracionMigradaDesdeVieja: Boolean(carpetaGastos || carpetaCatalogos || carpetaResumen),
          }
        }
        return persisted
      },
    }
  )
)
