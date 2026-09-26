import { useState } from 'react'
import { ExclamationTriangleIcon } from './icons'
import { useSettingsStore } from '../store/settingsStore'

// Bullet chart para presupuesto por categoria: una sola barra (gasto
// acumulado, con el color elegido para la categoria en Configuracion)
// con una marca gruesa violeta (presupuesto) y un rombo (promedio
// ultimos 3 meses), en vez de las 3 barras horizontales de antes.
// Etiquetas de valor superpuestas en HTML
// (no texto SVG) para que el tamano de letra no se achique cuando el
// grafico se hace angosto en la grilla de 2 columnas.
//
// El alto del area del grafico es FIJO en pixeles (no proporcional al
// ancho): con un alto proporcional, en una tarjeta angosta de celular
// las etiquetas de presupuesto/promedio terminaban a pocos pixeles de
// distancia entre si y se pisaban. El SVG tambien queda anclado a un
// "top" fijo (no centrado) para que el rombo/la marca no se muevan
// entre la variante normal y la "alta" (2 filas de etiquetas): lo unico
// que cambia es cuanto espacio libre queda despues.
const ALTO_NORMAL = 60
const ALTO_ALTO = 80
const Y_GASTO = 6
const Y_FILA_1 = 49
const Y_FILA_2 = 68

function fmt(v) {
  return new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 }).format(v)
}

// Formato compacto para las etiquetas del grafico: sin separador de
// miles ni centavos, solo K/M. El decimal de "M" se omite si es ",0"
// (se muestra "$1M", no "$1.0M").
function fmtCompacto(v) {
  if (v === null || v === undefined) return '—'
  const signo = v < 0 ? '-' : ''
  const abs = Math.abs(v)
  if (abs >= 1000000) {
    const decimas = Math.round(abs / 100000)
    const entero = Math.floor(decimas / 10)
    const resto = decimas % 10
    return `${signo}$${entero}${resto ? '.' + resto : ''}M`
  }
  if (abs >= 1000) return `${signo}$${Math.round(abs / 1000)}K`
  return `${signo}$${Math.round(abs)}`
}

// left/top/transform para una etiqueta superpuesta al grafico. xPct es
// horizontal (escala con el ancho); yPx es vertical en pixeles reales
// fijos. Cerca de los bordes horizontales cambia el anclaje para que la
// etiqueta no se corte contra el borde de la tarjeta.
function estiloEtiqueta(xPct, yPx) {
  let left, translateX
  if (xPct <= 10) { left = '2%'; translateX = '0%' }
  else if (xPct >= 90) { left = '98%'; translateX = '-100%' }
  else { left = `${xPct}%`; translateX = '-50%' }
  return { left, top: `${yPx}px`, transform: `translate(${translateX}, -50%)` }
}

// Icono de atencion junto al titulo, aparte del color de la barra (que
// ahora es libre eleccion del usuario, ver Configuracion): ambar cerca
// del limite, rojo si ya se paso -- los umbrales se configuran en
// Configuracion > Indicadores. Insignia rellena (no solo el trazo) para
// que llame la atencion de verdad, no un detalle sutil mas. Nada si no
// hay presupuesto cargado o si va bien encaminado.
function IconoEstado({ gasto, presupuesto, umbralAdvertencia, umbralExcedido }) {
  if (!presupuesto) return null
  const ratioPct = (gasto / presupuesto) * 100
  if (ratioPct >= umbralExcedido) {
    return (
      <span className="shrink-0 inline-flex items-center justify-center w-5 h-5 rounded-full bg-red-600 ring-2 ring-red-200 animate-pulse">
        <ExclamationTriangleIcon className="w-3.5 h-3.5 text-white" strokeWidth={2.5} />
      </span>
    )
  }
  if (ratioPct >= umbralAdvertencia) {
    return (
      <span className="shrink-0 inline-flex items-center justify-center w-5 h-5 rounded-full bg-amber-500 ring-2 ring-amber-200">
        <ExclamationTriangleIcon className="w-3.5 h-3.5 text-white" strokeWidth={2.5} />
      </span>
    )
  }
  return null
}

