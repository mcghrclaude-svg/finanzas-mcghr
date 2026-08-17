import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMsal, useIsAuthenticated } from '@azure/msal-react'
import Combobox from '../../components/Combobox'
import PhotoInput from '../../components/PhotoInput'
import { useSettingsStore } from '../../store/settingsStore'
import { useCatalogos } from '../../hooks/useCatalogos'
import { db } from '../../db/db'
import { uuid, fileTimestamp } from '../../utils/ids'
import { syncPendientes } from '../../utils/sync'

const MAX_LEN_COMENTARIOS = 1000

function hoyISO() {
  return new Date().toISOString().slice(0, 10)
}

export default function NuevoGasto() {
  const navigate = useNavigate()
  const { instance, accounts } = useMsal()
  const isAuthenticated = useIsAuthenticated()
  const account = accounts[0]
  const { usuarioDispositivo, monedaDefault, medioPagoDefault } = useSettingsStore()
  const { catalogos, cargarEjemplo } = useCatalogos()

  const [fecha, setFecha] = useState(hoyISO())
  const [idCategoria, setIdCategoria] = useState(null)
  const [monto, setMonto] = useState('')
  const [idMoneda, setIdMoneda] = useState(monedaDefault)
  const [idMedioPago, setIdMedioPago] = useState(medioPagoDefault)
  const [quien, setQuien] = useState(usuarioDispositivo)
  const [comentarios, setComentarios] = useState('')
  const [foto, setFoto] = useState(null)
  // PhotoInput guarda su propio preview interno -- para descartar la foto
  // "por completo" (no solo el state aca) hay que forzar su remount.
  const [fotoKey, setFotoKey] = useState(0)
  const [guardado, setGuardado] = useState(false)
  const [error, setError] = useState(null)

  const mediosFiltrados = catalogos.medios_de_pago.filter(
    (m) => m.propietario === quien || m.propietario === 'Ambos'
  )

  // Si cambia "quien" y el medio de pago elegido deja de ser valido para
  // el nuevo propietario, se limpia para forzar reeleccion. No toca la
  // seleccion mientras el catalogo todavia no cargo (lista vacia).
  useEffect(() => {
    if (!idMedioPago || catalogos.medios_de_pago.length === 0) return
    const actual = catalogos.medios_de_pago.find((m) => m.id === idMedioPago)
    const sigueValido = actual && (actual.propietario === quien || actual.propietario === 'Ambos')
    if (!sigueValido) setIdMedioPago(null)
  }, [quien, catalogos.medios_de_pago])

  function validar() {
    if (!fecha || !idCategoria || !monto || !idMoneda || !idMedioPago || !quien) {
      return 'Completa fecha, categoria, monto, moneda, medio de pago y quien realizo el gasto'
    }
    if (Number.isNaN(Number(monto)) || Number(monto) <= 0) {
      return 'El monto debe ser un numero mayor a cero'
    }
    return null
  }

  // Equivalente a entrar de nuevo a la pantalla desde cero: no toca
  // error/guardado, eso lo maneja cada llamante segun corresponda.
  function resetFormulario() {
    setFecha(hoyISO())
    setIdCategoria(null)
    setMonto('')
    setIdMoneda(monedaDefault)
    setIdMedioPago(medioPagoDefault)
    setQuien(usuarioDispositivo)
    setComentarios('')
    setFoto(null)
    setFotoKey((k) => k + 1)
  }

  function limpiar() {
    setError(null)
    setGuardado(false)
    resetFormulario()
  }

  // Devuelve true/false segun si pudo guardar, para que cada boton decida
  // que hacer despues (navegar vs resetear el formulario).
  async function guardarGasto() {
    const problema = validar()
    if (problema) {
      setError(problema)
      return false
    }
    setError(null)

    const archivoBase = `gasto_${fileTimestamp()}`
    const registro = {
      id: uuid(),
      fecha,
      id_categoria: idCategoria,
      monto: Number(monto),
      id_moneda: idMoneda,
      id_medio_pago: idMedioPago,
      quien,
      comentarios: comentarios.trim() || null,
      archivoBase,
      imagenBlob: foto ?? null,
      imagenNombre: foto ? `${archivoBase}.jpg` : null,
      creadoEn: new Date().toISOString(),
    }

    await db.gastosPendientes.add(registro)
    setGuardado(true)

    // Intento de subida en background; si falla queda pendiente y se
    // reintenta despues (boton manual en Ver Pendientes, o proxima carga).
    if (isAuthenticated) {
      syncPendientes(account).catch((err) => console.warn('Sync en background fallo:', err))
    }

    setTimeout(() => setGuardado(false), 2500)
    return true
  }

  async function grabarYCerrar() {
    const ok = await guardarGasto()
    if (ok) navigate('/')
  }

  async function grabarYNuevo() {
    const ok = await guardarGasto()
    if (ok) resetFormulario()
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="mx-auto max-w-md">
        <div className="flex items-center gap-3 mb-6">
          <Link to="/" className="text-blue-600 text-sm font-medium">{'<- Volver'}</Link>
          <h1 className="text-xl font-semibold text-gray-900">Agregar gasto</h1>
        </div>

        {catalogos.categorias.length === 0 && (
          <div className="mb-4 rounded-lg bg-yellow-50 border border-yellow-200 p-3 text-sm text-yellow-800">
            No hay catalogos cargados todavia.{' '}
            <button onClick={cargarEjemplo} className="underline font-medium">
              Usar datos de ejemplo (solo pruebas)
            </button>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm p-4 flex flex-col gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fecha</label>
            <input
              type="date"
              value={fecha}
              onChange={(e) => setFecha(e.target.value)}
              className="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Combobox
                label="Categoria"
                options={catalogos.categorias}
                value={idCategoria}
                onChange={setIdCategoria}
                placeholder="Buscar categoria..."
              />
            </div>

            <div>
              <Combobox
                label="Medio de pago"
                options={mediosFiltrados}
                value={idMedioPago}
                onChange={setIdMedioPago}
                placeholder="Buscar medio de pago..."
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Combobox
                label="Moneda"
                options={catalogos.monedas}
                value={idMoneda}
                onChange={setIdMoneda}
                placeholder="Buscar moneda..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Monto</label>
              <input
                type="number"
                inputMode="decimal"
                min="0"
                step="0.01"
                value={monto}
                onChange={(e) => setMonto(e.target.value)}
                className="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm focus:border-blue-500 focus:ring-blue-500"
                placeholder="0.00"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-sm font-medium text-gray-700">Comentarios</label>
              <span className="text-xs text-gray-400">{comentarios.length}/{MAX_LEN_COMENTARIOS}</span>
            </div>
            <textarea
              value={comentarios}
              onChange={(e) => setComentarios(e.target.value)}
              maxLength={MAX_LEN_COMENTARIOS}
              rows={3}
              placeholder="Notas opcionales..."
              className="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm focus:border-blue-500 focus:ring-blue-500 resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Quien realizo el gasto</label>
            <div className="flex gap-2">
              {['GHR', 'MC'].map((u) => (
                <button
                  key={u}
                  type="button"
                  onClick={() => setQuien(u)}
                  className={`flex-1 rounded-lg py-2 text-sm font-medium ${
                    quien === u ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {u}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Foto (opcional)</label>
            <PhotoInput key={fotoKey} onChange={setFoto} />
          </div>

          {/* Altura fija (2 lineas de text-sm) para que el mensaje nunca
              empuje el resto del layout -- ver mensajes revisados en
              validar() y "Grabado Localmente". */}
          <div className="h-10 flex items-center overflow-hidden">
            {error && <p className="text-sm text-red-600 leading-5">{error}</p>}
            {guardado && <p className="text-sm text-green-600 font-medium leading-5">Grabado Localmente</p>}
          </div>

          <div className="flex gap-2">
            <button
              onClick={limpiar}
              className="flex-1 rounded-lg bg-gray-200 text-gray-800 font-medium py-3 text-sm hover:bg-gray-300"
            >
              Limpiar
            </button>
            <button
              onClick={grabarYCerrar}
              className="flex-1 rounded-lg bg-blue-600 text-white font-medium py-3 text-sm hover:bg-blue-700"
            >
              Grabar y Cerrar
            </button>
            <button
              onClick={grabarYNuevo}
              className="flex-1 rounded-lg bg-blue-600 text-white font-medium py-3 text-sm hover:bg-blue-700"
            >
              Grabar y Nuevo
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
