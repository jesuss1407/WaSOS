# Requisitos: 01 Backend API

## Introducción
API serverless (AWS SAM, Python 3.12) que recibe reportes ciudadanos con foto, los guarda en DynamoDB y S3 privado,
y expone el mapa público y el tablero protegido. Contrato: #[[file:.kiro/steering/api-contract.md]]

## Requisito 1: Subida segura de la foto (MUST)
**Historia:** Como vecino, quiero subir la foto directamente a la nube, para que el envío sea rápido con mala señal.
- R1.1 CUANDO el cliente llame `POST /uploads` con `content_type="image/jpeg"` ENTONCES el sistema DEBERÁ devolver
  `upload_url` (PUT prefirmado de 5 min) y `foto_key` con formato `fotos/{uuid}.jpg`. (MUST)
- R1.2 SI `content_type` no es `image/jpeg` ENTONCES el sistema DEBERÁ responder 400. (MUST)
- R1.3 El bucket DEBERÁ ser privado, cifrado, con CORS solo para el dominio del frontend y deny a tráfico no HTTPS. (MUST)

## Requisito 2: Registro del reporte (MUST)
**Historia:** Como vecino, quiero enviar mi reporte sin registrarme, para alertar a las autoridades en segundos.
- R2.1 CUANDO llegue `POST /reportes` válido ENTONCES el sistema DEBERÁ clasificar la foto (spec 02), calcular la
  prioridad, guardar el reporte con estado `nuevo` y devolver 201 con `ReportePublico` y `motivos`. (MUST)
- R2.2 SI lat/lon están fuera del bbox de Piura, `consentimiento` no es `true`, `tipo`/`necesidades`/`distrito` no
  pertenecen a sus enums o la descripción supera 500 caracteres ENTONCES el sistema DEBERÁ responder 400 con `detalles` por campo. (MUST)
- R2.3 SI la foto no existe en S3 ENTONCES 400; SI pesa más de 1,5 MB ENTONCES 413. (MUST)
- R2.4 CUANDO se reenvíe el mismo `foto_key` (reintento offline) ENTONCES el sistema DEBERÁ devolver el reporte
  existente sin duplicarlo. (SHOULD)

## Requisito 3: Mapa público (MUST)
- R3.1 CUANDO se llame `GET /reportes?distrito&nivel` ENTONCES el sistema DEBERÁ devolver solo reportes con
  `es_valida=true` y estado distinto de `descartado`, ordenados por prioridad, sin foto, sin `foto_key`, sin descripción
  libre y con coordenadas a 4 decimales. (MUST)

## Requisito 4: Tablero protegido (MUST)
**Historia:** Como autoridad, quiero ver los reportes priorizados con foto y gestionar su atención.
- R4.1 SI una ruta `/admin/*` no trae `X-Admin-Key` correcta ENTONCES el sistema DEBERÁ responder 401. (MUST)
- R4.2 CUANDO se llame `GET /admin/reportes` ENTONCES el sistema DEBERÁ devolver la lista filtrable por distrito,
  tipo, estado y nivel, ordenada por prioridad, con `foto_url` prefirmada de 15 min y `transiciones` permitidas. (MUST)
- R4.3 CUANDO se llame `PATCH /admin/reportes/{id}` ENTONCES el sistema DEBERÁ aplicar solo transiciones válidas
  (`nuevo→verificado→en_atencion→resuelto`, `descartado` desde cualquier estado activo), exigir brigada para
  `en_atencion`, registrar historial y responder 409 ante transición inválida o edición concurrente. (MUST)
- R4.4 CUANDO se llame `GET /admin/resumen` ENTONCES el sistema DEBERÁ devolver conteos por estado y nivel y, por
  distrito, reportes activos, vulnerables y necesidades agregadas. (MUST)

## Requisito 5: Extras (SHOULD)
- R5.1 CUANDO un vecino llame `POST /reportes/{id}/confirmar` ENTONCES el sistema DEBERÁ sumar 1 confirmación de forma
  atómica y recalcular prioridad y motivos; SI dos confirmaciones llegan a la vez ENTONCES la prioridad guardada DEBERÁ
  corresponder al conteo más reciente; SI el reporte no está activo ENTONCES 409. (S1)
- R5.2 CUANDO se llame `GET /admin/export.csv` ENTONCES el sistema DEBERÁ devolver un CSV UTF-8 con BOM y celdas de
  texto protegidas contra inyección de fórmulas. (S2)

## Requisito 6: Operación (MUST)
- R6.1 La API DEBERÁ tener throttling 20 rps / burst 50 y CORS restringido. (MUST)
- R6.2 El despliegue DEBERÁ ser reproducible con un script (`scripts/deploy_backend.sh`). (MUST)
- R6.3 Los logs NO DEBERÁN contener datos personales ni la descripción del vecino. (MUST)
