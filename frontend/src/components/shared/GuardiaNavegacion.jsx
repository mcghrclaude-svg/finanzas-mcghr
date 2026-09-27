/**
 * GuardiaNavegacion.jsx — modal "cambios sin grabar" al intentar navegar a
 * otra pantalla del menu. Se monta una sola vez en Layout, igual que
 * AlertaSinGuardar (que cubre el cierre de la pestana) y UndoBar.
 *
 * Los links del Sidebar, al clickearse con hayCambiosSinGuardar=true, hacen
 * preventDefault() y llaman a solicitarConfirmacionSalida(to) en vez de
 * navegar directo -- este componente es el unico que sabe navegar de verdad
 * una vez que el usuario responde.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useAppStore from '@/store/useAppStore'

export default function GuardiaNavegacion() {
  const navigate = useNavigate()
  const destinoPendiente = useAppStore(s => s.destinoPendiente)
  const cancelarConfirmacionSalida = useAppStore(s => s.cancelarConfirmacionSalida)
  const limpiarCambios = useAppStore(s => s.limpiarCambios)
  const guardarPendientesFn = useAppStore(s => s.guardarPendientesFn)
  const [guardando, setGuardando] = useState(false)

  if (!destinoPendiente) return null

  function salirSinGrabar() {
    limpiarCambios()
    cancelarConfirmacionSalida()
    navigate(destinoPendiente)
  }

  async function grabarYSalir() {
    setGuardando(true)
    try {
      if (guardarPendientesFn) await guardarPendientesFn()
      limpiarCambios()
      cancelarConfirmacionSalida()
      navigate(destinoPendiente)
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
      onClick={e => e.target === e.currentTarget && cancelarConfirmacionSalida()}
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm">
        <div className="px-6 pt-5 pb-2">
          <h2 className="text-base font-semibold text-gray-900">Cambios sin grabar</h2>
        </div>
        <div className="px-6 py-4">
          <p className="text-sm text-gray-700">
            Tenés cambios sin grabar en esta pantalla. ¿Querés grabarlos antes de salir?
          </p>
        </div>
        <div className="flex justify-end gap-2 px-6 pb-5">
          <button
            onClick={salirSinGrabar}
            disabled={guardando}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Salir sin grabar
          </button>
          <button
            onClick={grabarYSalir}
            disabled={guardando}
            className="px-4 py-2 text-sm font-medium text-white rounded-lg bg-primary-600 hover:bg-primary-700 disabled:opacity-50 transition-colors"
          >
            {guardando ? 'Grabando...' : 'Grabar y salir'}
          </button>
        </div>
      </div>
    </div>
  )
}
