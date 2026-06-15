/**
 * Hook para operaciones con soporte Undo/Redo.
 * Wrapper sobre useAppStore que simplifica el registro de acciones.
 *
 * Uso:
 *   const { ejecutar } = useUndo()
 *   ejecutar({
 *     descripcion: 'Cambiar categoría a Alimentación',
 *     accion: () => api.editar(id, { categoria: 'ALI' }),
 *     deshacer: () => api.editar(id, { categoria: categoriaAnterior }),
 *     rehacer: () => api.editar(id, { categoria: 'ALI' }),
 *   })
 */

import useAppStore from '@/store/useAppStore'

export function useUndo() {
  const pushUndo = useAppStore(s => s.pushUndo)
  const marcarCambio = useAppStore(s => s.marcarCambio)

  const ejecutar = async ({ descripcion, accion, deshacer, rehacer }) => {
    await accion()
    pushUndo({ descripcion, deshacer, rehacer: rehacer ?? accion })
    marcarCambio()
  }

  return { ejecutar }
}
