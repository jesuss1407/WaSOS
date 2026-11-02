import { useCallback, useEffect, useState } from 'react'
import { MapContainer, useMap } from 'react-leaflet'
import { api } from '../api'
import { CapaBase, CapaZonasCriticas, Leyenda, MarcadorReporte, Nivel } from '../components/Mapas'
import { CENTRO_PIURA, COLOR_NIVEL, DISTRITOS, ESTADOS, NECESIDADES, NIVELES, TIPOS, fecha, tipoLabel } from '../catalogos'

const CLAVE_SESION = 'alerta-piura:admin-key'

function Acceso({ onOk }) {
  const [clave, setClave] = useState('')
  const [error, setError] = useState('')
  const entrar = async (e) => {
    e.preventDefault()
    try {
      await api.admin.resumen(clave)
      sessionStorage.setItem(CLAVE_SESION, clave)
      onOk(clave)
    } catch (err) {
      setError(err.status === 401 ? 'Clave incorrecta' : err.message)
    }
  }
  return (
    <form className="pagina estrecha" onSubmit={entrar}>
      <div className="tarjeta">
        <h1>Tablero de autoridades y brigadas</h1>
        <p>Acceso con la clave compartida del COER / municipalidad. (Roadmap: cuentas con roles en Amazon Cognito.)</p>
        <label className="campo">
          Clave de acceso
          <input type="password" value={clave} onChange={(e) => setClave(e.target.value)} autoComplete="current-password" required />
        </label>
        {error && <p className="alerta">{error}</p>}
        <button className="boton primario ancho">Entrar</button>
      </div>
    </form>
  )
}

function CentrarEn({ reporte }) {
  const map = useMap()
  useEffect(() => {
    if (reporte) map.setView([reporte.lat, reporte.lon], Math.max(map.getZoom(), 14))
  }, [reporte?.id]) // eslint-disable-line react-hooks/exhaustive-deps
  return null
}

function Detalle({ r, clave, onActualizado }) {
  const [brigada, setBrigada] = useState(r.brigada || '')
  const [nota, setNota] = useState('')
  const [error, setError] = useState('')
  const [guardando, setGuardando] = useState(false)
  useEffect(() => {
    setBrigada(r.brigada || '')
    setNota('')
    setError('')
  }, [r.id]) // eslint-disable-line react-hooks/exhaustive-deps

  const cambiar = async (estado) => {
    setGuardando(true)
    setError('')
    try {
      const actualizado = await api.admin.actualizar(clave, r.id, { estado, brigada: brigada || undefined, nota: nota || undefined })
      onActualizado(actualizado)
      setNota('')
    } catch (e) {
      setError(e.detalles ? Object.values(e.detalles).join('. ') : e.message)
    } finally {
      setGuardando(false)
    }
  }
  const ia = r.ia || {}
  return (
    <article className="tarjeta detalle">
      <header>
        <Nivel nivel={r.nivel} prioridad={r.prioridad} />
        <span className={`estado e-${r.estado}`}>{ESTADOS[r.estado]}</span>
      </header>
      <h2>{TIPOS[r.tipo]?.icono} {tipoLabel(r.tipo)}</h2>
      <p className="tenue">{r.distrito} · {fecha(r.creado_en)} · {r.lat.toFixed(5)}, {r.lon.toFixed(5)}</p>
      {r.foto_url ? (
        <a href={r.foto_url} target="_blank" rel="noreferrer"><img className="foto" src={r.foto_url} alt={`Foto del reporte: ${tipoLabel(r.tipo)}`} /></a>
      ) : (
        <p className="sin-foto">Reporte de demostración (sin foto)</p>
      )}
      <ul className="motivos">{(r.motivos || []).map((m) => <li key={m}>{m}</li>)}</ul>
      <dl>
        <dt>IA</dt>
        <dd>
          {ia.estado_ia === 'ok' && <>{ia.descripcion} <small>({ia.modelo}, confianza {Math.round((ia.confianza || 0) * 100)}%)</small></>}
          {ia.estado_ia === 'fallback' && <span className="alerta-texto">IA no disponible: verificar manualmente</span>}
          {ia.estado_ia === 'demo' && <>{ia.descripcion} <small>(dato demo, sin IA)</small></>}
        </dd>
        <dt>Tipo elegido por el vecino</dt><dd>{tipoLabel(r.tipo_usuario)}</dd>
        {r.descripcion && (<><dt>Descripción del vecino</dt><dd>{r.descripcion}</dd></>)}
        <dt>Necesidades</dt><dd>{r.necesidades?.length ? r.necesidades.map((n) => NECESIDADES[n]).join(', ') : '—'}</dd>
        <dt>Personas vulnerables</dt><dd>{r.vulnerables ? 'Sí' : 'No'}</dd>
        <dt>Confirmaciones vecinales</dt><dd>{r.confirmaciones || 0}</dd>
        {r.brigada && (<><dt>Brigada</dt><dd>{r.brigada}</dd></>)}
      </dl>
      {r.transiciones?.length > 0 && (
        <div className="acciones">
          {r.transiciones.includes('en_atencion') && (
            <label className="campo">
              Brigada asignada
              <input value={brigada} onChange={(e) => setBrigada(e.target.value)} maxLength={80} placeholder="Ej.: Brigada MPP 03" />
            </label>
          )}
          <label className="campo">
            Nota (opcional)
            <input value={nota} onChange={(e) => setNota(e.target.value)} maxLength={300} />
          </label>
          <div className="fila">
            {r.transiciones.map((t) => (
              <button key={t} className={`boton ${t === 'descartado' ? '' : 'primario'}`} disabled={guardando} onClick={() => cambiar(t)}>
                → {ESTADOS[t]}
              </button>
            ))}
          </div>
          {error && <p className="alerta">{error}</p>}
        </div>
      )}
      {r.historial?.length > 0 && (
        <details>
          <summary>Historial ({r.historial.length})</summary>
          <ol className="historial">
            {r.historial.map((h, i) => (
              <li key={i}>{fecha(h.fecha)} · <strong>{ESTADOS[h.estado]}</strong>{h.brigada ? ` · ${h.brigada}` : ''}{h.nota ? ` · ${h.nota}` : ''}</li>
            ))}
          </ol>
        </details>
      )}
    </article>
  )
}

