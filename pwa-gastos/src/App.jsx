import { HashRouter, Routes, Route } from 'react-router-dom'
import Home from './modules/Home'
import Configuracion from './modules/Configuracion'
import NuevoGasto from './modules/NuevoGasto'
import GastosPendientes from './modules/GastosPendientes'
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
        <Route path="/pendientes" element={<GastosPendientes />} />
        <Route path="/resumen" element={<ResumenMes />} />
      </Routes>
    </HashRouter>
  )
}
