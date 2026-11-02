// Re-codifica la foto en un canvas: JPEG <= 300 KB y sin metadatos EXIF (incluido el GPS de la cámara).
async function cargar(file) {
  if ('createImageBitmap' in window) {
    try {
      return await createImageBitmap(file, { imageOrientation: 'from-image' })
    } catch {
      /* algunos navegadores no aceptan opciones: usamos <img> */
    }
  }
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve(img)
    }
    img.onerror = () => reject(new Error('No se pudo leer la imagen'))
    img.src = url
  })
}

const aBlob = (canvas, calidad) =>
  new Promise((resolve) => canvas.toBlob((b) => resolve(b), 'image/jpeg', calidad))

export async function comprimirImagen(file, { maxLado = 1280, maxBytes = 300 * 1024 } = {}) {
  const img = await cargar(file)
  const ancho = img.width
  const alto = img.height
  let escala = Math.min(1, maxLado / Math.max(ancho, alto))
  let calidad = 0.82
  const canvas = document.createElement('canvas')
  let blob = null
  for (let i = 0; i < 10; i++) {
    canvas.width = Math.round(ancho * escala)
    canvas.height = Math.round(alto * escala)
    canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height)
    blob = await aBlob(canvas, calidad)
    if (blob && blob.size <= maxBytes) break
    if (calidad > 0.55) calidad -= 0.1
    else escala *= 0.8
  }
  if (!blob) throw new Error('No se pudo comprimir la imagen')
  return blob
}

export const blobADataUrl = (blob) =>
  new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => resolve(r.result)
    r.onerror = reject
    r.readAsDataURL(blob)
  })

export async function dataUrlABlob(dataUrl) {
  const r = await fetch(dataUrl)
  return r.blob()
}
