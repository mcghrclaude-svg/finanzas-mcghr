import { HashRouter, Routes, Route } from 'react-router-dom'
import Home from './modules/Home'
import Configuracion from './modules/Configuracion'
import NuevoGasto from './modules/NuevoGasto'
import Actividad from './modules/Actividad'
import ResumenMes from './modules/ResumenMes'

// HashRouter: sirve bien tanto en localhost como en GitHub Pages sin
// depender del "base" de Vite para las rutas del cliente.
export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/configuracion" element={<Configuracion />} />
        <Route path="/nuevo-gasto" element={<NuevoGasto />} />
        <Route path="/nuevo-gasto/:id" element={<NuevoGasto />} />
        <Route path="/actividad" element={<Actividad />} />
        <Route path="/resumen" element={<ResumenMes />} />
      </Routes>
    </HashRouter>
  )
}
