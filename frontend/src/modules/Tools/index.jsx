/**
 * modules/Tools/index.jsx
 * Herramientas de administracion del entorno de desarrollo.
 * Solo visible cuando VITE_ENV === 'dev'.
 */
import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import client from '@/api/client'
import ConfirmDialog from '@/components/shared/ConfirmDialog'

// -- API ---------------------------------------------------------------
const api = {
  resetParcial:    () => client.post('/tools/reset-parcial').then(r => r.data),
  resetTotal:      () => client.post('/tools/reset-total').then(r => r.data),
  backup:          (carpeta) => client.post('/tools/backup', { carpeta }).then(r => r.data),
  snapshots:       () => client.get('/tools/snapshots').then(r => r.data),
  restore:         (nombre_archivo) => client.post('/tools/restore', { nombre_archivo }).then(r => r.data),
  logEjecuciones:  (p) => client.get('/tools/log-ejecuciones', { params: p }).then(r => r.data),
  seed:            (p) => client.post('/tools/seed', p).then(r => r.data),
}

// -- Card colapsable ---------------------------------------------------
function Card({ title, icon, children }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="bg-white border rounded-xl overflow-hidden border-gray-200">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 text-left bg-gray-50 border-b border-gray-100"
      >
        <span className="flex items-center gap-2 text-sm font-semibold text-gray-800">
          <span>{icon}</span> {title}
        </span>
        <span className="text-xs text-gray-400">{open ? '▲' : '▼'}</span>
      </button>
      {open && <div className="px-4 py-4">{children}</div>}
    </div>
  )
}

