/**
 * Store global Zustand.
 * Principio: estado mínimo aquí. Los datos del servidor viven en React Query.
 * Este store contiene únicamente:
 *   - UI state (sidebar abierto, tema)
 *   - Undo/Redo stack (por sesión, no persiste)
 *   - Cambios no guardados (para AlertaSinGuardar)
 */

import { create } from 'zustand'

const useAppStore = create((set, get) => ({
  // — UI -----------------------------------------------------------------------
  sidebarOpen: true,
  toggleSidebar: () => set(s => ({ sidebarOpen: !s.sidebarOpen })),

  // — Undo / Redo (estilo Office) -----------------------------------------------
  // Cada entrada: { descripcion: str, deshacer: fn, rehacer: fn }
  undoStack: [],
  redoStack: [],

  pushUndo: (accion) => set(s => ({
    undoStack: [...s.undoStack, accion],
    redoStack: [],  // al hacer algo nuevo, se pierde el redo
  })),

  undo: () => {
    const { undoStack, redoStack } = get()
    if (!undoStack.length) return
    const accion = undoStack[undoStack.length - 1]
    accion.deshacer()
    set({
      undoStack: undoStack.slice(0, -1),
      redoStack: [...redoStack, accion],
    })
  },

  redo: () => {
    const { undoStack, redoStack } = get()
    if (!redoStack.length) return
    const accion = redoStack[redoStack.length - 1]
    accion.rehacer()
    set({
      undoStack: [...undoStack, accion],
      redoStack: redoStack.slice(0, -1),
    })
  },

  clearUndoStack: () => set({ undoStack: [], redoStack: [] }),

  // — Cambios no guardados -------------------------------------------------------
  // Se limpia al hacer Save. Dispara alerta si el usuario intenta cerrar la pestaña
  // (AlertaSinGuardar) o navegar a otra pantalla del menu (GuardiaNavegacion).
  hayCambiosSinGuardar: false,
  marcarCambio: () => set({ hayCambiosSinGuardar: true }),
  limpiarCambios: () => set({ hayCambiosSinGuardar: false }),

  // Funcion "grabar lo pendiente" de la pantalla actual con cambios sin
  // guardar -- la registra ella misma al montarse. GuardiaNavegacion la usa
  // para poder ofrecer "Grabar y salir" sin saber nada de la pantalla en si.
  guardarPendientesFn: null,
  registrarGuardadoPendiente: (fn) => set({ guardarPendientesFn: fn }),

  // Ruta a la que se intento navegar mientras habia cambios sin guardar.
  // No-null dispara el modal de GuardiaNavegacion.
  destinoPendiente: null,
  solicitarConfirmacionSalida: (to) => set({ destinoPendiente: to }),
  cancelarConfirmacionSalida: () => set({ destinoPendiente: null }),
}))

export default useAppStore
