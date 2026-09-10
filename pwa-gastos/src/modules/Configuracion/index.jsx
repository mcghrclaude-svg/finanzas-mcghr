import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMsal, useIsAuthenticated } from '@azure/msal-react'
import { loginRequest } from '../../auth/msalConfig'
import OneDrivePickerModal from '../../components/OneDrivePickerModal'
import SimpleSelect from '../../components/SimpleSelect'
import CategoriaVisibilidadTree from '../../components/CategoriaVisibilidadTree'
import ColorPickerPopover from '../../components/ColorPickerPopover'
import { ensureFolder, getAccessToken } from '../../api/graphClient'
import { useSettingsStore } from '../../store/settingsStore'
import { useCatalogos } from '../../hooks/useCatalogos'
import { useMedioPagoFiltrado } from '../../hooks/useMedioPagoFiltrado'

const TABS = [
  { id: 'cuenta', etiqueta: 'Cuenta' },
  { id: 'preferencias', etiqueta: 'Preferencias' },
  { id: 'indicadores', etiqueta: 'Indicadores' },
]

function FolderRow({ label, carpeta, onElegir }) {
  return (
    <div className="flex items-center justify-between gap-3 py-3 border-b border-gray-200">
      <div>
        <p className="font-medium text-gray-900">{label}</p>
        <p className="text-sm text-gray-500 truncate max-w-[16rem]">
          {carpeta ? carpeta.nombre : 'No configurada'}
        </p>
      </div>
      <button
        onClick={onElegir}
        className="shrink-0 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
      >
        Elegir
      </button>
    </div>
  )
}

