// Cliente de la API. Contrato: .kiro/steering/api-contract.md
export const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

export class ErrorApi extends Error {
  constructor(mensaje, status, detalles) {
    super(mensaje)
    this.status = status
    this.detalles = detalles
  }
}

const qs = (filtros = {}) => {
  const p = new URLSearchParams(Object.entries(filtros).filter(([, v]) => v))
  const s = p.toString()
  return s ? `?${s}` : ''
}

async function solicitar(ruta, { method = 'GET', body, adminKey } = {}) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (adminKey) headers['X-Admin-Key'] = adminKey
  const resp = await fetch(API_URL + ruta, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  const texto = await resp.text()
  let datos = null
  try {
    datos = texto ? JSON.parse(texto) : null
  } catch {
    datos = texto
  }
  if (!resp.ok) throw new ErrorApi(datos?.error || `Error ${resp.status}`, resp.status, datos?.detalles)
  return datos
}

export const api = {
  salud: () => solicitar('/health'),
  items: {
    crear: (value) => solicitar('/items', { method: 'POST', body: { value } }),
    obtener: (id) => solicitar(`/items/${id}`),
    listar: () => solicitar('/items'),
  },
  jobs: {
    crear: (input) => solicitar('/jobs', { method: 'POST', body: { input } }),
    obtener: (jobId) => solicitar(`/jobs/${jobId}`),
  },
  crearUpload: () => solicitar('/uploads', { method: 'POST', body: { content_type: 'image/jpeg' } }),
  async subirFoto(uploadUrl, blob) {
    const r = await fetch(uploadUrl, { method: 'PUT', headers: { 'Content-Type': 'image/jpeg' }, body: blob })
    if (!r.ok) throw new ErrorApi('No se pudo subir la foto', r.status)
  },
  crearReporte: (datos) => solicitar('/reportes', { method: 'POST', body: datos }),
  listarReportes: (filtros) => solicitar('/reportes' + qs(filtros)),
  confirmar: (id) => solicitar(`/reportes/${id}/confirmar`, { method: 'POST' }),
  admin: {
    listar: (key, filtros) => solicitar('/admin/reportes' + qs(filtros), { adminKey: key }),
    actualizar: (key, id, cambio) => solicitar(`/admin/reportes/${id}`, { method: 'PATCH', body: cambio, adminKey: key }),
    resumen: (key) => solicitar('/admin/resumen', { adminKey: key }),
    parteSituacional: (key, distrito) =>
      solicitar('/admin/parte-situacional', { method: 'POST', body: distrito ? { distrito } : {}, adminKey: key }),
    async exportarCsv(key) {
      const r = await fetch(API_URL + '/admin/export.csv', { headers: { 'X-Admin-Key': key } })
      if (!r.ok) throw new ErrorApi('No se pudo exportar', r.status)
      return r.blob()
    },
  },
}
