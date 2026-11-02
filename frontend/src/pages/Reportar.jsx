import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import L from 'leaflet'
import { MapContainer, Marker, useMap, useMapEvents } from 'react-leaflet'
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'
import { CapaBase, CapaZonasCriticas, Nivel } from '../components/Mapas'
import { CENTRO_PIURA, DISTRITOS, DISTRITOS_DATA, NECESIDADES, TIPOS, tipoLabel } from '../catalogos'
import { comprimirImagen } from '../lib/comprimirImagen'
import { distritoMasCercano, dentroDeRegion } from '../lib/geo'
import { encolar, enviarReporte } from '../lib/colaOffline'

L.Icon.Default.mergeOptions({ iconUrl, iconRetinaUrl, shadowUrl })

function SelectorUbicacion({ pos, onCambio }) {
  const map = useMap()
  useMapEvents({ click: (e) => onCambio([e.latlng.lat, e.latlng.lng]) })
  useEffect(() => {
    if (pos) map.setView(pos, Math.max(map.getZoom(), 16))
  }, [pos?.[0], pos?.[1]]) // eslint-disable-line react-hooks/exhaustive-deps
  if (!pos) return null
  return (
    <Marker
      position={pos}
      draggable
      eventHandlers={{
        dragend: (e) => {
          const ll = e.target.getLatLng()
          if (!onCambio([ll.lat, ll.lng])) e.target.setLatLng(pos) // rechazado: el pin vuelve a su lugar
        },
      }}
    />
  )
}

const INICIAL = { tipo: '', descripcion: '', vulnerables: false, necesidades: [], consentimiento: false }