export default function Configuracion() {
  const { instance, accounts } = useMsal()
  const isAuthenticated = useIsAuthenticated()
  const account = accounts[0]
  const [error, setError] = useState(null)
  const [cargando, setCargando] = useState(false)
  const [pickerAbierto, setPickerAbierto] = useState(false)
  const [colorTotalPopoverAbierto, setColorTotalPopoverAbierto] = useState(false)
  const [tab, setTab] = useState('cuenta')

  const {
    carpetaRaiz, setCarpetaRaiz,
    usuarioDispositivo, setUsuarioDispositivo,
    monedaDefault, setMonedaDefault,
    medioPagoDefault, setMedioPagoDefault,
    categoriasOcultasHome, toggleCategoriaOcultaHome,
    coloresCategorias, setColorCategoria,
    colorTotalHome, setColorTotalHome,
    umbralAdvertencia, setUmbralAdvertencia,
    umbralExcedido, setUmbralExcedido,
  } = useSettingsStore()
  const { catalogos } = useCatalogos()
  const mediosFiltrados = useMedioPagoFiltrado(
    catalogos.medios_de_pago,
    usuarioDispositivo,
    medioPagoDefault,
    setMedioPagoDefault
  )

  async function login() {
    try {
      await instance.loginRedirect(loginRequest)
    } catch (err) {
      setError(String(err))
    }
  }

  function logout() {
    instance.logoutRedirect()
  }

  function abrirPicker() {
    if (!isAuthenticated) {
      setError('Inicia sesion con Microsoft antes de elegir una carpeta')
      return
    }
    setError(null)
    setPickerAbierto(true)
  }

  async function handlePick(carpeta) {
    setPickerAbierto(false)
    setCargando(true)
    try {
      const token = await getAccessToken(account)
      await ensureFolder(token, carpeta.driveId, carpeta.itemId, 'pendientes')
      await ensureFolder(token, carpeta.driveId, carpeta.itemId, 'procesados')
      await ensureFolder(token, carpeta.driveId, carpeta.itemId, 'Catalogos')
      await ensureFolder(token, carpeta.driveId, carpeta.itemId, 'Resumen')
      setCarpetaRaiz(carpeta)
    } catch (err) {
      setError(String(err))
    } finally {
      setCargando(false)
    }
  }

  function handleCancelPicker() {
    setPickerAbierto(false)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="mx-auto max-w-md">
        <div className="flex items-center gap-3 mb-6">
          <Link to="/" className="text-blue-600 text-sm font-medium">{'<- Volver'}</Link>
          <h1 className="text-xl font-semibold text-gray-900">Configuracion</h1>
        </div>

        <div className="flex gap-1 bg-white rounded-xl shadow-sm p-1 mb-4">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${
                tab === t.id ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              {t.etiqueta}
            </button>
          ))}
        </div>

        {tab === 'cuenta' && (
          <>
            <div className="bg-white rounded-xl shadow-sm p-4 mb-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Sesion Microsoft</p>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">
                  {isAuthenticated ? `Conectado: ${account?.username}` : 'No conectado'}
                </span>
                {isAuthenticated ? (
                  <button onClick={logout} className="rounded-lg bg-gray-200 px-3 py-2 text-sm font-medium text-gray-800 hover:bg-gray-300">
                    Cerrar sesion
                  </button>
                ) : (
                  <button onClick={login} className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700">
                    Iniciar sesion
                  </button>
                )}
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm px-4 mb-4">
              <FolderRow label="Carpeta raiz" carpeta={carpetaRaiz} onElegir={abrirPicker} />
            </div>
          </>
        )}

        {tab === 'preferencias' && (
          <>
            <div className="bg-white rounded-xl shadow-sm p-4 mb-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Usuario de este dispositivo</p>
              <div className="flex gap-2">
                {['GHR', 'MC'].map((u) => (
                  <button
                    key={u}
                    onClick={() => setUsuarioDispositivo(u)}
                    className={`flex-1 rounded-lg border py-2 text-sm font-medium ${
                      usuarioDispositivo === u
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-white text-gray-700 border-gray-300'
                    }`}
                  >
                    {u}
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm p-4 mb-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Moneda por default</p>
              <SimpleSelect
                options={catalogos.monedas}
                value={monedaDefault}
                onChange={setMonedaDefault}
                placeholder="Seleccionar..."
              />
            </div>

            <div className="bg-white rounded-xl shadow-sm p-4 mb-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Medio de pago por default</p>
              <SimpleSelect
                options={mediosFiltrados}
                value={medioPagoDefault}
                onChange={setMedioPagoDefault}
                placeholder="Seleccionar..."
              />
            </div>

            <div className="bg-white rounded-xl shadow-sm p-4 mb-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-700">Color del total en inicio</p>
                  <p className="text-xs text-gray-500 mt-0.5">Barra de "Gasto acumulado" en el Home</p>
                </div>
                <div className="relative shrink-0">
                  <button
                    type="button"
                    onClick={() => setColorTotalPopoverAbierto((v) => !v)}
                    className="w-8 h-8 rounded-full"
                    style={{ background: colorTotalHome, boxShadow: '0 0 0 1px rgba(0,0,0,0.08)' }}
                  />
                  {colorTotalPopoverAbierto && (
                    <ColorPickerPopover
                      value={colorTotalHome}
                      onChange={setColorTotalHome}
                      onClose={() => setColorTotalPopoverAbierto(false)}
                    />
                  )}
                </div>
              </div>
            </div>
          </>
        )}

        {tab === 'indicadores' && (
          <>
            <div className="bg-white rounded-xl shadow-sm p-4 mb-4">
              <p className="text-sm font-medium text-gray-700 mb-1">Ícono de atención por categoría</p>
              <p className="text-xs text-gray-500 mb-3">
                A qué % del presupuesto se enciende cada aviso junto al título de la etiqueta en el Home.
              </p>
              <div className="flex items-center justify-between gap-3 py-2">
                <span className="flex items-center gap-2 text-sm text-gray-700">
                  <span className="w-5 h-5 rounded-full bg-amber-500 shrink-0" />
                  Advertencia (ámbar) desde
                </span>
                <div className="flex items-center gap-1 shrink-0">
                  <input
                    type="number"
                    min={0}
                    max={300}
                    value={umbralAdvertencia}
                    onChange={(e) => setUmbralAdvertencia(Number(e.target.value))}
                    className="w-16 rounded-lg border border-gray-300 py-1.5 px-2 text-sm text-right"
                  />
                  <span className="text-sm text-gray-500">%</span>
                </div>
              </div>
              <div className="flex items-center justify-between gap-3 py-2 border-t border-gray-100">
                <span className="flex items-center gap-2 text-sm text-gray-700">
                  <span className="w-5 h-5 rounded-full bg-red-600 shrink-0" />
                  Excedido (rojo) desde
                </span>
                <div className="flex items-center gap-1 shrink-0">
                  <input
                    type="number"
                    min={0}
                    max={300}
                    value={umbralExcedido}
                    onChange={(e) => setUmbralExcedido(Number(e.target.value))}
                    className="w-16 rounded-lg border border-gray-300 py-1.5 px-2 text-sm text-right"
                  />
                  <span className="text-sm text-gray-500">%</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm p-3 mb-4">
              <p className="text-sm font-medium text-gray-700 px-1 mb-1">Categorias visibles en inicio</p>
              <p className="text-xs text-gray-500 px-1 mb-2">
                Navega el arbol, tildá "Ver" para que la categoría aparezca en el
                Home, y elegí el color de su barra en el bullet chart.
              </p>
              <CategoriaVisibilidadTree
                categorias={catalogos.categorias}
                ocultas={categoriasOcultasHome}
                onToggleOculta={toggleCategoriaOcultaHome}
                colores={coloresCategorias}
                onSetColor={setColorCategoria}
              />
            </div>
          </>
        )}

        {cargando && <p className="text-sm text-gray-500">Procesando...</p>}
        {error && <p className="text-sm text-red-600 break-words">{error}</p>}
      </div>

      {pickerAbierto && (
        <OneDrivePickerModal account={account} onPick={handlePick} onCancel={handleCancelPicker} />
      )}
    </div>
  )
}