// -- Boton de accion ---------------------------------------------------
function Btn({ onClick, disabled, danger = false, children }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors disabled:opacity-50 ${
        danger
          ? 'bg-red-600 text-white hover:bg-red-700'
          : 'bg-primary-600 text-white hover:bg-primary-700'
      }`}
    >
      {children}
    </button>
  )
}

// -- ResultBox ---------------------------------------------------------
function ResultBox({ result }) {
  if (!result) return null
  return (
    <pre className="mt-3 text-xs bg-gray-900 text-green-400 rounded-lg p-3 overflow-auto max-h-40 whitespace-pre-wrap">
      {JSON.stringify(result, null, 2)}
    </pre>
  )
}

// -- Secciones ---------------------------------------------------------

function ResetParcial() {
  const [confirm, setConfirm] = useState(false)
  const [running, setRunning] = useState(false)
  const [result,  setResult]  = useState(null)

  async function ejecutar() {
    setRunning(true); setConfirm(false)
    try {
      const r = await api.resetParcial()
      setResult(r)
      toast.success('Reset parcial completado')
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    } finally {
      setRunning(false)
    }
  }

  return (
    <Card title="Reset Parcial" icon="🗑">
      <p className="text-xs text-gray-500 mb-3">
        Vacia tablas ETL (transacciones, tramos, vinculos, documentos, inbox, correos,
        entidades_potenciales, log_ejecuciones). Preserva catalogo.
      </p>
      <Btn danger onClick={() => setConfirm(true)} disabled={running}>
        {running ? 'Ejecutando...' : 'Execute'}
      </Btn>
      <ResultBox result={result} />
      <ConfirmDialog
        open={confirm}
        titulo="Reset Parcial"
        mensaje="Se borraran todas las transacciones y datos ETL. El catalogo se preserva. Esta accion no se puede deshacer."
        onConfirm={ejecutar}
        onCancel={() => setConfirm(false)}
        peligroso
      />
    </Card>
  )
}

function ResetTotal() {
  const [confirm, setConfirm] = useState(false)
  const [running, setRunning] = useState(false)
  const [result,  setResult]  = useState(null)
  const [texto,   setTexto]   = useState('')

  async function ejecutar() {
    setRunning(true); setConfirm(false); setTexto('')
    try {
      const r = await api.resetTotal()
      setResult(r)
      toast.success('Reset total completado')
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    } finally {
      setRunning(false)
    }
  }

  return (
    <Card title="Reset Total" icon="☢">
      <p className="text-xs text-gray-500 mb-3">
        Vacia ETL + catalogo (categorias, cuentas, contrapartes, personas, inversiones,
        obligaciones, presupuestos). Preserva reglas_clasificacion y periodos_financieros.
      </p>
      <div className="flex gap-2 items-center mb-1">
        <input
          type="text"
          value={texto}
          onChange={e => setTexto(e.target.value)}
          placeholder='Escriba RESET para habilitar'
          className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 w-56 focus:outline-none focus:border-red-400"
        />
        <Btn danger onClick={() => setConfirm(true)} disabled={running || texto !== 'RESET'}>
          {running ? 'Ejecutando...' : 'Execute'}
        </Btn>
      </div>
      <ResultBox result={result} />
      <ConfirmDialog
        open={confirm}
        titulo="Reset Total -- accion irreversible"
        mensaje="Se borraran TODOS los datos incluyendo el catalogo. Esta accion no se puede deshacer."
        onConfirm={ejecutar}
        onCancel={() => setConfirm(false)}
        peligroso
      />
    </Card>
  )
}

function BackupSection() {
  const [carpeta,  setCarpeta]  = useState('')
  const [running,  setRunning]  = useState(false)
  const [result,   setResult]   = useState(null)

  async function ejecutar() {
    setRunning(true)
    try {
      const r = await api.backup(carpeta)
      setResult(r)
      toast.success(`Backup: ${r.nombre_archivo}`)
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    } finally {
      setRunning(false)
    }
  }

  return (
    <Card title="Backup" icon="💾">
      <p className="text-xs text-gray-500 mb-3">
        Copia finanzas_dev.db a la carpeta de snapshots con timestamp.
        Dejar vacio usa data/dev/snapshots/.
      </p>
      <div className="flex gap-2 mb-1">
        <input
          type="text"
          value={carpeta}
          onChange={e => setCarpeta(e.target.value)}
          placeholder="data/dev/snapshots/ (default)"
          className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 flex-1 focus:outline-none focus:border-primary-400"
        />
        <Btn onClick={ejecutar} disabled={running}>
          {running ? 'Copiando...' : 'Execute'}
        </Btn>
      </div>
      <ResultBox result={result} />
    </Card>
  )
}

function RestoreSection() {
  const [snapshots, setSnapshots] = useState([])
  const [selected,  setSelected]  = useState('')
  const [confirm,   setConfirm]   = useState(false)
  const [running,   setRunning]   = useState(false)
  const [result,    setResult]    = useState(null)

  useEffect(() => {
    api.snapshots().then(d => {
      setSnapshots(d.items ?? [])
      if (d.items?.length > 0) setSelected(d.items[0].nombre)
    }).catch(() => {})
  }, [])

  async function ejecutar() {
    setRunning(true); setConfirm(false)
    try {
      const r = await api.restore(selected)
      setResult(r)
      toast.success(`Restaurado desde ${selected}`)
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    } finally {
      setRunning(false)
    }
  }

  return (
    <Card title="Restore" icon="📂">
      <p className="text-xs text-gray-500 mb-3">
        Reemplaza finanzas_dev.db con el snapshot seleccionado.
        La conexion se cierra y reabre automaticamente.
      </p>
      {snapshots.length === 0 ? (
        <p className="text-xs text-gray-400 italic mb-2">Sin snapshots disponibles. Crea un backup primero.</p>
      ) : (
        <div className="flex gap-2 mb-1">
          <select
            value={selected}
            onChange={e => setSelected(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 flex-1 bg-white focus:outline-none focus:border-primary-400"
          >
            {snapshots.map(s => (
              <option key={s.nombre} value={s.nombre}>
                {s.nombre} ({s.tamano_kb} KB — {s.creado_en})
              </option>
            ))}
          </select>
          <Btn danger onClick={() => setConfirm(true)} disabled={running || !selected}>
            {running ? 'Restaurando...' : 'Restore'}
          </Btn>
        </div>
      )}
      <ResultBox result={result} />
      <ConfirmDialog
        open={confirm}
        titulo="Restaurar snapshot"
        mensaje={`Se reemplazara la DB actual con "${selected}". Todos los cambios posteriores al snapshot se perderan.`}
        onConfirm={ejecutar}
        onCancel={() => setConfirm(false)}
        peligroso
      />
    </Card>
  )
}

function LogEjecuciones() {
  const [desde,   setDesde]   = useState('')
  const [hasta,   setHasta]   = useState('')
  const [items,   setItems]   = useState([])
  const [loading, setLoading] = useState(false)

  async function cargar() {
    setLoading(true)
    try {
      const r = await api.logEjecuciones({ desde, hasta, limit: 50 })
      setItems(r.items ?? [])
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargar() }, [])

  return (
    <Card title="Log de Corridas ETL" icon="📋">
      <div className="flex items-center gap-2 mb-3">
        <input type="date" value={desde} onChange={e => setDesde(e.target.value)}
          className="text-xs border border-gray-200 rounded px-2 py-1.5 focus:outline-none focus:border-primary-400" />
        <span className="text-xs text-gray-400">–</span>
        <input type="date" value={hasta} onChange={e => setHasta(e.target.value)}
          className="text-xs border border-gray-200 rounded px-2 py-1.5 focus:outline-none focus:border-primary-400" />
        <button onClick={cargar} disabled={loading}
          className="px-3 py-1.5 text-xs border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-600 disabled:opacity-50">
          {loading ? '...' : '↻ Filtrar'}
        </button>
      </div>
      {items.length === 0 ? (
        <p className="text-xs text-gray-400 italic">Sin corridas registradas.</p>
      ) : (
        <div className="overflow-auto max-h-72">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-100 text-gray-400 text-left">
                <th className="pb-1.5 pr-3">Inicio</th>
                <th className="pb-1.5 pr-3">Fin</th>
                <th className="pb-1.5 pr-3 text-right">Correos</th>
                <th className="pb-1.5 pr-3 text-right">TX nuevas</th>
                <th className="pb-1.5 pr-3 text-right">TX enriq.</th>
                <th className="pb-1.5">Alertas</th>
              </tr>
            </thead>
            <tbody>
              {items.map(r => {
                const errores = r.alertas?.errores?.length ?? 0
                const adv     = r.alertas?.advertencias?.length ?? 0
                const completa = !!r.fecha_fin
                return (
                  <tr key={r.id} className="border-b border-gray-50 hover:bg-gray-50" title={r.notas ?? ''}>
                    <td className="py-1.5 pr-3 font-mono">{r.fecha_inicio?.slice(0, 16).replace('T', ' ')}</td>
                    <td className="py-1.5 pr-3 font-mono">
                      {r.fecha_fin ? r.fecha_fin.slice(11, 16) : <span className="text-red-400">anormal</span>}
                    </td>
                    <td className="py-1.5 pr-3 text-right">{r.correos_leidos}</td>
                    <td className="py-1.5 pr-3 text-right">{r.transacciones_nuevas}</td>
                    <td className="py-1.5 pr-3 text-right">{r.transacciones_enriquecidas}</td>
                    <td className="py-1.5">
                      {errores > 0 && <span className="text-red-600 font-semibold mr-1">{errores} err</span>}
                      {adv > 0    && <span className="text-yellow-600 mr-1">{adv} adv</span>}
                      {errores === 0 && adv === 0 && completa && <span className="text-green-600">OK</span>}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

function SeedSection() {
  const [prefijo,    setPrefijo]    = useState('SEED')
  const [fechaBase,  setFechaBase]  = useState('')
  const [running,    setRunning]    = useState(false)
  const [result,     setResult]     = useState(null)

  async function ejecutar() {
    setRunning(true)
    try {
      const r = await api.seed({ prefijo, fecha_base: fechaBase })
      setResult(r)
      toast.success(`Seed OK: ${r.ids.length} transacciones insertadas`)
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    } finally {
      setRunning(false)
    }
  }

  return (
    <Card title="Seed Controlado" icon="🌱">
      <p className="text-xs text-gray-500 mb-3">
        Inserta 4 transacciones de prueba: notificacion inicial, con factura,
        con extracto, y con entidad potencial pendiente (activa indicadores PEN-004).
        Todas en estado pendiente, revisado_humano=0.
      </p>
      <div className="flex gap-2 items-center mb-1 flex-wrap">
        <label className="text-xs text-gray-500">Prefijo:</label>
        <input type="text" value={prefijo} onChange={e => setPrefijo(e.target.value)}
          className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 w-28 focus:outline-none focus:border-primary-400" />
        <label className="text-xs text-gray-500">Fecha base:</label>
        <input type="date" value={fechaBase} onChange={e => setFechaBase(e.target.value)}
          className="text-sm border border-gray-200 rounded px-2 py-1.5 focus:outline-none focus:border-primary-400" />
        <Btn onClick={ejecutar} disabled={running || !prefijo}>
          {running ? 'Insertando...' : 'Execute'}
        </Btn>
      </div>
      <ResultBox result={result} />
    </Card>
  )
}

// -- Componente principal ----------------------------------------------
export default function Tools() {
  return (
    <div className="space-y-4 max-w-3xl">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">🔧 Tools</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Herramientas de administracion del entorno dev. No disponibles en produccion.
        </p>
      </div>

      <div className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-lg">
        <span className="text-xs font-medium text-amber-700">Entorno: DEV</span>
      </div>

      <ResetParcial />
      <ResetTotal />
      <BackupSection />
      <RestoreSection />
      <LogEjecuciones />
      <SeedSection />
    </div>
  )
}
