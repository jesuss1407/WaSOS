// Pruebas con el runner nativo de Node: `npm test`
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { BBOX, dentroDeRegion, distritoMasCercano, haversineM } from './geo.js'

const DISTRITOS = JSON.parse(readFileSync(new URL('../../../data/distritos_piura.json', import.meta.url), 'utf8'))

test('distrito autodetectado por cercanía al centroide', () => {
  const casos = [
    [-5.1953, -80.6301, 'Piura'],
    [-5.199, -80.612, 'Castilla'],
    [-5.184, -80.6738, 'Veintiséis de Octubre'],
    [-5.2659, -80.6757, 'Catacaos'],
    [-5.32, -80.664, 'Cura Mori'],
    [-4.9353, -80.3424, 'Tambogrande'],
    [-4.9039, -80.6853, 'Otro (región)'], // Sullana: a más de 25 km
    [-5.375, -79.605, 'Otro (región)'], // Canchaque
  ]
  for (const [lat, lon, esperado] of casos) assert.equal(distritoMasCercano(lat, lon, DISTRITOS), esperado)
})

test('cada centroide se detecta a sí mismo', () => {
  for (const d of DISTRITOS) assert.equal(distritoMasCercano(d.lat, d.lon, DISTRITOS), d.nombre)
})

test('bbox de la región Piura: bordes incluidos, fuera rechazado', () => {
  assert.deepEqual(BBOX, { latMin: -6.4, latMax: -4.0, lonMin: -81.4, lonMax: -79.2 })
  assert.ok(dentroDeRegion(-4.0, -79.2) && dentroDeRegion(-6.4, -81.4))
  assert.ok(!dentroDeRegion(-3.99, -80.6) && !dentroDeRegion(-5.2, -79.19))
  assert.ok(!dentroDeRegion(-12.05, -77.04)) // Lima
  assert.ok(!dentroDeRegion(NaN, -80.6))
})

test('haversine: 0.001° de latitud ≈ 111 m', () => {
  const d = haversineM(-5.19, -80.63, -5.191, -80.63)
  assert.ok(d > 105 && d < 117, `${d}`)
})
