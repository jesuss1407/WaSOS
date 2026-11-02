# Tareas: 01 Backend API

- [x] 1. Template SAM con S3 privado, DynamoDB on-demand, HTTP API (CORS + throttling) y Lambda Python 3.12
  - `backend/template.yaml`
  - _Requisitos: R1.3, R6.1_
- [x] 2. Router único por `routeKey`, helpers HTTP y verificación `X-Admin-Key` (`hmac.compare_digest`)
  - `backend/src/app.py` → `RUTAS`, `_verificar_admin` · test: `test_admin_sin_clave_o_con_clave_incorrecta_401`, `test_contrato.py`
  - _Requisitos: R4.1_
- [x] 3. `POST /uploads` con URL prefirmada PUT y `foto_key` validable
  - `rutas/publicas.py` → `crear_upload` · test: `test_uploads_entrega_url_prefirmada_y_solo_acepta_jpeg`
  - _Requisitos: R1.1, R1.2_
- [x] 4. Validación de `POST /reportes`: bbox de Piura (lat −6,4…−4,0; lon −81,4…−79,2), enums, consentimiento, longitudes
  - `dominio/validacion.py` → `validar_reporte` · tests: `test_geo.py::test_bbox_region_piura` (bordes incluidos),
    `test_coordenadas_no_numericas_rechazadas`, `test_validacion.py::test_reporte_invalido`,
    `test_api_integracion.py::test_reporte_fuera_de_piura_400_sin_guardar`
  - _Requisitos: R2.2_
- [x] 5. `POST /reportes`: lectura de la foto, clasificación, prioridad, guardado idempotente
  - `rutas/publicas.py` → `crear_reporte` · tests: `test_reenviar_el_mismo_foto_key_no_duplica`,
    `test_reporte_sin_foto_subida_400`, `test_si_bedrock_falla_el_reporte_se_guarda_con_fallback`
  - _Requisitos: R2.1, R2.3, R2.4_
- [x] 6. `GET /reportes` público sin datos sensibles
  - `rutas/servicio.py` → `a_publico` · tests: `test_mapa_publico_sin_datos_sensibles_y_coordenadas_redondeadas`,
    `test_mapa_publico_oculta_fotos_no_validas_y_descartados`
  - _Requisitos: R3.1_
- [x] 7. Endpoints admin: lista con `foto_url`, PATCH de estado con historial y bloqueo optimista, resumen
  - `rutas/admin.py` → `listar`, `actualizar`, `resumen`; `datos/repositorio.py` → `cambiar_estado`
    (`ConditionExpression="estado = :actual"` → `ConflictoEstado` → 409)
  - tests: `test_flujo_de_estados_completo_con_historial`, `test_transicion_no_permitida_409`,
    `test_en_atencion_exige_brigada_400`, `test_edicion_concurrente_409_no_pisa_el_cambio_ajeno`,
    `test_cambiar_estado_con_estado_esperado_viejo_lanza_conflicto`, `test_resumen_agrega_necesidades_por_distrito`
  - _Requisitos: R4.2, R4.3, R4.4_
- [x] 8. S1 confirmar y S2 CSV
  - S1: `repositorio.incrementar_confirmaciones` (`ADD` atómico) + `actualizar_prioridad` condicionada a
    `confirmaciones = :c` · tests: `test_confirmar_suma_y_recalcula_prioridad`,
    `test_confirmacion_retrasada_no_pisa_la_prioridad_mas_reciente`, `test_confirmar_reporte_descartado_409`
  - S2: `rutas/admin.py` → `exportar_csv` + `_celda` (antepone `'` a textos que empiezan con `= + - @`, tab o CR)
    · tests: `test_admin_csv.py`, `test_export_csv_neutraliza_formulas_y_conserva_numeros`
  - _Requisitos: R5.1, R5.2_
- [x] 9. Script de despliegue y primer deploy en us-east-1
  - `scripts/deploy_backend.sh`
  - _Requisitos: R6.2_
- [x] 10. Seed de datos demo y prueba E2E contra la API real
  - `scripts/seed.py`, `scripts/smoke_test.py`
  - _Requisitos: R2.1, R3.1_
- [x] 11. Tests de integración con DynamoDB/S3 simulados (moto) y hook de pytest al guardar
  - `backend/tests/test_api_integracion.py`, `backend/tests/conftest.py`, `.kiro/hooks/pytest-backend.json`
  - _Requisitos: R2.1-R5.2_