function PanelNecesidades({ resumen }) {
  if (!resumen) return null
  return (
    <section className="tarjeta">
      <h2>Necesidades por distrito (reportes activos)</h2>
      <p className="tenue">Orienta la ayuda humanitaria: almacenes del GORE, colectas y voluntariado.</p>
      <div className="tabla-scroll">
        <table>
          <thead>
            <tr>
              <th>Distrito</th><th>Activos</th>
              {NIVELES.map((n) => <th key={n} style={{ color: COLOR_NIVEL[n] }}>{n}</th>)}
              <th>Vulnerables</th><th>¿Qué se necesita?</th>
            </tr>
          </thead>
          <tbody>
            {resumen.por_distrito.map((d) => (
              <tr key={d.distrito}>
                <td><strong>{d.distrito}</strong></td>
                <td>{d.total}</td>
                {NIVELES.map((n) => <td key={n}>{d.niveles[n] || ''}</td>)}
                <td>{d.vulnerables || ''}</td>
                <td>
                  {Object.entries(d.necesidades).map(([k, v]) => (
                    <span key={k} className="chip mini">{NECESIDADES[k]} {v}</span>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default function Tablero() {
  const [clave, setClave] = useState(() => sessionStorage.getItem(CLAVE_SESION) || '')
  const [filtros, setFiltros] = useState({ distrito: '', tipo: '', estado: '', nivel: '' })
  const [reportes, setReportes] = useState([])
  const [resumen, setResumen] = useState(null)
  const [sel, setSel] = useState(null)
  const [error, setError] = useState('')
  const [parte, setParte] = useState(null)
  const [generando, setGenerando] = useState(false)

  const salir = () => {
    sessionStorage.removeItem(CLAVE_SESION)
    setClave('')
  }

  const cargar = useCallback(async () => {
    if (!clave) return
    try {
      const [lista, res] = await Promise.all([api.admin.listar(clave, filtros), api.admin.resumen(clave)])
      setReportes(lista)
      setResumen(res)
      setSel((s) => (s ? lista.find((r) => r.id === s.id) || null : null))
      setError('')
    } catch (e) {
      if (e.status === 401) salir()
      else setError(e.message)
    }
  }, [clave, filtros])

  useEffect(() => {
    cargar()
    const t = setInterval(cargar, 30_000)
    return () => clearInterval(t)
  }, [cargar])

  if (!clave) return <Acceso onOk={setClave} />

  const onActualizado = (r) => {
    setReportes((rs) => rs.map((x) => (x.id === r.id ? r : x)))
    setSel(r)
    api.admin.resumen(clave).then(setResumen).catch(() => {})
  }

  const exportar = async () => {
    try {
      const blob = await api.admin.exportarCsv(clave)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `wasos-${new Date().toISOString().slice(0, 10)}.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e.message)
    }
  }

  const generarParte = async () => {
    setGenerando(true)
    try {
      setParte(await api.admin.parteSituacional(clave, filtros.distrito))
    } catch (e) {
      setError(e.message)
    } finally {
      setGenerando(false)
    }
  }

  const f = (campo) => (e) => setFiltros({ ...filtros, [campo]: e.target.value })

  return (
    <section className="pagina tablero">
      <div className="cabecera-tablero">
        <h1>Tablero priorizado</h1>
        <div className="kpis">
          {NIVELES.map((n) => (
            <button key={n} className={`kpi ${filtros.nivel === n ? 'activa' : ''}`} style={{ borderColor: COLOR_NIVEL[n] }}
              onClick={() => setFiltros({ ...filtros, nivel: filtros.nivel === n ? '' : n })}>
              <strong style={{ color: COLOR_NIVEL[n] }}>{resumen?.por_nivel?.[n] ?? '–'}</strong> {n}
            </button>
          ))}
          <span className="kpi">
            <strong>{resumen?.por_estado?.en_atencion ?? '–'}</strong> en atención
          </span>
        </div>
        <div className="fila">
          <button className="boton" onClick={exportar}>⬇ Exportar CSV</button>
          <button className="boton primario" onClick={generarParte} disabled={generando}>
            {generando ? 'Redactando…' : '📝 Parte situacional IA'}
          </button>
          <button className="boton" onClick={salir}>Salir</button>
        </div>
      </div>

      <div className="filtros">
        <select aria-label="Distrito" value={filtros.distrito} onChange={f('distrito')}>
          <option value="">Todos los distritos</option>
          {DISTRITOS.map((d) => <option key={d}>{d}</option>)}
        </select>
        <select aria-label="Tipo" value={filtros.tipo} onChange={f('tipo')}>
          <option value="">Todos los tipos</option>
          {Object.entries(TIPOS).map(([k, t]) => <option key={k} value={k}>{t.label}</option>)}
        </select>
        <select aria-label="Estado" value={filtros.estado} onChange={f('estado')}>
          <option value="">Todos los estados</option>
          {Object.entries(ESTADOS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select aria-label="Nivel" value={filtros.nivel} onChange={f('nivel')}>
          <option value="">Todos los niveles</option>
          {NIVELES.map((n) => <option key={n}>{n}</option>)}
        </select>
        <span className="contador">{reportes.length} reportes</span>
      </div>
      {error && <p className="alerta">{error}</p>}

      {parte && (
        <section className="tarjeta parte">
          <header className="fila">
            <h2>Parte situacional {parte.estado_ia === 'ok' ? `(IA · ${parte.modelo})` : '(sin IA)'}</h2>
            <button className="boton" onClick={() => navigator.clipboard?.writeText(parte.texto)}>Copiar</button>
            <button className="boton" onClick={() => setParte(null)}>Cerrar</button>
          </header>
          <pre>{parte.texto}</pre>
        </section>
      )}

      <div className="rejilla">
        <ol className="lista">
          {reportes.map((r) => (
            <li key={r.id}>
              <button className={`item ${sel?.id === r.id ? 'activa' : ''}`} onClick={() => setSel(r)}>
                <span className="barra-nivel" style={{ background: COLOR_NIVEL[r.nivel] }} />
                <span className="item-cuerpo">
                  <span className="item-titulo">
                    <strong>{r.prioridad}</strong> {TIPOS[r.tipo]?.icono} {tipoLabel(r.tipo)}
                  </span>
                  <span className="tenue">{r.distrito} · {fecha(r.creado_en)} · <span className={`estado e-${r.estado}`}>{ESTADOS[r.estado]}</span>{r.brigada ? ` · ${r.brigada}` : ''}</span>
                  <span className="tenue">{(r.motivos || []).slice(0, 3).join(' · ')}</span>
                </span>
              </button>
            </li>
          ))}
          {reportes.length === 0 && <li className="tenue">Sin reportes para estos filtros.</li>}
        </ol>
        <div className="columna-derecha">
          <div className="mapa-tablero">
            <MapContainer center={CENTRO_PIURA} zoom={12}>
              <CapaBase />
              <CapaZonasCriticas />
              {reportes.map((r) => (
                <MarcadorReporte key={r.id} r={r} seleccionado={sel?.id === r.id} onClick={setSel} />
              ))}
              <CentrarEn reporte={sel} />
            </MapContainer>
            <Leyenda />
          </div>
          {sel ? <Detalle r={sel} clave={clave} onActualizado={onActualizado} /> : <p className="tenue centro">Selecciona un reporte de la lista o del mapa.</p>}
        </div>
      </div>
      <PanelNecesidades resumen={resumen} />
    </section>
  )
}
