---
inclusion: always
---
# Producto: WaSOS (antes "Alerta Piura")

Nombre visible: **WaSOS**. Los recursos de AWS y las claves de `localStorage` conservan `alerta-piura` a propósito.
Id del equipo en el portal de la Kiro IAthon: `T051` (lo devuelve `GET /health`).

Mapa ciudadano de riesgo ante el Fenómeno El Niño (FEN) costero 2026-2027 para vecinos, brigadas y autoridades de Piura.
Entregable: reporte de puntos críticos con foto y un tablero priorizado. Reto: solidaridad y ayuda humanitaria.

## Contexto (30-oct-2026)
- ENFEN (Comunicado 18-2026): alerta de Niño costero, magnitud extraordinaria posible hasta ene-2027.
- 20-oct-2026: calles inundadas en Piura, Castilla, Veintiséis de Octubre, Catacaos y Cura Mori.
- Defensoría (22-oct): zonas críticas Ignacio Merino, El Chilcal, Las Azucenas, Dos Grifos y Los Olivos.
- Hay listas oficiales dispersas de puntos críticos, pero no un registro vivo, ciudadano y priorizado. Ese es el vacío.

## Usuarios
- **Vecino**: reporta desde el celular, sin instalar nada ni registrarse (94,1% de hogares con celular, 60,5% con internet).
- **Brigada / operador municipal**: verifica, atiende y cierra reportes.
- **Autoridad / COER**: ve prioridades, necesidades por distrito, exporta evidencia (CSV) y pide un parte situacional.

## Alcance (MoSCoW)
- MUST: M1 reporte sin login · M2 clasificación IA de la foto · M3 prioridad 0-100 explicable · M4 mapa público ·
  M5 tablero con clave compartida · M6 datos demo de Piura.
- SHOULD: S1 "yo también lo veo" · S2 exportar CSV · S3 parte situacional IA · S4 cola offline.
- ROADMAP (solo pitch): WhatsApp (AWS End User Messaging Social), Cognito con roles, Amazon Location Service,
  alertas SNS, deduplicación espacial, difuminado de rostros (Rekognition), capas CENEPRED/SIGRID, avisos SENAMHI.

## Principios
- Español claro, tono sobrio: "ni alarmismo ni indiferencia" (UDEP).
- Privacidad (Ley 29733): sin nombre ni teléfono, consentimiento explícito, el canvas elimina EXIF, las fotos solo
  se ven en el tablero con URL prefirmada de 15 min, el mapa público redondea coordenadas a 4 decimales.
- Contra la desinformación: la IA valida que la foto muestre un riesgo real; la prioridad siempre muestra motivos.
- Inclusión: botones grandes (≥44 px), poco texto, funciona con mala señal (cola offline).
- Números de emergencia mostrados: 105 (PNP), 116 (Bomberos), 106 (SAMU), con nota "verificar". No usar 115.
