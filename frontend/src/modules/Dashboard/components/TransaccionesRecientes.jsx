/**
 * TransaccionesRecientes — widget "Últimas transacciones" del Home.
 * Al hacer click en una fila, el mismo cuadro reemplaza el listado por el
 * panel de edición real de Transacciones (DetailPanel, modo="edicion") --
 * no tapa ningún otro widget de la página. "Cancelar"/"Guardar" vuelven al
 * listado.
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import DetailPanel from '@/modules/Transacciones/DetailPanel'
import { api as trxApi, fmt, fmtFecha } from '@/modules/Transacciones/shared'

export default function TransaccionesRecientes({ items, onEditada }) {
  const navigate = useNavigate()
  const [categorias, setCategorias] = useState([])
  const [contrapartes, setContrapartes] = useState([])
  const [cuentas, setCuentas] = useState([])
  const [seleccion, setSeleccion] = useState(null)

  useEffect(() => {
    const aLista = (r) => Array.isArray(r) ? r : (r?.items ?? [])
    trxApi.getCategorias().then(r => setCategorias(aLista(r))).catch(() => {})
    trxApi.getContrapartes().then(r => setContrapartes(aLista(r))).catch(() => {})
    trxApi.getCuentas().then(r => setCuentas(aLista(r))).catch(() => {})
  }, [])

  const nombreCategoria = (id) => categorias.find(c => c.id === id)?.nombre
  const nombreCuenta = (id) => cuentas.find(c => c.id === id)?.nombre

  async function handleEditar(id, data) {
    await trxApi.editar(id, data)
    onEditada?.()
  }

  if (seleccion) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl h-[300px] flex flex-col overflow-hidden">
        <DetailPanel
          item={seleccion}
          categorias={categorias}
          contrapartes={contrapartes}
          cuentas={cuentas}
          onEditar={handleEditar}
          modo="edicion"
          onCerrar={() => setSeleccion(null)}
        />
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl h-[300px] flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 flex-shrink-0">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Últimas transacciones</h2>
        <button onClick={() => navigate('/transacciones')} className="text-xs text-primary-600 hover:text-primary-700 font-medium">
          Ver todas →
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {(!items || items.length === 0) ? (
          <div className="py-8 text-center text-xs text-gray-400">Sin transacciones recientes.</div>
        ) : items.map(item => {
          const cuentaId = item.tramos?.[0]?.id_cuenta_origen
          const esGasto = item.tipo === 'gasto'
          return (
            <button
              key={item.id}
              onClick={() => setSeleccion(item)}
              className="w-full flex items-center gap-3 px-4 py-2.5 border-b border-gray-50 hover:bg-gray-50 text-left transition-colors"
            >
              <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center text-xs font-semibold text-gray-500 flex-shrink-0">
                {(item.descripcion || '?').slice(0, 1).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-900 truncate">{item.descripcion || 'Sin descripción'}</div>
                <div className="text-xs text-gray-400 truncate">
                  {nombreCategoria(item.id_categoria) ?? '—'} · {nombreCuenta(cuentaId) ?? '—'}
                </div>
              </div>
              {item.estado === 'pendiente' && (
                <span className="text-[10px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded flex-shrink-0">revisar</span>
              )}
              <div className="text-right flex-shrink-0">
                <div className={`text-sm font-semibold ${esGasto ? 'text-gray-900' : 'text-success-500'}`}>
                  {esGasto ? '-' : '+'}{fmt(item.monto, item.moneda)}
                </div>
                <div className="text-[10px] text-gray-400">{fmtFecha(item.fecha)}</div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
