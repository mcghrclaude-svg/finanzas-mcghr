import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMsal, useIsAuthenticated } from '@azure/msal-react'
import { loginRequest } from '../../auth/msalConfig'
import OneDrivePickerModal from '../../components/OneDrivePickerModal'
import Combobox from '../../components/Combobox'
import { ensureFolder, getAccessToken } from '../../api/graphClient'
import { useSettingsStore } from '../../store/settingsStore'
import { useCatalogos } from '../../hooks/useCatalogos'

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

  const {
    carpetaRaiz, setCarpetaRaiz,
    configuracionMigradaDesdeVieja,
    usuarioDispositivo, setUsuarioDispositivo,
    monedaDefault, setMonedaDefault,
    medioPagoDefault, setMedioPagoDefault,
  } = useSettingsStore()
  const { catalogos } = useCatalogos()

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

        {configuracionMigradaDesdeVieja && !carpetaRaiz && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
            <p className="text-sm font-medium text-amber-800">Simplificamos la configuracion de carpetas</p>
            <p className="text-sm text-amber-700 mt-1">
              Antes elegias 3 carpetas por separado. Ahora alcanza con una sola
              carpeta raiz -- las subcarpetas se crean solas debajo. Elegi tu
              carpeta raiz de nuevo aca abajo; es un cambio de una sola vez, la
              app no se rompio.
            </p>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm px-4 mb-4">
          <FolderRow label="Carpeta raiz" carpeta={carpetaRaiz} onElegir={abrirPicker} />
        </div>

        <div className="bg-white rounded-xl shadow-sm p-4 mb-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Usuario de este dispositivo</p>
          <div className="flex gap-2">
            {['GHR', 'MC'].map((u) => (
              <button
                key={u}
                onClick={() => setUsuarioDispositivo(u)}
                className={`flex-1 rounded-lg py-2 text-sm font-medium ${
                  usuarioDispositivo === u ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
                }`}
              >
                {u}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-4 mb-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Moneda por default</p>
          <Combobox
            options={catalogos.monedas}
            value={monedaDefault}
            onChange={setMonedaDefault}
            placeholder="Buscar moneda..."
          />
        </div>

        <div className="bg-white rounded-xl shadow-sm p-4 mb-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Medio de pago por default</p>
          <Combobox
            options={catalogos.medios_de_pago}
            value={medioPagoDefault}
            onChange={setMedioPagoDefault}
            placeholder="Buscar medio de pago..."
          />
        </div>

        {cargando && <p className="text-sm text-gray-500">Procesando...</p>}
        {error && <p className="text-sm text-red-600 break-words">{error}</p>}
      </div>

      {pickerAbierto && (
        <OneDrivePickerModal account={account} onPick={handlePick} onCancel={handleCancelPicker} />
      )}
    </div>
  )
}
