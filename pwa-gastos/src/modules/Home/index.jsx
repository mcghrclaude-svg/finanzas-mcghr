import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Cog6ToothIcon, CloudIcon, InboxIcon, ExclamationTriangleIcon } from '../../components/icons'
import { useResumenCategorias } from '../../hooks/useResumenCategorias'
import { useSettingsStore } from '../../store/settingsStore'
import { db } from '../../db/db'

// __APP_BUILD_DATE__ llega en ISO 8601 (build-time, ver vite.config.js).
// Se normaliza a America/Bogota aca, no en el build, para que el valor
// crudo quede disponible sin perder informacion si en el futuro hace
// falta otro formato u otra zona horaria.
function formatearFechaBuild(iso) {
  if (!iso) return null
  const fecha = new Date(iso)
  if (Number.isNaN(fecha.getTime())) return null
  const partes = new Intl.DateTimeFormat('es-CO', {
    timeZone: 'America/Bogota',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).formatToParts(fecha)
  const valor = (tipo) => partes.find((p) => p.type === tipo)?.value ?? ''
  return `${valor('day')}/${valor('month')}/${valor('year')} ${valor('hour')}:${valor('minute')}`
}

function formatearNumero(valor) {
  return new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 }).format(valor ?? 0)
}

// Barra horizontal generica: valor/maximo de la fila, sin unidad de moneda
// (las transacciones pueden mezclar monedas -- ver limitacion ya existente
// en presupuesto_service.py, no se resuelve en este bloque).
function Barra({ etiqueta, valor, maximo, colorBarra, colorTexto }) {
  const pct = maximo > 0 ? Math.min((valor / maximo) * 100, 100) : 0
  return (
    <div className="flex items-center gap-2">
      <span className="w-14 shrink-0 text-xs text-gray-500">{etiqueta}</span>
      <div className="flex-1 h-2.5 rounded-full bg-gray-100 overflow-hidden">
        <div className={`h-full rounded-full ${colorBarra}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`w-24 shrink-0 text-right text-xs font-medium ${colorTexto}`}>{formatearNumero(valor)}</span>
    </div>
  )
}

function TresBarras({ datos }) {
  const maximo = Math.max(datos.gasto_acumulado, datos.presupuesto, datos.promedio_ultimos_3_meses, 1)
  return (
    <div className="flex flex-col gap-1.5">
      <Barra etiqueta="Gasto" valor={datos.gasto_acumulado} maximo={maximo} colorBarra="bg-teal-500" colorTexto="text-teal-700" />
      <Barra etiqueta="Presup." valor={datos.presupuesto} maximo={maximo} colorBarra="bg-violet-400" colorTexto="text-violet-700" />
      <Barra etiqueta="Prom. 3m" valor={datos.promedio_ultimos_3_meses} maximo={maximo} colorBarra="bg-amber-400" colorTexto="text-amber-700" />
    </div>
  )
}

function FilaCategoria({ cat, tieneHijos, onClick }) {
  return (
    <button
      onClick={onClick}
      disabled={!tieneHijos}
      className={`w-full bg-white rounded-xl shadow-sm p-3 flex flex-col gap-2 text-left ${tieneHijos ? 'hover:bg-gray-50' : ''}`}
    >
      <div className="flex items-center justify-between">
        <span className="font-medium text-gray-900">{cat.nombre}</span>
        {tieneHijos && <span className="text-gray-400">{'›'}</span>}
      </div>
      <TresBarras datos={cat} />
    </button>
  )
}

export default function Home() {
  const fechaBuild = formatearFechaBuild(__APP_BUILD_DATE__)
  const { resumen, cargarEjemplo } = useResumenCategorias()
  const { categoriasOcultasHome } = useSettingsStore()
  const [hayGastoConError, setHayGastoConError] = useState(false)

  // Solo se pisa el estado en 'inicio' -- viendoTodos y pila son
  // independientes entre si, nunca hay overlap de vistas.
  const [viendoTodos, setViendoTodos] = useState(false)
  const [pila, setPila] = useState([]) // [{id, nombre}] -- ultimo = nivel actual

  useEffect(() => {
    (async () => {
      const conError = await db.gastos.where('estado').equals('error').count()
      setHayGastoConError(conError > 0)
    })()
  }, [])

  const categorias = resumen.categorias ?? []
  const categoriasNivel1 = useMemo(() => categorias.filter((c) => c.nivel === 1), [categorias])
  const categoriasVisiblesHome = useMemo(
    () => categoriasNivel1.filter((c) => !categoriasOcultasHome.includes(c.id_categoria)),
    [categoriasNivel1, categoriasOcultasHome]
  )

  function tieneHijos(idCategoria) {
    return categorias.some((c) => c.id_padre === idCategoria)
  }

  const nivelActual = pila.length > 0 ? pila[pila.length - 1] : null
  const enRaiz = !nivelActual && !viendoTodos

  const listaMostrada = nivelActual
    ? categorias.filter((c) => c.id_padre === nivelActual.id)
    : viendoTodos
      ? categoriasNivel1
      : categoriasVisiblesHome

  function abrirCategoria(cat) {
    if (!tieneHijos(cat.id_categoria)) return
    setPila((p) => [...p, { id: cat.id_categoria, nombre: cat.nombre }])
  }

  function volverUnNivel() {
    if (pila.length > 0) {
      setPila((p) => p.slice(0, -1))
    } else if (viendoTodos) {
      setViendoTodos(false)
    }
  }

  function volverAlHome() {
    setPila([])
    setViendoTodos(false)
  }

  const tituloVista = nivelActual ? nivelActual.nombre : viendoTodos ? 'Todas las categorias' : null

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="mx-auto max-w-md">
        <div className="flex items-center justify-between mb-8 pt-2">
          <h1 className="text-2xl font-semibold text-gray-900">Gastos MCGHR</h1>
          <Link to="/configuracion" aria-label="Configuracion" className="p-2 text-gray-600 hover:text-gray-900">
            <Cog6ToothIcon className="w-7 h-7" />
          </Link>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-4 mb-4">
          {categorias.length === 0 ? (
            <div className="text-sm text-yellow-800 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              No hay datos de presupuesto todavia.{' '}
              <button onClick={cargarEjemplo} className="underline font-medium">
                Usar datos de ejemplo (solo pruebas)
              </button>
            </div>
          ) : (
            <>
              {!nivelActual && !viendoTodos && (
                <button onClick={() => setViendoTodos(true)} className="w-full text-left mb-4">
                  <TresBarras datos={resumen.total} />
                </button>
              )}

              {(nivelActual || viendoTodos) && (
                <div className="flex items-center justify-between mb-3">
                  <button onClick={volverUnNivel} className="text-blue-600 text-sm font-medium">
                    {'<- Atras'}
                  </button>
                  <span className="text-sm font-medium text-gray-700">{tituloVista}</span>
                  <button onClick={volverAlHome} className="text-blue-600 text-sm font-medium">
                    Home
                  </button>
                </div>
              )}

              <div className="flex flex-col gap-2">
                {listaMostrada.length === 0 ? (
                  <p className="text-sm text-gray-500">Sin categorias para mostrar.</p>
                ) : (
                  listaMostrada.map((cat) => (
                    <FilaCategoria
                      key={cat.id_categoria}
                      cat={cat}
                      tieneHijos={tieneHijos(cat.id_categoria)}
                      onClick={() => abrirCategoria(cat)}
                    />
                  ))
                )}
              </div>
            </>
          )}
        </div>

        <div className="flex gap-3 mb-3">
          <Link
            to="/actividad"
            className="flex-1 rounded-xl bg-white text-gray-900 font-medium py-3 text-center shadow-sm border border-gray-200 hover:bg-gray-50 flex items-center justify-center gap-1.5"
          >
            <CloudIcon className={`w-5 h-5 ${hayGastoConError ? 'text-amber-600' : 'text-gray-500'}`} />
            {hayGastoConError && <ExclamationTriangleIcon className="w-4 h-4 text-red-600" />}
            Actividad
          </Link>
          <Link
            to="/bandeja"
            className="flex-1 rounded-xl bg-white text-gray-900 font-medium py-3 text-center shadow-sm border border-gray-200 hover:bg-gray-50 flex items-center justify-center gap-1.5"
          >
            <InboxIcon className="w-5 h-5 text-gray-400" />
            Bandeja
          </Link>
        </div>

        <Link
          to="/nuevo-gasto"
          className="block rounded-xl bg-blue-600 text-white text-lg font-medium py-5 text-center shadow-sm hover:bg-blue-700"
        >
          Agregar gasto
        </Link>

        <p className="mt-8 text-center text-xs text-gray-400">
          v{__APP_VERSION__}
          {fechaBuild && <><br />{fechaBuild}</>}
        </p>
      </div>
    </div>
  )
}
