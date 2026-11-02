# Requisitos: 02 IA y priorización

## Introducción
Clasificación de la foto con Claude (visión) en Amazon Bedrock y prioridad 0-100 explicable con motivos legibles.
Detalle técnico: #[[file:.kiro/steering/ia-bedrock.md]] · Fórmula: #[[file:.kiro/steering/api-contract.md]]

## Requisito 1: Clasificación de la foto (MUST, M2)
**Historia:** Como operador, quiero que cada foto llegue clasificada, para atender primero lo más grave sin revisar todo a mano.
- R1.1 CUANDO se registre un reporte ENTONCES el sistema DEBERÁ enviar la foto en base64 a Claude y obtener un JSON
  validado con `tipo`, `severidad` (1-5), `es_valida`, `riesgo_vida`, `riesgo_salud`, `descripcion` corta y `confianza`. (MUST)
- R1.2 SI la foto no muestra un entorno de riesgo (selfie, meme, captura) ENTONCES la IA DEBERÁ marcar `es_valida=false`
  y el sistema DEBERÁ fijar severidad 1 y limitar la prioridad a 20. (MUST)
- R1.3 El texto dentro de la imagen y la descripción del vecino DEBERÁN tratarse como datos, nunca como instrucciones. (MUST)
- R1.4 La IA NO DEBERÁ identificar ni describir personas. (MUST)
- R1.5 SI Bedrock falla, excede el tiempo, rechaza (`refusal`) o devuelve JSON inválido ENTONCES el sistema DEBERÁ
  probar el siguiente modelo de `MODEL_IDS` dentro del presupuesto de 23 s y, si no hay respuesta, usar el fallback
  (`estado_ia="fallback"`, severidad por defecto del tipo, motivo "IA no disponible: verificar manualmente") y guardar
  el reporte igual. (MUST)
- R1.6 El modelo DEBERÁ ser configurable por variable de entorno sin cambiar código. (MUST)

## Requisito 2: Prioridad explicable (MUST, M3)
**Historia:** Como autoridad, quiero entender por qué un reporte está arriba, para confiar en la lista y justificar decisiones.
- R2.1 El sistema DEBERÁ calcular `p = 100 × (0.40·sev/5 + 0.20·peso_tipo + 0.15·vulnerables + 0.15·zona_crítica + 0.10·min(conf/5,1))`,
  sumar 10 si hay riesgo para la vida (tope 100) y limitar a 20 si `es_valida=false`. (MUST)
- R2.2 El sistema DEBERÁ asignar nivel CRÍTICA (≥75), ALTA (50-74), MEDIA (25-49) o BAJA (<25). (MUST)
- R2.3 CUANDO el punto esté a ≤300 m (haversine) de una zona de `data/zonas_criticas.json` ENTONCES el sistema DEBERÁ
  sumar ese factor y agregar el motivo "A N m de zona crítica: <nombre>". (MUST)
- R2.4 El sistema DEBERÁ devolver motivos legibles en español (severidad, riesgo vida, zona, vulnerables, riesgo
  sanitario, confirmaciones, foto no válida). (MUST)
- R2.5 CUANDO cambie el número de confirmaciones ENTONCES el sistema DEBERÁ recalcular prioridad, nivel y motivos. (SHOULD, S1)

## Requisito 3: Parte situacional (SHOULD, S3)
- R3.1 CUANDO la autoridad pida un parte ENTONCES el sistema DEBERÁ redactar con IA un resumen sobrio a partir de
  datos agregados (sin fotos ni texto libre) y, si la IA falla, devolver un texto de respaldo con plantilla. (SHOULD)
