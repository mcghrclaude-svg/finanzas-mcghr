/**
 * App.jsx
 * Cambios vs anterior:
 *   - Eliminado import de Inbox
 *   - Ruta /inbox redirige permanentemente a /transacciones
 *   - Transacciones es el modulo unificado (inbox + transacciones)
 */
import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from '@/components/layout/Layout'
import Dashboard from '@/modules/Dashboard'
import Transacciones from '@/modules/Transacciones'
import Presupuesto from '@/modules/Presupuesto'
import Obligaciones from '@/modules/Obligaciones'
import Inversiones from '@/modules/Inversiones'
import Catalogos from '@/modules/Catalogos'
import Analitica from '@/modules/Analitica'
import Backup from '@/modules/Backup'
import { Toaster } from 'react-hot-toast'
import AlertaSinGuardar from '@/components/shared/AlertaSinGuardar'

export default function App() {
  return (
    <>
      <Toaster position="top-right" />
      <AlertaSinGuardar />
      <Layout>
        <Routes>
          <Route path="/"              element={<Navigate to="/dashboard"     replace />} />
          <Route path="/inbox"         element={<Navigate to="/transacciones" replace />} />
          <Route path="/dashboard"     element={<Dashboard />} />
          <Route path="/transacciones" element={<Transacciones />} />
          <Route path="/presupuesto"   element={<Presupuesto />} />
          <Route path="/obligaciones"  element={<Obligaciones />} />
          <Route path="/inversiones"   element={<Inversiones />} />
          <Route path="/catalogos/*"   element={<Catalogos />} />
          <Route path="/analitica"     element={<Analitica />} />
          <Route path="/backup"        element={<Backup />} />
        </Routes>
      </Layout>
    </>
  )
}
