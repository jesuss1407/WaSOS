# Requisitos: 04 Insignias técnicas de la Kiro IAthon

## Introducción
Rutas públicas que exige el portal de la Kiro IAthon para otorgar las insignias "API viva", "Persistencia" y
"Asíncrono o agente". Viven en la misma Lambda y HTTP API de WaSOS (spec 01), sin tocar el flujo de reportes.
Fuente: las cartas de cada insignia en el portal (30-oct-2026). Contrato: #[[file:.kiro/steering/api-contract.md]]
Id público del equipo: `T051`. Solo datos simulados: los verificadores envían valores aleatorios, nunca datos personales.

## Requisito 1: API viva (MUST)
**Historia:** Como verificador del portal, quiero comprobar que la API del equipo responde, para otorgar la insignia.
- R1.1 CUANDO se llame `GET /health` sin autenticación ENTONCES el sistema DEBERÁ responder 200 con
  `{"status":"ok","team":"T051"}` y `Content-Type: application/json`. (MUST)
- R1.2 El valor de `team` DEBERÁ venir del parámetro SAM `TeamId` (env `TEAM_ID`), nunca escrito en el código. (MUST)
- R1.3 SI se intenta desplegar sin `TEAM_ID` ENTONCES `scripts/deploy_backend.sh` DEBERÁ fallar antes de llamar a SAM. (MUST)

## Requisito 2: Persistencia (MUST)
**Historia:** Como verificador, quiero crear un ítem y volver a leerlo, para comprobar que la API guarda datos.
- R2.1 CUANDO llegue `POST /items` con `{"value": str}` (1 a 1024 caracteres) ENTONCES el sistema DEBERÁ guardarlo en
  `ItemsTable` (env `TABLE_NAME`) y responder 201 con `{"id","value"}`. (MUST)
- R2.2 SI `value` falta, no es texto, está vacío, supera 1024 caracteres o el cuerpo no es un objeto JSON ENTONCES el
  sistema DEBERÁ responder 400 sin guardar nada. (MUST)
- R2.3 CUANDO se llame `GET /items/{id}` ENTONCES el sistema DEBERÁ responder 200 con `{"id","value"}`; SI no existe o
  el id no es un ítem ENTONCES 404. (MUST)
- R2.4 CUANDO se llame `GET /items` ENTONCES el sistema DEBERÁ devolver un arreglo de hasta 100 ítems, los más recientes
  primero, recorriendo todas las páginas del scan, de modo que el ítem recién creado siempre aparezca. (MUST)

## Requisito 3: Asíncrono o agente (MUST)
**Historia:** Como verificador, quiero encolar un trabajo y consultarlo, para comprobar procesamiento asíncrono.
- R3.1 CUANDO llegue `POST /jobs` con `{"input": str}` (1 a 1024) ENTONCES el sistema DEBERÁ responder 202 de inmediato
  con `{"jobId"}` y guardar el trabajo en `ItemsTable`. (MUST)
- R3.2 CUANDO se llame `GET /jobs/{jobId}` ANTES de 2 s desde la creación ENTONCES el sistema DEBERÁ responder 200 con
  `status="queued"` y `output=null`. (MUST)
- R3.3 CUANDO se llame `GET /jobs/{jobId}` desde 2 s después de la creación ENTONCES el sistema DEBERÁ responder
  `status="done"` y `output` = `input` invertido carácter por carácter (`"abc1"` → `"1cba"`), siempre antes de 12 s. (MUST)
- R3.4 SI el trabajo no existe o el id es de un ítem ENTONCES 404; SI `input` es inválido ENTONCES 400 sin guardar. (MUST)

## Requisito 4: Convivencia con WaSOS (MUST)
- R4.1 Los trabajos NO DEBERÁN aparecer en `GET /items` ni ser legibles por `GET /items/{id}`. (MUST)
- R4.2 Ítems y trabajos NO DEBERÁN guardarse en la tabla `Reportes` ni aparecer en el mapa o el tablero. (MUST)
- R4.3 La Lambda DEBERÁ tener sobre `ItemsTable` solo `PutItem`, `GetItem` y `Scan`. (MUST)
- R4.4 Las rutas nuevas DEBERÁN estar en el contrato, en `RUTAS`, en `template.yaml` y en `api.js`. (MUST)
