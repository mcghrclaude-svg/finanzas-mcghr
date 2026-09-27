/**
 * PresupuestoCard.jsx -- tarjeta de una categoria, tamano fijo, navegable.
 *
 * Una categoria sin hijos (hoja) muestra un campo editable. Una categoria
 * con hijos muestra el total (suma de sus hojas) y, dentro de la misma
 * tarjeta, hasta 2 de sus hijos directos -- editables ahi mismo si a su vez
 * son hoja. Si tiene mas de 2 hijos, o si se hace click en el encabezado,
 * se "entra" a verlos todos en sus propias tarjetas (mismo patron,
 * recursivo). Tamano fijo (sin scroll nunca): lo que no entra se resume en
 * "+N mas".
 */
import CampoMonto from './CampoMonto'
import { esHoja, calcularTotal, contarFaltantes, fmt, fmtCompacto } from './presupuestoUtils'

const MAX_FILAS_PREVIEW = 2

function Badge({ children, tono }) {
  const clases = tono === 'alerta'
    ? 'bg-warning-100 text-warning-500'
    : 'bg-primary-50 text-primary-700'
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded-md whitespace-nowrap flex-shrink-0 ${clases}`}>
      {children}
    </span>
  )
}

export default function PresupuestoCard({ nodo, valores, resumenById, anteriorById, copiadoPendiente, totalGeneral, onChange, onEntrar }) {
  const hoja = esHoja(nodo)
  const total = calcularTotal(nodo, valores)
  const pct = totalGeneral > 0 ? Math.round((total / totalGeneral) * 100) : 0
  const promedio = resumenById[nodo.id] ?? 0
  const { total: totalHojas, faltantes } = contarFaltantes(nodo, valores)

  const esCopiado = hoja && copiadoPendiente
    && anteriorById[nodo.id] != null
    && valores[nodo.id] === anteriorById[nodo.id]
  const sinDefinir = hoja && valores[nodo.id] == null

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-3.5 flex flex-col overflow-hidden h-[184px] box-border">
      <div
        className={`flex items-center justify-between gap-1.5 mb-0.5 ${!hoja ? 'cursor-pointer' : ''}`}
        onClick={!hoja ? () => onEntrar(nodo) : undefined}
      >
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="text-sm font-semibold text-gray-900 truncate">{nodo.nombre}</span>
          {esCopiado && <Badge>copiado</Badge>}
          {sinDefinir && <Badge tono="alerta">sin definir</Badge>}
          {!hoja && faltantes > 0 && <Badge tono="alerta">{`faltan ${faltantes}`}</Badge>}
        </div>
        {!hoja && <span className="text-gray-400 text-base flex-shrink-0">&rsaquo;</span>}
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-lg font-bold text-gray-900">{fmt(total) || '$0'}</span>
        <span className="text-xs text-gray-400">{pct}%</span>
      </div>
      <div className="text-[10px] text-gray-400 mb-1.5">Promedio 3m: {fmt(promedio)}</div>

      {hoja ? (
        <div className="mt-auto">
          <CampoMonto valor={valores[nodo.id] ?? null} onChange={(v) => onChange(nodo.id, v)} />
        </div>
      ) : (
        <div className="flex flex-col gap-1.5 overflow-hidden">
          {nodo.hijos.slice(0, MAX_FILAS_PREVIEW).map(hijo => {
            const hijoEsHoja = esHoja(hijo)
            const totalHijo = calcularTotal(hijo, valores)
            return (
              <div key={hijo.id} className="flex items-center justify-between gap-1.5">
                <div className="min-w-0">
                  <div className="text-[11px] text-gray-700 truncate">{hijo.nombre}</div>
                  <div className="text-[10px] text-gray-400">
                    prom {fmtCompacto(resumenById[hijo.id] ?? 0)}
                  </div>
                </div>
                {hijoEsHoja ? (
                  <CampoMonto valor={valores[hijo.id] ?? null} onChange={(v) => onChange(hijo.id, v)} placeholder="-" compacto />
                ) : (
                  <div
                    className="flex items-center gap-1 flex-shrink-0 cursor-pointer"
                    onClick={(e) => { e.stopPropagation(); onEntrar(hijo) }}
                  >
                    <span className="text-xs font-medium text-gray-700">{fmtCompacto(totalHijo)}</span>
                    <span className="text-gray-400">&rsaquo;</span>
                  </div>
                )}
              </div>
            )
          })}
          {nodo.hijos.length > MAX_FILAS_PREVIEW && (
            <div
              className="text-[11px] text-primary-600 cursor-pointer"
              onClick={(e) => { e.stopPropagation(); onEntrar(nodo) }}
            >
              {`+${nodo.hijos.length - MAX_FILAS_PREVIEW} mas - click para ver`}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
