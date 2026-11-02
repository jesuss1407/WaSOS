# Tareas: 03 Frontend y tablero

- [x] 1. Proyecto Vite + React, router, cabecera, pie con números de emergencia, manifest
  - _Requisitos: R4.1_
- [x] 2. `api.js` y `catalogos.js` alineados con `api-contract.md`
  - test: `backend/tests/test_contrato.py` (rutas de `api.js` y enums de `catalogos.js`)
  - _Requisitos: R1.4, R3.2_
- [x] 3. Compresión de foto en canvas (≤300 KB, sin EXIF)
  - `frontend/src/lib/comprimirImagen.js`
  - _Requisitos: R1.1_
- [x] 4. Reportar: GPS + pin arrastrable dentro del bbox de Piura + distrito autodetectado + formulario + consentimiento
  - `frontend/src/lib/geo.js` → `dentroDeRegion` (GPS, toque y arrastre del pin) y `distritoMasCercano`
    (centroide más cercano de `data/distritos_piura.json`; a más de 25 km → "Otro (región)"), usados en `pages/Reportar.jsx`
  - tests: `frontend/src/lib/geo.test.js` (`npm test`), `backend/tests/test_geo.py::test_bbox_y_radio_del_frontend_iguales_al_backend`
  - _Requisitos: R1.2, R1.3, R1.4_
- [x] 5. Pantalla de resultado con prioridad, motivos, tipo sugerido por IA y números de emergencia
  - _Requisitos: R1.5_
- [x] 6. Cola offline con reintento idempotente (S4)
  - `frontend/src/lib/colaOffline.js` (conserva `foto_key`; el backend usa ese uuid como id)
  - _Requisitos: R1.6_
- [x] 7. Mapa público con niveles, zonas críticas, filtros y "Yo también lo veo" (S1)
  - _Requisitos: R2.1, R2.2, R2.3_
- [x] 8. Tablero: acceso con clave, KPIs, lista, mapa, detalle con foto y cambio de estado
  - Muestra el 409 de edición concurrente ("El reporte cambió mientras lo editaba; recargue")
  - _Requisitos: R3.1, R3.2, R3.3_
- [x] 9. Panel de necesidades por distrito, exportar CSV (S2) y parte situacional IA (S3)
  - _Requisitos: R3.4, R3.5_
- [x] 10. Deploy en Amplify Hosting con reescritura SPA
  - `scripts/deploy_frontend.sh`
  - _Requisitos: R4.2_
