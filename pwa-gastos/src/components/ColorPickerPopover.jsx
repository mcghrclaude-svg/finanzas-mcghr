import { useRef, useState } from 'react'

const PALETA = ['#14b8a6', '#7c5cd9', '#d97706', '#2563eb', '#db2777', '#16a34a', '#dc2626', '#64748b', '#0891b2', '#a16207']

function hsvToRgb(h, s, v) {
  s /= 100; v /= 100
  const k = (n) => (n + h / 60) % 6
  const f = (n) => v - v * s * Math.max(0, Math.min(k(n), 4 - k(n), 1))
  return [Math.round(f(5) * 255), Math.round(f(3) * 255), Math.round(f(1) * 255)]
}
function rgbToHsv(r, g, b) {
  r /= 255; g /= 255; b /= 255
  const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min
  let h = 0
  if (d !== 0) {
    if (max === r) h = 60 * (((g - b) / d) % 6)
    else if (max === g) h = 60 * ((b - r) / d + 2)
    else h = 60 * ((r - g) / d + 4)
  }
  if (h < 0) h += 360
  return [h, max === 0 ? 0 : (d / max) * 100, max * 100]
}
function hexToRgb(hex) {
  const m = hex.replace('#', '').match(/^([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i)
  if (!m) return [20, 184, 166]
  return [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)]
}
function rgbToHex([r, g, b]) {
  return '#' + [r, g, b].map((n) => Math.max(0, Math.min(255, n)).toString(16).padStart(2, '0')).join('')
}

// Selector de color estandar + personalizado, estilo "mas colores" pero
// reducido a lo esencial: cuadrado de saturacion/brillo + tira de matiz
// + hex, sin sliders de R/G/B separados. Los presets estandar alcanzan
// para el caso comun; el cuadrado da libertad total cuando hace falta.
export default function ColorPickerPopover({ value, onChange, onClose }) {
  const [hsv, setHsv] = useState(() => rgbToHsv(...hexToRgb(value)))
  const [h, s, v] = hsv
  const hexActual = rgbToHex(hsvToRgb(h, s, v))
  const svRef = useRef(null)
  const hueRef = useRef(null)

  function arrastrar(ref, onMove) {
    return (eInicial) => {
      eInicial.preventDefault()
      const mover = (e) => {
        const rect = ref.current.getBoundingClientRect()
        const x = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
        const y = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height))
        onMove(x, y)
      }
      mover(eInicial)
      const soltar = () => {
        window.removeEventListener('pointermove', mover)
        window.removeEventListener('pointerup', soltar)
      }
      window.addEventListener('pointermove', mover)
      window.addEventListener('pointerup', soltar)
    }
  }

  function onHex(e) {
    const limpio = e.target.value.trim()
    if (/^#?[0-9a-f]{6}$/i.test(limpio)) {
      setHsv(rgbToHsv(...hexToRgb(limpio)))
    }
  }

  return (
    <div
      className="absolute z-20 mt-1.5 right-0 w-52 bg-white border border-gray-200 rounded-xl shadow-lg p-3"
      onClick={(e) => e.stopPropagation()}
    >
      <p className="text-[0.68rem] font-bold uppercase tracking-wide text-gray-500 mb-1.5">Colores estándar</p>
      <div className="grid grid-cols-5 gap-1.5 mb-3">
        {PALETA.map((color) => (
          <button
            key={color}
            type="button"
            className={`w-6 h-6 rounded-full border-2 ${color.toLowerCase() === value.toLowerCase() ? 'border-gray-900' : 'border-transparent'}`}
            style={{ background: color }}
            onClick={() => { onChange(color); onClose() }}
          />
        ))}
      </div>

      <div className="h-px bg-gray-200 mb-3" />

      <p className="text-[0.68rem] font-bold uppercase tracking-wide text-gray-500 mb-1.5">Personalizado</p>
      <div
        ref={svRef}
        className="relative w-full h-28 rounded-lg mb-2.5 cursor-crosshair touch-none"
        style={{
          background: `linear-gradient(to top, #000, transparent), linear-gradient(to right, #fff, hsl(${h},100%,50%))`,
        }}
        onPointerDown={arrastrar(svRef, (x, y) => setHsv([h, x * 100, (1 - y) * 100]))}
      >
        <div
          className="absolute w-3 h-3 rounded-full border-2 border-white pointer-events-none"
          style={{ left: `${s}%`, top: `${100 - v}%`, transform: 'translate(-50%, -50%)', boxShadow: '0 0 0 1px rgba(0,0,0,.4), 0 1px 3px rgba(0,0,0,.4)' }}
        />
      </div>

      <div
        ref={hueRef}
        className="relative w-full h-3.5 rounded-full mb-2.5 cursor-pointer touch-none"
        style={{ background: 'linear-gradient(to right, #f00, #ff0, #0f0, #0ff, #00f, #f0f, #f00)' }}
        onPointerDown={arrastrar(hueRef, (x) => setHsv([x * 360, s, v]))}
      >
        <div
          className="absolute top-1/2 w-3.5 h-3.5 rounded-full border-2 border-white pointer-events-none"
          style={{ left: `${(h / 360) * 100}%`, transform: 'translate(-50%, -50%)', boxShadow: '0 0 0 1px rgba(0,0,0,.4), 0 1px 3px rgba(0,0,0,.4)' }}
        />
      </div>

      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-md shrink-0 shadow-[0_0_0_1px_rgba(0,0,0,0.1)]" style={{ background: hexActual }} />
        <input
          className="flex-1 min-w-0 border border-gray-200 rounded-md px-2 py-1 text-xs uppercase tabular-nums"
          defaultValue={hexActual}
          key={hexActual}
          onChange={onHex}
          maxLength={7}
        />
        <button
          type="button"
          className="shrink-0 rounded-md bg-violet-600 text-white text-xs font-semibold px-2.5 py-1.5"
          onClick={() => { onChange(hexActual); onClose() }}
        >
          Usar
        </button>
      </div>
    </div>
  )
}
