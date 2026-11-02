import { useCallback, useEffect, useState } from 'react'
import { MapContainer } from 'react-leaflet'
import { api } from '../api'
import { CapaBase, CapaZonasCriticas, Leyenda, MarcadorReporte, Nivel } from '../components/Mapas'
import { CENTRO_PIURA, DISTRITOS, ESTADOS, NECESIDADES, NIVELES, TIPOS, fecha, tipoLabel } from '../catalogos'

const CLAVE_CONFIRMADOS = 'alerta-piura:confirmados'
const leerConfirmados = () => {
  try {
    return new Set(JSON.parse(localStorage.getItem(CLAVE_CONFIRMADOS) || '[]'))
  } catch {
    return new Set()
  }
}

export default function Mapa() {
  const [reportes, setReportes] = useState([])
  const [filtros, setFiltros] = useState({ distrito: '', nivel: '' })
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(true)
  const [confirmados, setConfirmados] = useState(leerConfirmados)

  const cargar = useCallback(async () => {
    try {
      setReportes(await api.listarReportes(filtros))
      setError('')
    } catch (e) {
      setError(`No se pudo cargar el mapa: ${e.message}`)
    } finally {
      setCargando(false)
    }
  }, [filtros])

  useEffect(() => {
    cargar()
    const t = setInterval(cargar, 30_000)
    return () => clearInterval(t)
  }, [cargar])

  // S1: "yo también lo veo" (verificación vecinal), una vez por dispositivo
  const confirmar = async (r) => {
    try {
      const res = await api.confirmar(r.id)
      setReportes((rs) => rs.map((x) => (x.id === r.id ? { ...x, ...res } : x)))
      const nuevos = new Set(confirmados).add(r.id)
      setConfirmados(nuevos)
      localStorage.setItem(CLAVE_CONFIRMADOS, JSON.stringify([...nuevos]))
    } catch (e) {
      alert(e.message)
    }
  }

  const activos = reportes.filter((r) => r.estado !== 'resuelto')

  return (
    <section className="pagina mapa-pagina">
      <div className="filtros">
        <h1>Mapa público de riesgo</h1>
        <select aria-label="Distrito" value={filtros.distrito} onChange={(e) => setFiltros({ ...filtros, distrito: e.target.value })}>
          <option value="">Todos los distritos</option>
          {DISTRITOS.map((d) => <option key={d}>{d}</option>)}
        </select>
        <select aria-label="Nivel" value={filtros.nivel} onChange={(e) => setFiltros({ ...filtros, nivel: e.target.value })}>
          <option value="">Todos los niveles</option>
          {NIVELES.map((n) => <option key={n}>{n}</option>)}
        </select>
        <span className="contador">{cargando ? 'Cargando…' : `${activos.length} puntos activos`}</span>
      </div>
      {error && <p className="alerta">{error}</p>}
      <div className="mapa-grande">
        <MapContainer center={CENTRO_PIURA} zoom={12}>
          <CapaBase />
          <CapaZonasCriticas />
          {reportes.map((r) => (
            <MarcadorReporte key={r.id} r={r}>
              <div className="popup">
                <strong>{TIPOS[r.tipo]?.icono} {tipoLabel(r.tipo)}</strong>
                <div><Nivel nivel={r.nivel} prioridad={r.prioridad} /> · {ESTADOS[r.estado]}</div>
                <div className="tenue">{r.distrito} · {fecha(r.creado_en)}</div>
                {r.descripcion_ia && <p>{r.descripcion_ia}</p>}
                <ul className="motivos">{r.motivos.map((m) => <li key={m}>{m}</li>)}</ul>
                {r.necesidades.length > 0 && (
                  <div className="tenue">Necesita: {r.necesidades.map((n) => NECESIDADES[n]).join(', ')}</div>
                )}
                {r.estado !== 'resuelto' && (
                  <button className="boton primario" disabled={confirmados.has(r.id)} onClick={() => confirmar(r)}>
                    {confirmados.has(r.id) ? `✔ Confirmado (${r.confirmaciones})` : `👁 Yo también lo veo (${r.confirmaciones})`}
                  </button>
                )}
              </div>
            </MarcadorReporte>
          ))}
        </MapContainer>
        <Leyenda />
      </div>
      <p className="ayuda">El mapa público no muestra fotos ni datos personales. Coordenadas redondeadas (~10 m). Las zonas moradas son puntos críticos citados por Defensoría, Contraloría y prensa.</p>
    </section>
  )
}
