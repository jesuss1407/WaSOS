import { useEffect, useState } from 'react'
import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import Reportar from './pages/Reportar'
import Mapa from './pages/Mapa'
import Tablero from './pages/Tablero'
import { pendientes } from './lib/colaOffline'

function useEnLinea() {
  const [enLinea, setEnLinea] = useState(navigator.onLine)
  const [cola, setCola] = useState(pendientes())
  useEffect(() => {
    const on = () => setEnLinea(true)
    const off = () => setEnLinea(false)
    const cambio = () => setCola(pendientes())
    window.addEventListener('online', on)
    window.addEventListener('offline', off)
    window.addEventListener('cola-cambio', cambio)
    return () => {
      window.removeEventListener('online', on)
      window.removeEventListener('offline', off)
      window.removeEventListener('cola-cambio', cambio)
    }
  }, [])
  return { enLinea, cola }
}

export default function App() {
  const { enLinea, cola } = useEnLinea()
  return (
    <div className="app">
      <header className="barra">
        <NavLink to="/" className="marca">
          <img src="/icon.svg" alt="" width="28" height="28" />
          <span>WaSOS</span>
        </NavLink>
        <nav>
          <NavLink to="/" end>Reportar</NavLink>
          <NavLink to="/mapa">Mapa</NavLink>
          <NavLink to="/tablero">Tablero</NavLink>
        </nav>
      </header>
      {(!enLinea || cola > 0) && (
        <div className="aviso-red" role="status">
          {!enLinea ? 'Sin conexión. ' : ''}
          {cola > 0 ? `${cola} reporte(s) pendiente(s): se enviarán solos al volver la señal.` : 'Puedes reportar igual: lo guardamos en tu celular.'}
        </div>
      )}
      <main>
        <Routes>
          <Route path="/" element={<Reportar />} />
          <Route path="/mapa" element={<Mapa />} />
          <Route path="/tablero" element={<Tablero />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <footer className="pie">
        Emergencias: <a href="tel:105">105 PNP</a> · <a href="tel:116">116 Bomberos</a> · <a href="tel:106">106 SAMU</a>{' '}
        <small>(números a verificar)</small> · Mapa © OpenStreetMap
      </footer>
    </div>
  )
}
