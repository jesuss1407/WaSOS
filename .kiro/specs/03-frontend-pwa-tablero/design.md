# Diseño: 03 Frontend y tablero

## Rutas (react-router-dom, BrowserRouter)
| Ruta | Componente | Requisitos |
|---|---|---|
| `/` | `pages/Reportar.jsx` | R1.1-R1.6 |
| `/mapa` | `pages/Mapa.jsx` | R2.1-R2.3 |
| `/tablero` | `pages/Tablero.jsx` (`Acceso`, `Detalle`, `PanelNecesidades`) | R3.1-R3.5 |

Amplify Hosting reescribe toda ruta sin extensión a `/index.html` (regla 200 creada con `aws amplify create-app`).

## Módulos
- `src/api.js`: único lugar con rutas HTTP. `api.crearUpload`, `api.subirFoto`, `api.crearReporte`, `api.listarReportes`,
  `api.confirmar`, `api.admin.{listar, actualizar, resumen, parteSituacional, exportarCsv}`. Lanza `ErrorApi(mensaje, status, detalles)`.
- `src/lib/comprimirImagen.js`: `comprimirImagen(file, {maxLado: 1280, maxBytes: 300 KB})` con bucle calidad/escala.
- `src/lib/colaOffline.js`: `enviarReporte(datos, blob, fotoKey?, onFotoKey)`, `encolar`, `procesarCola`, `iniciarReintentos`.
  Guarda `foto_key` cuando la subida ya ocurrió: el backend usa ese uuid como id, así el reintento es idempotente.
- `src/lib/geo.js`: `haversineM`, `distritoMasCercano`, `dentroDeRegion`.
- `src/catalogos.js`: enums y etiquetas, importa `data/distritos_piura.json` y `data/zonas_criticas.json`.
- `src/components/Mapas.jsx`: `CapaBase` (OSM), `CapaZonasCriticas`, `MarcadorReporte` (CircleMarker por nivel), `Leyenda`, `Nivel`.

## Secuencia de envío (Reportar)
```
validar faltantes → si offline: encolar
enviarReporte: POST /uploads → PUT S3 → POST /reportes → pantalla de resultado
error 4xx → mensaje por campo · error de red / 5xx → encolar (con foto_key si ya subió)
```

## Decisiones
- `CircleMarker` en vez de íconos PNG: sin problemas de assets y color por nivel.
- Clave admin en `sessionStorage` (se borra al cerrar la pestaña); nunca en el bundle.
- Sin service worker en el MVP: la cola offline cubre el caso crítico (enviar sin señal) con menos riesgo.
- `VITE_API_URL` en `.env.production`; la API restringe CORS al dominio de Amplify y a `localhost:5173`.

## Pruebas
- Prueba de navegador (Playwright, Chromium headless, viewport 412×915 con GPS simulado): foto → GPS → tipo →
  necesidades → consentimiento → envío → resultado con motivos; mapa con marcadores; tablero con clave, lista y detalle.
  Resultado del 30-oct: sin errores de consola.
