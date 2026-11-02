# Requisitos: 03 Frontend (web móvil) y tablero

## Introducción
SPA React + Vite, mobile-first, sin instalación ni login para el vecino, con mapa Leaflet/OpenStreetMap y tablero
para autoridades. Contrato: #[[file:.kiro/steering/api-contract.md]]

## Requisito 1: Pantalla Reportar (MUST, M1)
**Historia:** Como vecino con un celular básico y mala señal, quiero reportar un punto crítico en menos de un minuto.
- R1.1 CUANDO el vecino toque "Tomar o elegir foto" ENTONCES el sistema DEBERÁ abrir la cámara trasera
  (`capture="environment"`) y re-codificar la imagen en un canvas a JPEG ≤300 KB sin EXIF, mostrando vista previa y peso. (MUST)
- R1.2 CUANDO se abra la pantalla ENTONCES el sistema DEBERÁ pedir el GPS y mostrar un mapa con pin arrastrable;
  SI no hay GPS ENTONCES el vecino DEBERÁ poder tocar el mapa para ubicar el punto. SI el GPS, el toque o el arrastre
  dejan el punto fuera del bbox de la región Piura ENTONCES el sistema DEBERÁ rechazarlo con un mensaje y conservar el
  pin anterior (la API aplica el mismo bbox). (MUST)
- R1.3 CUANDO cambie la ubicación ENTONCES el sistema DEBERÁ autodetectar el distrito por cercanía al centroide
  (editable; "Otro (región)" si está a más de 25 km). (MUST)
- R1.4 El formulario DEBERÁ pedir tipo (10 opciones con icono), descripción opcional (≤500), casilla de personas
  vulnerables, necesidades (multi-selección) y consentimiento Ley 29733; el botón Enviar DEBERÁ indicar qué falta. (MUST)
- R1.5 CUANDO el envío termine ENTONCES el sistema DEBERÁ mostrar nivel, prioridad, motivos, la descripción de la IA,
  el tipo sugerido por la IA si difiere del elegido y los números 105 / 116 / 106 con la nota "verificar". (MUST)
- R1.6 SI no hay conexión o el servidor falla (5xx) ENTONCES el sistema DEBERÁ guardar el reporte en localStorage y
  reenviarlo al volver la conexión (evento `online` y cada 60 s), sin duplicarlo. (SHOULD, S4)

## Requisito 2: Mapa público (MUST, M4)
- R2.1 El mapa DEBERÁ mostrar solo reportes válidos con color por nivel (rojo, naranja, amarillo, verde; gris si resuelto),
  leyenda, capa de zonas críticas (300 m) y filtros por distrito y nivel; se actualiza cada 30 s. (MUST)
- R2.2 El popup NO DEBERÁ mostrar fotos ni datos personales. (MUST)
- R2.3 CUANDO un vecino toque "Yo también lo veo" ENTONCES el sistema DEBERÁ sumar su confirmación una vez por
  dispositivo y actualizar prioridad y nivel. (SHOULD, S1)

## Requisito 3: Tablero priorizado (MUST, M5)
**Historia:** Como autoridad o brigada, quiero una lista ordenada por prioridad con foto, para decidir a dónde ir primero.
- R3.1 CUANDO se abra `/tablero` sin clave ENTONCES el sistema DEBERÁ pedir la clave compartida y guardarla solo en
  `sessionStorage`; SI la API responde 401 ENTONCES DEBERÁ volver a pedirla. (MUST)
- R3.2 El tablero DEBERÁ mostrar KPIs por nivel, lista ordenada por prioridad, mapa sincronizado y filtros por
  distrito, tipo, estado y nivel. (MUST)
- R3.3 CUANDO se seleccione un reporte ENTONCES el sistema DEBERÁ mostrar foto, motivos, datos de la IA, descripción
  del vecino, necesidades, historial y botones solo para las transiciones permitidas (brigada obligatoria para "En atención"). (MUST)
- R3.4 El tablero DEBERÁ mostrar el panel "Necesidades por distrito" con activos, niveles, vulnerables y necesidades. (MUST)
- R3.5 El tablero DEBERÁ permitir exportar CSV (S2) y generar el parte situacional IA con botón Copiar (S3). (SHOULD)

## Requisito 4: Calidad (MUST)
- R4.1 Interfaz en español, botones de al menos 44 px, legible en pantallas de 360 px. (MUST)
- R4.2 Publicación en AWS Amplify Hosting con rutas SPA (`/mapa`, `/tablero`) accesibles por URL directa. (MUST)