export default function Reportar() {
  const [form, setForm] = useState(INICIAL)
  const [foto, setFoto] = useState(null) // { blob, url }
  const [pos, setPos] = useState(null)
  const [precision, setPrecision] = useState(null)
  const [distrito, setDistrito] = useState('')
  const [estadoGps, setEstadoGps] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')
  const [resultado, setResultado] = useState(null)
  const [guardadoOffline, setGuardadoOffline] = useState(false)
  const inputFoto = useRef(null)

  const set = (campo, valor) => setForm((f) => ({ ...f, [campo]: valor }))

  const pedirGps = () => {
    if (!('geolocation' in navigator)) {
      setEstadoGps('Tu navegador no permite GPS: toca el mapa para marcar el lugar.')
      return
    }
    setEstadoGps('Buscando tu ubicación…')
    navigator.geolocation.getCurrentPosition(
      (p) => {
        const nueva = [p.coords.latitude, p.coords.longitude]
        if (!dentroDeRegion(...nueva)) {
          setEstadoGps('Tu ubicación está fuera de la región Piura: marca el lugar en el mapa.')
          return
        }
        setPos(nueva)
        setPrecision(Math.round(p.coords.accuracy))
        setEstadoGps('')
      },
      () => setEstadoGps('No pudimos obtener el GPS: toca el mapa para marcar el lugar.'),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 30000 },
    )
  }

  useEffect(() => { pedirGps() }, [])

  // Pin movido a mano (toque o arrastre): solo se acepta dentro de la región Piura (mismo bbox que la API)
  const moverPin = (nueva) => {
    if (!dentroDeRegion(nueva[0], nueva[1])) {
      setEstadoGps('Ese punto está fuera de la región Piura: marca un lugar dentro de la región.')
      return false
    }
    setEstadoGps('')
    setPrecision(null)
    setPos(nueva)
    return true
  }

  // Distrito autodetectado por cercanía al centroide (editable)
  useEffect(() => {
    if (pos) setDistrito(distritoMasCercano(pos[0], pos[1], DISTRITOS_DATA))
  }, [pos])

  useEffect(() => () => foto?.url && URL.revokeObjectURL(foto.url), [foto])

  // Al mostrar el resultado, volver arriba (el botón Enviar está al final del formulario)
  useEffect(() => {
    if (resultado || guardadoOffline) window.scrollTo(0, 0)
  }, [resultado, guardadoOffline])

  const onFoto = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setError('')
    try {
      const blob = await comprimirImagen(file)
      setFoto({ blob, url: URL.createObjectURL(blob) })
    } catch (err) {
      setError(err.message)
    }
  }

  const toggleNecesidad = (n) =>
    set('necesidades', form.necesidades.includes(n) ? form.necesidades.filter((x) => x !== n) : [...form.necesidades, n])

  const faltantes = useMemo(() => {
    const f = []
    if (!foto) f.push('la foto')
    if (!pos) f.push('la ubicación')
    if (!form.tipo) f.push('qué pasa')
    if (!form.consentimiento) f.push('el consentimiento')
    return f
  }, [foto, pos, form.tipo, form.consentimiento])

  const enviar = async (e) => {
    e.preventDefault()
    if (faltantes.length) return
    setEnviando(true)
    setError('')
    const datos = {
      lat: pos[0],
      lon: pos[1],
      distrito,
      tipo: form.tipo,
      descripcion: form.descripcion.trim(),
      vulnerables: form.vulnerables,
      necesidades: form.necesidades,
      consentimiento: true,
    }
    let fotoKey = null
    try {
      if (!navigator.onLine) throw new TypeError('offline')
      const r = await enviarReporte(datos, foto.blob, null, (k) => { fotoKey = k })
      setResultado(r)
    } catch (err) {
      if (err.status && err.status < 500) {
        setError(err.detalles ? Object.values(err.detalles).join('. ') : err.message)
      } else {
        try {
          await encolar(datos, foto.blob, fotoKey)
          setGuardadoOffline(true)
        } catch (e2) {
          setError(e2.message)
        }
      }
    } finally {
      setEnviando(false)
    }
  }

  const reiniciar = () => {
    setForm(INICIAL)
    setFoto(null)
    setResultado(null)
    setGuardadoOffline(false)
    setError('')
    if (inputFoto.current) inputFoto.current.value = ''
    window.scrollTo(0, 0)
  }

  if (resultado || guardadoOffline) {
    return (
      <section className="pagina estrecha">
        {resultado ? (
          <div className="tarjeta resultado">
            <h1>¡Gracias! Tu reporte fue registrado</h1>
            <p><Nivel nivel={resultado.nivel} prioridad={resultado.prioridad} /></p>
            {resultado.es_valida === false ? (
              <p className="alerta">La foto no parece mostrar un riesgo. Un operador la revisará antes de publicarla en el mapa.</p>
            ) : (
              <p>Ya aparece en el <Link to="/mapa">mapa público</Link>. Las autoridades lo ven en su tablero, ordenado por prioridad.</p>
            )}
            <h2>Clasificación</h2>
            <p>
              <strong>{TIPOS[resultado.tipo]?.icono} {tipoLabel(resultado.tipo)}</strong>
              {resultado.tipo !== form.tipo && <> · <small>tipo sugerido por la IA (tú elegiste: {tipoLabel(form.tipo)})</small></>}
            </p>
            {resultado.descripcion_ia && <p className="ia">“{resultado.descripcion_ia}”</p>}
            <h2>¿Por qué esta prioridad?</h2>
            <ul className="motivos">
              {resultado.motivos.map((m) => <li key={m}>{m}</li>)}
            </ul>
          </div>
        ) : (
          <div className="tarjeta resultado">
            <h1>Reporte guardado en tu celular</h1>
            <p>No hay conexión estable. Lo enviaremos automáticamente cuando vuelva la señal; no cierres el navegador por completo.</p>
          </div>
        )}
        <div className="tarjeta emergencia">
          <h2>Si hay riesgo para la vida, llama ya</h2>
          <p>
            <a className="boton rojo" href="tel:105">105 · Policía</a>
            <a className="boton rojo" href="tel:116">116 · Bomberos</a>
            <a className="boton rojo" href="tel:106">106 · SAMU</a>
          </p>
          <small>Números de referencia a verificar con las autoridades locales.</small>
        </div>
        <button className="boton primario ancho" onClick={reiniciar}>Reportar otro punto</button>
      </section>
    )
  }

  return (
    <form className="pagina estrecha" onSubmit={enviar}>
      <h1>Reporta un punto crítico</h1>
      <p className="intro">Sin registro ni datos personales. Tu foto ayuda a priorizar a brigadas y autoridades de Piura ante El Niño costero.</p>

      <fieldset className="tarjeta">
        <legend>1. Foto del lugar</legend>
        <input ref={inputFoto} id="foto" type="file" accept="image/*" capture="environment" onChange={onFoto} hidden />
        <label htmlFor="foto" className="boton primario ancho">{foto ? '📷 Cambiar foto' : '📷 Tomar o elegir foto'}</label>
        {foto && (
          <figure className="vista-previa">
            <img src={foto.url} alt="Vista previa de la foto del reporte" />
            <figcaption>{Math.round(foto.blob.size / 1024)} KB · sin metadatos de ubicación (EXIF)</figcaption>
          </figure>
        )}
      </fieldset>

      <fieldset className="tarjeta">
        <legend>2. Ubicación</legend>
        <p className="ayuda">
          {estadoGps || (pos ? `Arrastra el pin o toca el mapa para ajustar${precision ? ` (precisión ±${precision} m)` : ''}.` : 'Toca el mapa para marcar el lugar.')}
        </p>
        <div className="mapa-chico">
          <MapContainer center={pos || CENTRO_PIURA} zoom={pos ? 16 : 12} scrollWheelZoom={false}>
            <CapaBase />
            <CapaZonasCriticas />
            <SelectorUbicacion pos={pos} onCambio={moverPin} />
          </MapContainer>
        </div>
        <div className="fila">
          <button type="button" className="boton" onClick={pedirGps}>📍 Usar mi ubicación</button>
          <label className="campo">
            Distrito
            <select value={distrito} onChange={(e) => setDistrito(e.target.value)} required>
              <option value="" disabled>Elegir…</option>
              {DISTRITOS.map((d) => <option key={d}>{d}</option>)}
            </select>
          </label>
        </div>
      </fieldset>

      <fieldset className="tarjeta">
        <legend>3. ¿Qué está pasando?</legend>
        <div className="opciones">
          {Object.entries(TIPOS).map(([k, t]) => (
            <label key={k} className={`opcion ${form.tipo === k ? 'activa' : ''}`}>
              <input type="radio" name="tipo" value={k} checked={form.tipo === k} onChange={() => set('tipo', k)} />
              <span aria-hidden="true">{t.icono}</span> {t.label}
            </label>
          ))}
        </div>
        <label className="campo">
          Descripción (opcional)
          <textarea
            maxLength={500}
            rows={3}
            value={form.descripcion}
            onChange={(e) => set('descripcion', e.target.value)}
            placeholder="Ej.: el dren está lleno de basura y el agua ya entra a las casas"
          />
          <small>{form.descripcion.length}/500 · no escribas nombres ni teléfonos</small>
        </label>
        <label className="check">
          <input type="checkbox" checked={form.vulnerables} onChange={(e) => set('vulnerables', e.target.checked)} />
          Hay personas vulnerables (niños, adultos mayores, personas con discapacidad, gestantes)
        </label>
      </fieldset>

      <fieldset className="tarjeta">
        <legend>4. ¿Qué se necesita?</legend>
        <div className="chips">
          {Object.entries(NECESIDADES).map(([k, label]) => (
            <button
              type="button"
              key={k}
              className={`chip ${form.necesidades.includes(k) ? 'activa' : ''}`}
              aria-pressed={form.necesidades.includes(k)}
              onClick={() => toggleNecesidad(k)}
            >
              {label}
            </button>
          ))}
        </div>
      </fieldset>

      <fieldset className="tarjeta">
        <label className="check">
          <input type="checkbox" checked={form.consentimiento} onChange={(e) => set('consentimiento', e.target.checked)} />
          <span>
            Acepto que la foto y la ubicación se usen solo para la gestión de esta emergencia (Ley 29733 de Protección de Datos
            Personales). La foto solo la ven las autoridades; el mapa público no muestra fotos.
          </span>
        </label>
      </fieldset>

      {error && <p className="alerta" role="alert">{error}</p>}
      <button className="boton primario ancho grande" disabled={enviando || faltantes.length > 0}>
        {enviando ? 'Analizando la foto con IA…' : 'Enviar reporte'}
      </button>
      {faltantes.length > 0 && <p className="ayuda centro">Falta: {faltantes.join(', ')}.</p>}
    </form>
  )
}
