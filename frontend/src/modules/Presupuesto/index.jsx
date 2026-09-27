/**
 * modules/Presupuesto/index.jsx
 *
 * Pantalla de definicion de presupuesto por categoria. El presupuesto de
 * una categoria con hijos es siempre la suma de sus hojas -- solo las
 * hojas se editan. Al entrar a un mes sin nada grabado, si el mes anterior
 * tenia presupuesto se trae solo (sin grabar todavia) como sugerencia.
 */
import { useState, useEffect, useCallback, useMemo } from 'react'
import useAppStore from '@/store/useAppStore'
import { usePresupuestoMes, useGuardarPresupuesto, mesAnterior } from '@/hooks/usePresupuestoDefinicion'
import { construirArbol, hojasDe } from './presupuestoUtils'
import PresupuestoCard from './PresupuestoCard'

const MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

function totalGeneralDe(arbol, valores) {
  return arbol.reduce((acc, raiz) => acc + hojasDe(raiz).reduce((a, h) => a + (valores[h.id] ?? 0), 0), 0)
}

export default function Presupuesto() {
  const hoy = new Date()
  const [anio, setAnio] = useState(hoy.getFullYear())
  const [mes, setMes] = useState(hoy.getMonth() + 1)

  const { categorias, resumenById, actualById, anteriorById, isLoading, error } = usePresupuestoMes(anio, mes)
  const { guardarPendientes, guardando } = useGuardarPresupuesto(anio, mes)
  const marcarCambio = useAppStore(s => s.marcarCambio)
  const limpiarCambios = useAppStore(s => s.limpiarCambios)
  const registrarGuardadoPendiente = useAppStore(s => s.registrarGuardadoPendiente)

  const arbol = useMemo(() => construirArbol(categorias), [categorias])

  const [valores, setValores] = useState({})
  const [copiadoPendiente, setCopiadoPendiente] = useState(false)
  const [pila, setPila] = useState([])
  const [inicializadoPara, setInicializadoPara] = useState(null)

  // Inicializa (una sola vez por mes) los valores editables: lo ya grabado
  // este mes, o -- si no hay nada grabado todavia -- lo del mes anterior
  // como sugerencia (sin grabar), marcando el banner de "se copio".
  useEffect(() => {
    const clave = `${anio}-${mes}`
    if (isLoading || inicializadoPara === clave) return
    const hayActual = Object.keys(actualById).length > 0
    if (hayActual) {
      setValores({ ...actualById })
      setCopiadoPendiente(false)
    } else if (Object.keys(anteriorById).length > 0) {
      setValores({ ...anteriorById })
      setCopiadoPendiente(true)
    } else {
      setValores({})
      setCopiadoPendiente(false)
    }
    setPila([])
    setInicializadoPara(clave)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [anio, mes, isLoading, inicializadoPara])

  const idsRelevantes = useMemo(
    () => new Set([...Object.keys(valores), ...Object.keys(actualById)]),
    [valores, actualById]
  )
  const dirty = useMemo(
    () => [...idsRelevantes].some(id => (valores[id] ?? null) !== (actualById[id] ?? null)),
    [idsRelevantes, actualById]
  )
  const copiable = useMemo(
    () => Object.entries(anteriorById).some(([id, monto]) => (valores[id] ?? null) !== monto),
    [valores, anteriorById]
  )
  const totalGeneral = useMemo(() => totalGeneralDe(arbol, valores), [arbol, valores])

  const handleGuardar = useCallback(async () => {
    const paraGuardar = []
    const paraBorrar = []
    for (const id of idsRelevantes) {
      const valorActual = valores[id] ?? null
      const base = actualById[id] ?? null
      if (valorActual === base) continue
      if (valorActual == null) paraBorrar.push(id)
      else paraGuardar.push({ idCategoria: id, monto: valorActual })
    }
    await guardarPendientes({ paraGuardar, paraBorrar })
    setCopiadoPendiente(false)
    limpiarCambios()
  }, [idsRelevantes, valores, actualById, guardarPendientes, limpiarCambios])

  useEffect(() => {
    if (dirty) marcarCambio()
    else limpiarCambios()
  }, [dirty, marcarCambio, limpiarCambios])

  useEffect(() => {
    registrarGuardadoPendiente(dirty ? handleGuardar : null)
    return () => registrarGuardadoPendiente(null)
  }, [dirty, handleGuardar, registrarGuardadoPendiente])

  function onChange(id, monto) {
    setValores(prev => ({ ...prev, [id]: monto }))
  }

  function copiarMesAnterior() {
    setValores(prev => ({ ...prev, ...anteriorById }))
    setCopiadoPendiente(true)
  }

  function entrar(nodo) {
    setPila(prev => [...prev, nodo])
  }

  function irA(indice) {
    setPila(prev => prev.slice(0, indice))
  }

  const nodoActual = pila.length ? pila[pila.length - 1] : null
  const nivelMostrado = nodoActual ? nodoActual.hijos : arbol

  const anioMesAnterior = mesAnterior(anio, mes)
  const nombreMesAnterior = MESES[anioMesAnterior.mes - 1]

  if (error) {
    return <div className="p-6 text-sm text-danger-500">Error cargando el presupuesto: {error.message}</div>
  }

  return (
    <div className="p-6 space-y-4 max-w-6xl">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-gray-900">Presupuesto</h1>
        <div className="flex items-center gap-2">
          <select
            value={mes}
            onChange={e => setMes(Number(e.target.value))}
            className="text-sm border border-gray-200 rounded-lg px-2.5 py-2 text-gray-700"
          >
            {MESES.map((nombre, i) => (
              <option key={nombre} value={i + 1}>{nombre}</option>
            ))}
          </select>
          <select
            value={anio}
            onChange={e => setAnio(Number(e.target.value))}
            className="text-sm border border-gray-200 rounded-lg px-2.5 py-2 text-gray-700"
          >
            {[hoy.getFullYear() - 1, hoy.getFullYear(), hoy.getFullYear() + 1].map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex-1 min-w-[240px]">
          {copiadoPendiente && (
            <div className="flex items-center gap-2.5 bg-primary-50 border border-primary-100 rounded-xl px-3.5 py-2.5">
              <span className="text-sm text-primary-700">
                Se copió el presupuesto de {nombreMesAnterior}. Revisalo y grabalo cuando quede como querés.
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={copiarMesAnterior}
            disabled={!copiable}
            title={`Vuelve todas las categorias al monto de ${nombreMesAnterior}`}
            className={`text-sm px-3.5 py-2 rounded-lg border transition-colors ${
              copiable
                ? 'border-primary-300 text-primary-700 hover:bg-primary-50'
                : 'border-gray-200 text-gray-400 cursor-default'
            }`}
          >
            Copiar mes anterior
          </button>
          <button
            onClick={handleGuardar}
            disabled={!dirty || guardando}
            className={`text-sm font-medium px-4 py-2 rounded-lg transition-colors ${
              dirty
                ? 'bg-primary-600 text-white hover:bg-primary-700'
                : 'bg-gray-200 text-gray-400 cursor-default'
            }`}
          >
            {guardando ? 'Guardando...' : 'Guardar presupuesto'}
          </button>
        </div>
      </div>

      <div className="flex items-center gap-1.5 text-sm">
        <button
          onClick={() => irA(0)}
          className={pila.length ? 'text-primary-600 hover:underline' : 'text-gray-900 font-medium'}
        >
          Inicio
        </button>
        {pila.map((nodo, i) => (
          <span key={nodo.id} className="flex items-center gap-1.5">
            <span className="text-gray-300">&rsaquo;</span>
            <button
              onClick={() => irA(i + 1)}
              className={i === pila.length - 1 ? 'text-gray-900 font-medium' : 'text-primary-600 hover:underline'}
            >
              {nodo.nombre}
            </button>
          </span>
        ))}
      </div>

      {isLoading ? (
        <div className="text-sm text-gray-400 py-10 text-center">Cargando presupuesto...</div>
      ) : nivelMostrado.length === 0 ? (
        <div className="text-sm text-gray-400 py-10 text-center">No hay categorías para mostrar.</div>
      ) : (
        <div className="grid gap-3" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
          {nivelMostrado.map(nodo => (
            <PresupuestoCard
              key={nodo.id}
              nodo={nodo}
              valores={valores}
              resumenById={resumenById}
              anteriorById={anteriorById}
              copiadoPendiente={copiadoPendiente}
              totalGeneral={totalGeneral}
              onChange={onChange}
              onEntrar={entrar}
            />
          ))}
        </div>
      )}
    </div>
  )
}
