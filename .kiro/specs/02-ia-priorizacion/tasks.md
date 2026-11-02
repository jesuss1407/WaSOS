# Tareas: 02 IA y priorización

- [x] 1. `scripts/check_bedrock.py`: acceso y latencia por modelo (Mantle)
  - _Requisitos: R1.6_
- [x] 2. Schema `ClasificacionIA` y prompt de sistema (tipos, severidad, validez, datos ≠ instrucciones, sin personas)
  - `backend/src/ia/clasificador.py` → `ClasificacionIA`, `SYSTEM_PROMPT`
  - _Requisitos: R1.1-R1.4_
- [x] 3. `clasificar()` con cadena de modelos, presupuesto de tiempo, `refusal` y fallback
  - `clasificador.py` → `clasificar`, `fallback` · test: `test_api_integracion.py::test_si_bedrock_falla_el_reporte_se_guarda_con_fallback`
  - _Requisitos: R1.5, R1.6_
- [x] 4. `calcular_prioridad()` pura + niveles + motivos
  - `backend/src/dominio/prioridad.py` · tests: `test_prioridad.py` (fórmula, tope 100, foto inválida ≤20, umbrales, motivos)
  - _Requisitos: R2.1, R2.2, R2.4_
- [x] 5. Distancia a zonas críticas (haversine ≤300 m) con `data/zonas_criticas.json`
  - `backend/src/dominio/geo.py` → `haversine_m`, `zona_critica_cercana` · tests: `test_haversine_aproximado`,
    `test_zona_critica_dentro_y_fuera_del_radio`
  - _Requisitos: R2.3_
- [x] 6. Recálculo al confirmar (S1), sin que una escritura tardía deje una prioridad vieja
  - `rutas/publicas.py` → `confirmar`; `repositorio.actualizar_prioridad` (condición `confirmaciones = :c`)
    · test: `test_confirmacion_retrasada_no_pisa_la_prioridad_mas_reciente`
  - _Requisitos: R2.5_
- [x] 7. Parte situacional IA con respaldo (S3)
  - `backend/src/ia/parte_situacional.py` → `generar_parte`
  - _Requisitos: R3.1_
