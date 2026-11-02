// Reglas geográficas del cliente. Funciones puras (sin imports) para poder probarlas con `node --test`.
// Deben coincidir con backend/src/dominio/geo.py y catalogos.py (lo verifica backend/tests/test_geo.py).

export const BBOX = { latMin: -6.4, latMax: -4.0, lonMin: -81.4, lonMax: -79.2 }

export const dentroDeRegion = (lat, lon) =>
  Number.isFinite(lat) && Number.isFinite(lon) &&
  lat >= BBOX.latMin && lat <= BBOX.latMax && lon >= BBOX.lonMin && lon <= BBOX.lonMax

export function haversineM(lat1, lon1, lat2, lon2) {
  const rad = (g) => (g * Math.PI) / 180
  const dp = rad(lat2 - lat1)
  const dl = rad(lon2 - lon1)
  const a = Math.sin(dp / 2) ** 2 + Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(dl / 2) ** 2
  return 2 * 6371000 * Math.asin(Math.sqrt(a))
}

// Distrito de la provincia con el centroide más cercano; "Otro (región)" si está a más de maxKm.
// `distritos`: [{ nombre, lat, lon }] (data/distritos_piura.json).
export function distritoMasCercano(lat, lon, distritos, maxKm = 25) {
  let mejor = null
  let mejorD = Infinity
  for (const d of distritos) {
    const dist = haversineM(lat, lon, d.lat, d.lon)
    if (dist < mejorD) {
      mejor = d.nombre
      mejorD = dist
    }
  }
  return mejor !== null && mejorD <= maxKm * 1000 ? mejor : 'Otro (región)'
}