export default function BulletChart({ titulo, gasto, presupuesto, promedio, onDrill, color = '#14b8a6' }) {
  const [expandido, setExpandido] = useState(false)
  const { umbralAdvertencia, umbralExcedido } = useSettingsStore()

  const candidatos = [gasto, promedio]
  if (presupuesto !== null) candidatos.push(presupuesto)
  const max = Math.max(...candidatos) * 1.15
  const escalaPct = (v) => Math.max((v / max) * 100, v > 0 ? 0.8 : 0)
  const escalaSvg = (v) => (escalaPct(v) / 100) * 400

  const gastoPct = escalaPct(gasto)
  const promPct = escalaPct(promedio)
  const presPct = presupuesto !== null ? escalaPct(presupuesto) : null
  const promX = escalaSvg(promedio)
  const presX = presupuesto !== null ? escalaSvg(presupuesto) : null

  let promY = Y_FILA_1
  if (presPct !== null && Math.abs(presPct - promPct) < 16) promY = Y_FILA_2
  const alto = promY === Y_FILA_2 ? ALTO_ALTO : ALTO_NORMAL

  return (
    <div>
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <div className="flex items-center gap-1.5 min-w-0">
          {titulo}
          <IconoEstado gasto={gasto} presupuesto={presupuesto} umbralAdvertencia={umbralAdvertencia} umbralExcedido={umbralExcedido} />
        </div>
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); setExpandido((v) => !v) }}
          aria-label={expandido ? 'Ocultar detalle' : 'Expandir detalle'}
          className={`shrink-0 w-5 h-5 rounded-full border border-gray-200 bg-white shadow-sm text-gray-500 flex items-center justify-center text-sm leading-none transition-transform ${
            expandido ? 'rotate-45 text-gray-900' : ''
          }`}
        >
          +
        </button>
      </div>

      <div className="relative">
        <div
          className={`relative ${onDrill ? 'cursor-pointer' : ''}`}
          style={{ height: alto }}
          onClick={onDrill}
        >
          <svg
            viewBox="0 0 400 26"
            preserveAspectRatio="none"
            className="absolute left-0 w-full"
            style={{ top: 14, height: 24 }}
          >
            <rect x="0" y="4" width="400" height="18" rx="5" className="fill-gray-100" />
            <rect x="0" y="4" width={escalaSvg(gasto)} height="18" rx="5" style={{ fill: color }} />
            <rect
              x={promX - 5.5} y="7.5" width="11" height="11"
              transform={`rotate(45 ${promX} 13)`}
              className="fill-slate-500"
            />
            {presX !== null && (
              <line x1={presX} y1="0" x2={presX} y2="26" className="stroke-violet-500" strokeWidth="4" strokeLinecap="round" />
            )}
          </svg>

          <span
            className="absolute text-[11px] font-bold whitespace-nowrap bg-white px-1 rounded pointer-events-none tabular-nums"
            style={{ ...estiloEtiqueta(gastoPct, Y_GASTO), color }}
          >
            {fmtCompacto(gasto)}
          </span>
          {presX !== null && (
            <span
              className="absolute text-[11px] font-bold whitespace-nowrap bg-white px-1 rounded pointer-events-none tabular-nums text-violet-600"
              style={estiloEtiqueta(presPct, Y_FILA_1)}
            >
              {fmtCompacto(presupuesto)}
            </span>
          )}
          <span
            className="absolute text-[11px] font-bold whitespace-nowrap bg-white px-1 rounded pointer-events-none tabular-nums text-slate-500"
            style={estiloEtiqueta(promPct, promY)}
          >
            {fmtCompacto(promedio)}
          </span>
        </div>

        {expandido && (
          <>
            <div className="fixed inset-0 bg-black/30 z-30" onClick={() => setExpandido(false)} />
            <div className="absolute left-0 right-0 top-full mt-2 z-40 bg-white rounded-xl border border-gray-200 shadow-lg p-3 flex flex-col gap-2 text-xs text-gray-600">
              {/* Label y valor van en lineas separadas, no en una sola
                  fila: en una tarjeta angosta de celular no entran los
                  dos juntos y el texto terminaba cortandose a mitad de
                  palabra en vez de acomodarse prolijo. */}
              <div>
                <span className="flex items-center gap-1.5 whitespace-nowrap">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: color }} />
                  Gasto
                </span>
                <strong className="block text-gray-900 pl-[14px] whitespace-nowrap">$ {fmt(gasto)}</strong>
              </div>
              <div>
                <span className="flex items-center gap-1.5 whitespace-nowrap">
                  <span className="w-1 h-3.5 rounded shrink-0 bg-violet-500" />
                  Presupuesto
                </span>
                <strong className="block text-gray-900 pl-[14px] whitespace-nowrap">
                  {presupuesto === null ? '—' : `$ ${fmt(presupuesto)}`}
                </strong>
              </div>
              <div>
                <span className="flex items-center gap-1.5 whitespace-nowrap">
                  <span className="w-2 h-2 rotate-45 shrink-0 bg-slate-500" />
                  Promedio 3m
                </span>
                <strong className="block text-gray-900 pl-[14px] whitespace-nowrap">$ {fmt(promedio)}</strong>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
