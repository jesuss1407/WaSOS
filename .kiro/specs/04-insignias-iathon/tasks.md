# Tareas: 04 Insignias técnicas de la Kiro IAthon

- [x] 1. Parámetro `TeamId` en `template.yaml`, env `TEAM_ID` y `TEAM_ID` obligatorio en `scripts/deploy_backend.sh`
  - `backend/template.yaml` → `Parameters.TeamId`; `scripts/deploy_backend.sh` → `${TEAM_ID:?...}`
  - _Requisitos: R1.2, R1.3_
- [x] 2. `GET /health` pública
  - `rutas/publicas.py` → `salud`; `app.py` → `RUTAS["GET /health"]`; evento `Salud` · test: `test_health.py::test_health`
  - _Requisitos: R1.1_
- [x] 3. Fila de `/health` en el contrato, `api.salud()` en `api.js` y `test_contrato.py` actualizado
  - `.kiro/steering/api-contract.md`, `frontend/src/api.js` · test: `test_rutas_contrato_app_y_template_alineadas`
  - _Requisitos: R4.4_
- [x] 4. Desplegar con `TEAM_ID=T051` y verificar `curl -s <ApiUrl>/health` → `{"status": "ok", "team": "T051"}`
  - _Requisitos: R1.1_
- [x] 5. `ItemsTable` (on-demand, PK `id`), env `TABLE_NAME`, salida `TablaItems` y política mínima
  - `backend/template.yaml` → `ItemsTable`, `ItemsSoloCrearLeerListar`
  - _Requisitos: R2.1, R4.2, R4.3_
- [x] 6. Capa de datos con `TABLE` reemplazable y listado que recorre todas las páginas
  - `datos/items.py` → `guardar`, `obtener`, `listar` · test:
    `test_listar_pagina_el_scan_y_devuelve_hasta_100_con_el_mas_reciente`
  - _Requisitos: R2.4_
- [x] 7. Rutas `POST /items`, `GET /items/{id}`, `GET /items` con validación de `value`
  - `rutas/items.py` · tests: `test_crear_obtener_y_listar_item`, `test_item_inexistente_404`,
    `test_value_invalido_400_sin_guardar`
  - _Requisitos: R2.1, R2.2, R2.3_
- [x] 8. Lógica pura del trabajo: invertir la entrada y calcular `queued`/`done` según `listo_en`
  - `dominio/trabajos.py` → `procesar`, `estado` · test: `test_procesar_invierte_caracter_por_caracter`
  - _Requisitos: R3.3_
- [x] 9. Rutas `POST /jobs` (202) y `GET /jobs/{jobId}` resueltas al leer
  - `rutas/trabajos.py` · tests: `test_trabajo_pasa_de_queued_a_done_con_la_entrada_invertida`,
    `test_trabajo_inexistente_o_id_de_item_404`, `test_input_invalido_400_sin_guardar`
  - _Requisitos: R3.1, R3.2, R3.3, R3.4_
- [x] 10. Separar ítems de trabajos en `/items` (misma tabla)
  - `rutas/items.py` → `_es_item`; `datos/items.py` → filtro por `value` · test: `test_trabajos_de_jobs_no_salen_por_items`
  - _Requisitos: R4.1_
- [x] 11. Contrato, `RUTAS`, eventos SAM y `api.items` / `api.jobs` alineados (15 rutas)
  - `test_contrato.py` acepta `${jobId}` en `api.js` · hook `revisar-contrato-api.json`
  - _Requisitos: R4.4_
- [x] 12. Desplegar y simular a los verificadores contra la API real
  - `/items`: 201 → 200 → presente en la lista; `/jobs`: `queued` a 0,1 y 1,7 s, `done` a 3,2 s con la salida correcta
  - _Requisitos: R2.1-R3.4_
- [x] 13. Documentar en README (secciones de cada insignia) y en esta spec
  - _Requisitos: R4.4_
