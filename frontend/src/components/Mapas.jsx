import { Circle, CircleMarker, Popup, TileLayer, Tooltip } from 'react-leaflet'
import { COLOR_NIVEL, NIVELES, ZONAS_CRITICAS, tipoLabel } from '../catalogos'

export function CapaBase() {
  return (
    <TileLayer
      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      maxZoom={19}
    />
  )
}

// Zonas críticas citadas en prensa (radio de 300 m que suma prioridad)
export function CapaZonasCriticas() {
  return ZONAS_CRITICAS.map((z) => (
    <Circle
      key={z.id}
      center={[z.lat, z.lon]}
      radius={300}
      pathOptions={{ color: '#6a1b9a', weight: 1.5, dashArray: '4 4', fillOpacity: 0.08 }}
    >
      <Tooltip>
        <strong>Zona crítica: {z.nombre}</strong>
        <br />
        {z.fuente}
        {z.coordenada_aproximada ? ' (ubicación aproximada)' : ''}
      </Tooltip>
    </Circle>
  ))
}

export function MarcadorReporte({ r, seleccionado, onClick, children }) {
  const inactivo = r.estado === 'resuelto' || r.estado === 'descartado'
  const color = inactivo ? '#9e9e9e' : COLOR_NIVEL[r.nivel]
  return (
    <CircleMarker
      center={[r.lat, r.lon]}
      radius={seleccionado ? 13 : r.nivel === 'CRÍTICA' ? 10 : 8}
      pathOptions={{ color: seleccionado ? '#000' : '#fff', weight: seleccionado ? 3 : 2, fillColor: color, fillOpacity: 0.9 }}
      eventHandlers={onClick ? { click: () => onClick(r) } : undefined}
    >
      <Tooltip>{tipoLabel(r.tipo)} · {r.nivel} ({r.prioridad})</Tooltip>
      {children && <Popup>{children}</Popup>}
    </CircleMarker>
  )
}

export function Leyenda() {
  return (
    <div className="leyenda">
      {NIVELES.map((n) => (
        <span key={n}>
          <i style={{ background: COLOR_NIVEL[n] }} /> {n}
        </span>
      ))}
      <span>
        <i style={{ background: '#9e9e9e' }} /> Resuelto
      </span>
      <span>
        <i className="zona" /> Zona crítica
      </span>
    </div>
  )
}

export function Nivel({ nivel, prioridad }) {
  return (
    <span className="nivel" style={{ background: COLOR_NIVEL[nivel] }}>
      {nivel}
      {prioridad !== undefined ? ` · ${prioridad}/100` : ''}
    </span>
  )
}
