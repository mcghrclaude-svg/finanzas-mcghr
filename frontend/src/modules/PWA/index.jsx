/**
 * modules/PWA/index.jsx
 * Configuracion de la importacion automatica de gastos de la PWA mobile:
 * intervalo, on/off (Tarea Programada de Windows), carpetas de OneDrive,
 * carpeta de catalogos, carpeta de resumen mensual (a futuro), e historial
 * de corridas con errores.
 */
import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import { pwaConfigApi } from '@/api/pwaConfig'
import FolderPickerModal from '@/components/shared/FolderPickerModal'
import FolderPickerField from '@/components/shared/FolderPickerField'

// Punto de partida comodo para un picker nuevo: cualquier carpeta ya
// guardada en los tres campos, en vez de arrancar siempre desde las
// unidades de disco.
function ultimoPathConocido(config) {
  return (
    config.carpetas_gastos?.[config.carpetas_gastos.length - 1] ??
    config.carpeta_catalogos ??
    config.carpeta_resumen_mensual ??
    undefined
  )
}

function fmtFecha(iso) {
  if (!iso) return '-'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function CarpetasList({ carpetas, onChange, initialPath }) {
  const [pickerAbierto, setPickerAbierto] = useState(false)

  function agregar(ruta) {
    setPickerAbierto(false)
    if (!ruta || carpetas.includes(ruta)) return
    onChange([...carpetas, ruta])
  }

  function quitar(idx) {
    onChange(carpetas.filter((_, i) => i !== idx))
  }

  return (
    <div className="space-y-2">
      {carpetas.length === 0 && (
        <p className="text-sm text-gray-400 italic">No expense folders configured yet.</p>
      )}
      {carpetas.map((c, idx) => (
        <div key={c} className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
          <code className="text-xs text-gray-700 flex-1 truncate">{c}</code>
          <button
            onClick={() => quitar(idx)}
            className="p-1 rounded text-gray-400 hover:text-danger-500 hover:bg-danger-100 text-sm"
            title="Remove"
          >🗑️</button>
        </div>
      ))}
      <button
        onClick={() => setPickerAbierto(true)}
        className="px-3 py-2 text-sm font-medium text-primary-700 border border-primary-200 rounded-lg hover:bg-primary-50"
      >
        + Add folder
      </button>

      {pickerAbierto && (
        <FolderPickerModal
          initialPath={initialPath}
          onPick={agregar}
          onCancel={() => setPickerAbierto(false)}
        />
      )}
    </div>
  )
}

function HistorialTable({ items }) {
  if (!items?.length) return (
    <div className="flex flex-col items-center justify-center py-16 text-gray-400 gap-2">
      <p className="text-sm font-medium text-gray-600">No runs yet</p>
    </div>
  )

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <table className="w-full">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            {['Started', 'Finished', 'Read', 'New', 'Duplicates', 'Errors', 'Notes'].map(h => (
              <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {items.map(row => (
            <tr key={row.id} className={row.errores > 0 ? 'bg-danger-50/40' : ''}>
              <td className="px-4 py-2.5 text-sm text-gray-700">{fmtFecha(row.fecha_inicio)}</td>
              <td className="px-4 py-2.5 text-sm text-gray-500">{row.fecha_fin ? fmtFecha(row.fecha_fin) : (
                <span className="text-amber-600">unfinished</span>
              )}</td>
              <td className="px-4 py-2.5 text-sm text-gray-700">{row.archivos_leidos}</td>
              <td className="px-4 py-2.5 text-sm text-success-600 font-medium">{row.transacciones_nuevas}</td>
              <td className="px-4 py-2.5 text-sm text-gray-500">{row.duplicados}</td>
              <td className="px-4 py-2.5 text-sm">
                {row.errores > 0
                  ? <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-danger-100 text-danger-600">{row.errores}</span>
                  : <span className="text-gray-400">0</span>}
              </td>
              <td className="px-4 py-2.5 text-xs text-gray-500 max-w-xs">
                <p className="truncate" title={row.notas}>{row.notas}</p>
                {row.alertas?.errores?.length > 0 && (
                  <ul className="mt-1 space-y-0.5">
                    {row.alertas.errores.slice(0, 3).map((e, i) => (
                      <li key={i} className="text-danger-600 truncate" title={`${e.archivo}: ${e.motivo}`}>
                        {e.archivo ? `${e.archivo}: ` : ''}{e.motivo}
                      </li>
                    ))}
                  </ul>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function PWA() {
  const [config, setConfig] = useState(null)
  const [historial, setHistorial] = useState([])
  const [loading, setLoading] = useState(true)
  const [guardando, setGuardando] = useState(false)
  const [toggling, setToggling] = useState(false)

  const cargar = useCallback(async () => {
    setLoading(true)
    try {
      const [cfg, hist] = await Promise.all([
        pwaConfigApi.obtener(),
        pwaConfigApi.historial(20),
      ])
      setConfig(cfg)
      setHistorial(hist.items ?? [])
    } catch (e) {
      toast.error('Error loading PWA config: ' + e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { cargar() }, [cargar])

  async function guardar() {
    setGuardando(true)
    try {
      const actualizado = await pwaConfigApi.actualizar({
        intervalo_minutos: Number(config.intervalo_minutos),
        carpetas_gastos: config.carpetas_gastos,
        carpeta_catalogos: config.carpeta_catalogos,
        carpeta_resumen_mensual: config.carpeta_resumen_mensual,
      })
      setConfig(actualizado)
      toast.success('Configuration saved')
    } catch (e) {
      toast.error(e.message)
    } finally {
      setGuardando(false)
    }
  }

  async function toggle() {
    setToggling(true)
    try {
      await pwaConfigApi.toggle(!config.tarea_habilitada)
      const cfg = await pwaConfigApi.obtener()
      setConfig(cfg)
      toast.success(cfg.tarea_habilitada ? 'Scheduled task enabled' : 'Scheduled task paused')
    } catch (e) {
      toast.error(e.message)
    } finally {
      setToggling(false)
    }
  }

  if (loading || !config) return (
    <div className="flex items-center justify-center py-20 text-gray-400 text-sm gap-2">
      <span className="animate-spin">⏳</span> Loading...
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">📲 PWA Import</h1>
          <p className="text-sm text-gray-500 mt-0.5">Automatic import of mobile-captured expenses</p>
        </div>
        <button
          onClick={toggle}
          disabled={toggling}
          className={`inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors disabled:opacity-50 ${
            config.tarea_habilitada
              ? 'bg-success-100 text-success-600 hover:bg-success-100/80'
              : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
          }`}
        >
          <span className={`w-2 h-2 rounded-full ${config.tarea_habilitada ? 'bg-success-500' : 'bg-gray-400'}`} />
          {config.tarea_habilitada ? 'Enabled' : 'Disabled'}
        </button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Scheduled Task</p>
          <p className="text-sm font-medium text-gray-900">{config.tarea_existe ? 'Registered' : 'Not created yet'}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Next Run</p>
          <p className="text-sm font-medium text-gray-900">{config.proxima_ejecucion ?? '-'}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Last Result</p>
          <p className="text-sm font-medium text-gray-900">{config.ultimo_resultado_tarea ?? '-'}</p>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-5">
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
            Run interval (minutes)
          </label>
          <input
            type="number"
            min="1"
            value={config.intervalo_minutos}
            onChange={e => setConfig({ ...config, intervalo_minutos: e.target.value })}
            className="w-40 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
            Expense folders (parents of pendientes/ and procesados/)
          </label>
          <CarpetasList
            carpetas={config.carpetas_gastos}
            onChange={v => setConfig({ ...config, carpetas_gastos: v })}
            initialPath={ultimoPathConocido(config)}
          />
        </div>

        <FolderPickerField
          label="Catalogs folder (where catalogos.json is written)"
          value={config.carpeta_catalogos}
          onChange={v => setConfig({ ...config, carpeta_catalogos: v })}
          initialPath={ultimoPathConocido(config)}
        />

        <FolderPickerField
          label={<>Monthly summary folder <span className="normal-case text-gray-400">(field only — generation not implemented yet)</span></>}
          value={config.carpeta_resumen_mensual}
          onChange={v => setConfig({ ...config, carpeta_resumen_mensual: v })}
          initialPath={ultimoPathConocido(config)}
        />

        <div className="flex justify-end pt-2 border-t border-gray-100">
          <button
            onClick={guardar}
            disabled={guardando}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
          >
            {guardando ? 'Saving...' : 'Save configuration'}
          </button>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-semibold text-gray-700">Run history</h2>
          <button onClick={cargar} className="px-3 py-1.5 text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50">
            ↻ Refresh
          </button>
        </div>
        <HistorialTable items={historial} />
      </div>
    </div>
  )
}
