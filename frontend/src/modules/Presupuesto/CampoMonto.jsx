/**
 * CampoMonto.jsx -- input de monto en pesos, sin decimales.
 * El "$" y los separadores de miles son una mascara del propio input (no
 * hay un componente ni un span aparte): mientras esta enfocado se ven los
 * digitos crudos que se estan tipeando (sin re-formatear en cada tecla,
 * para no romper la posicion del cursor), y al perder el foco se muestra
 * el valor formateado.
 */
import { useState, useEffect } from 'react'
import { fmt } from './presupuestoUtils'

export default function CampoMonto({ valor, onChange, placeholder = 'Sin definir', compacto = false }) {
  const [editando, setEditando] = useState(false)
  const [texto, setTexto] = useState(valor != null ? fmt(valor) : '')

  useEffect(() => {
    if (!editando) setTexto(valor != null ? fmt(valor) : '')
  }, [valor, editando])

  function manejarInput(e) {
    const digitos = e.target.value.replace(/[^0-9]/g, '')
    setTexto(digitos)
    onChange(digitos === '' ? null : Number(digitos))
  }

  const vacio = valor == null

  return (
    <input
      type="text"
      inputMode="numeric"
      value={texto}
      placeholder={placeholder}
      onFocus={() => setEditando(true)}
      onBlur={() => setEditando(false)}
      onChange={manejarInput}
      className={`text-right border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-100 focus:border-primary-500 text-gray-900 ${
        compacto ? 'text-xs px-1.5 py-1 w-[68px]' : 'text-sm px-3 py-2 w-full'
      } ${vacio ? 'border-gray-200' : 'border-primary-300'}`}
    />
  )
}
