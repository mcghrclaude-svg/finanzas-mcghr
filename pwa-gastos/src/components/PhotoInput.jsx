import { useRef, useState } from 'react'
import { compressPhoto } from '../utils/imageCompress'

// Dos botones (camara / galeria) que comparten el mismo <input type="file">
// pero cambian el atributo "capture" segun cual se toco.
export default function PhotoInput({ onChange }) {
  const inputRef = useRef(null)
  const [preview, setPreview] = useState(null)
  const [comprimiendo, setComprimiendo] = useState(false)

  function abrir(capture) {
    if (capture) {
      inputRef.current.setAttribute('capture', capture)
    } else {
      inputRef.current.removeAttribute('capture')
    }
    inputRef.current.click()
  }

  async function handleFile(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setComprimiendo(true)
    try {
      const compressed = await compressPhoto(file)
      setPreview(URL.createObjectURL(compressed))
      onChange(compressed)
    } finally {
      setComprimiendo(false)
    }
  }

  function quitar() {
    setPreview(null)
    onChange(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div>
      <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={handleFile} />
      {preview ? (
        <div className="flex items-center gap-3">
          <img src={preview} alt="Foto del gasto" className="w-20 h-20 object-cover rounded-lg border border-gray-200" />
          <button type="button" onClick={quitar} className="text-sm text-red-600 font-medium">
            Quitar foto
          </button>
        </div>
      ) : (
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => abrir('environment')}
            className="flex-1 rounded-lg border border-gray-300 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Camara
          </button>
          <button
            type="button"
            onClick={() => abrir(null)}
            className="flex-1 rounded-lg border border-gray-300 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Galeria
          </button>
        </div>
      )}
      {comprimiendo && <p className="text-xs text-gray-500 mt-1">Comprimiendo foto...</p>}
    </div>
  )
}
