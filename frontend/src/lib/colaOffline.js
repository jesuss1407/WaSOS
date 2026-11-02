// S4: cola offline en localStorage. Guarda la foto (<=300 KB en base64) y los datos; reintenta al volver la conexión.
// Idempotencia: cuando la foto ya se subió se conserva su foto_key, y el backend usa ese uuid como id del reporte.
import { api } from '../api'
import { blobADataUrl, dataUrlABlob } from './comprimirImagen'

const CLAVE = 'alerta-piura:cola'

const leer = () => {
  try {
    return JSON.parse(localStorage.getItem(CLAVE) || '[]')
  } catch {
    return []
  }
}
const escribir = (cola) => {
  localStorage.setItem(CLAVE, JSON.stringify(cola))
  window.dispatchEvent(new Event('cola-cambio'))
}

export const pendientes = () => leer().length

// Sube la foto (si hace falta) y crea el reporte. onFotoKey permite guardar el progreso.
export async function enviarReporte(datos, fotoBlob, fotoKey, onFotoKey) {
  let key = fotoKey
  if (!key) {
    const { upload_url, foto_key } = await api.crearUpload()
    await api.subirFoto(upload_url, fotoBlob)
    key = foto_key
    onFotoKey?.(key)
  }
  return api.crearReporte({ ...datos, foto_key: key })
}

export async function encolar(datos, fotoBlob, fotoKey) {
  const cola = leer()
  cola.push({ local_id: crypto.randomUUID(), datos, foto: await blobADataUrl(fotoBlob), foto_key: fotoKey || null, creado: Date.now() })
  try {
    escribir(cola)
  } catch {
    throw new Error('No hay espacio para guardar el reporte sin conexión')
  }
}

let procesando = false
export async function procesarCola() {
  if (procesando || !navigator.onLine) return 0
  procesando = true
  let enviados = 0
  try {
    for (const item of leer()) {
      try {
        const blob = await dataUrlABlob(item.foto)
        await enviarReporte(item.datos, blob, item.foto_key, (k) => {
          escribir(leer().map((i) => (i.local_id === item.local_id ? { ...i, foto_key: k } : i)))
        })
        escribir(leer().filter((i) => i.local_id !== item.local_id))
        enviados++
      } catch (e) {
        // 4xx (datos inválidos) no se reintenta; errores de red o 5xx sí
        if (e.status && e.status >= 400 && e.status < 500) {
          escribir(leer().filter((i) => i.local_id !== item.local_id))
        } else break
      }
    }
  } finally {
    procesando = false
  }
  return enviados
}

export function iniciarReintentos() {
  window.addEventListener('online', () => procesarCola())
  setInterval(() => procesarCola(), 60_000)
  procesarCola()
}
