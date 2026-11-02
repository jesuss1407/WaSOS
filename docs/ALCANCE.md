# Alcance, decisiones y demo

## Problema (30-oct-2026)
- ENFEN, Comunicado 18-2026 (16-oct): alerta de Niño costero con magnitud extraordinaria posible hasta ene-2027.
- 20-oct: calles inundadas en Piura, Castilla, Veintiséis de Octubre, Catacaos y Cura Mori.
- Defensoría (22-oct): zonas críticas Ignacio Merino, El Chilcal, Las Azucenas, Dos Grifos y Los Olivos.
- Cifras oficiales dispersas (MPP 150+ puntos críticos, Congreso 134, Contraloría 74, más de 120 cuencas ciegas):
  hay listas, pero no un **registro vivo, ciudadano y priorizado**.

## De la investigación al producto
| Hallazgo | Decisión implementada |
|---|---|
| Aniegos y cuencas ciegas con motobombas (Defensoría) | Tipo `aniego_via`, necesidad `motobomba`, capa de zonas críticas que suma prioridad |
| Drenes 31 de Enero y Enace sin limpieza (Contraloría) | Tipo `dren_colmatado`, zonas en el mapa, CSV como evidencia para fiscalización |
| Basura en drenes agrava el riesgo (Vigilante) | Tipo `basura_cauce`: también sirve para prevenir |
| Dengue y leptospirosis tras lluvias (Minsa/DIRESA) | Tipo `agua_estancada` y marca `riesgo_salud` |
| Huaicos y caseríos aislados en la sierra | Tipo `deslizamiento_huaico`; el mapa cubre toda la región |
| 94,1% de hogares con celular, 60,5% con internet (INEI) | Web móvil sin instalación ni login, foto ≤300 KB, cola offline |
| SINPAD/SIGRID sin API pública | CSV exportable para el COER |
| Riesgo de desinformación (UDEP) | IA que valida la foto, motivos visibles, "Yo también lo veo" |
| 17 almacenes del GORE, colectas UDEP y Arzobispado | Campo "¿Qué se necesita?" y panel de necesidades por distrito |

## Pitch (30 s)
"El 20 de octubre Piura amaneció inundada y el ENFEN advierte un Niño costero que puede ser extraordinario. Las listas de
puntos críticos existen, pero están dispersas y desactualizadas. WaSOS convierte a cada vecino con un celular
en un sensor: una foto, su ubicación y lo que necesita. La IA valida y clasifica la foto, el sistema prioriza con
motivos que cualquiera entiende y las autoridades ven en un tablero qué atender primero y qué ayuda enviar a cada
distrito. Serverless, de pago por uso, desplegado hoy en AWS."

## Guion de demo (3 min)
1. **Contexto (20 s):** alerta ENFEN, Piura inundada el 20-oct, zonas críticas de la Defensoría en el mapa (círculos morados).
2. **Vecino (60 s):** en el celular, `/` → foto → GPS cerca del óvalo Dos Grifos → "Dren colmatado" → vulnerables →
   "Motobomba" → consentimiento → Enviar. Resultado: nivel, prioridad, motivos y tipo sugerido por la IA.
3. **Mapa público (20 s):** `/mapa` muestra el punto nuevo; "Yo también lo veo" sube la confirmación.
4. **Autoridad (50 s):** `/tablero` → el reporte aparece arriba por zona crítica + vulnerables → ver foto →
   "Verificado" → asignar "Brigada MPP 03" → "En atención". Historial registrado.
5. **Solidaridad (20 s):** panel "Necesidades por distrito" (p. ej., Catacaos: agua y víveres) → "Parte situacional IA"
   para el COER → "Exportar CSV" para Defensoría/Contraloría.
6. **Roadmap (10 s):** WhatsApp, Cognito con roles, SINPAD, alertas SNS a brigadas, Rekognition para difuminar rostros.

## Roadmap
WhatsApp (AWS End User Messaging Social) · Cognito con roles · Amazon Location Service · alertas SNS a brigadas ·
deduplicación espacial · difuminado de rostros (Rekognition) · capas CENEPRED/SIGRID y avisos SENAMHI · integración COER.

## Fuentes
- ENFEN, Comunicado Oficial 18-2026: https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-18-2026/
- Infobae, Piura inundada (20-oct-2026): https://www.infobae.com/peru/2026/10/20/el-norte-del-peru-empieza-a-sentir-los-estragos-de-el-nino-calles-de-piura-amanecen-inundadas-por-lluvias/
- RCR, zonas críticas según la Defensoría: https://www.rcrperu.com/defensoria-identifica-zonas-criticas-por-lluvias-del-nino-costero-2026-en-piura-y-reporta-viviendas-inundadas/
- La República, 31% de ejecución presupuestal y drenes sin limpieza: https://larepublica.pe/sociedad/2026/10/24/distrito-de-piura-afectado-por-lluvias-ejecuto-solo-el-31-del-presupuesto-para-enfrentar-el-nino-882936
- RPP, cuenca Las Azucenas (urb. APAF) y Los Dos Grifos: https://rpp.pe/peru/piura/lluvias-en-piura-ciudadanos-exigen-mas-electrobombas-e-hidrojets-para-evacuar-aguas-pluviales-noticia-1713628
- Ministerio de Vivienda, aniegos en Dos Grifos y El Chilcal: https://www.gob.pe/institucion/vivienda/noticias/902316-ministerio-de-vivienda-atendio-aniegos-producidos-por-lluvias-en-piura
- UDEP, El Niño 2026-2027 en Piura: https://www.udep.edu.pe/hoy/2026/07/el-nino-2026-2027-en-piura-lo-que-realmente-sabemos-hasta-ahora/
- Vigilante, ciudadanos y riesgo: https://vigilante.pe/2026/08/21/el-nino-como-los-ciudadanos-tambien-agravan-el-peligro-en-zonas-inundables/
- Andina / Panamericana, datos INEI: https://andina.pe/agencia/noticia-inei-uso-internet-alcanzo-al-802-de-poblacion-6-y-mas-anos-edad-1012997.aspx
- Coordenadas: OpenStreetMap / Nominatim (© colaboradores de OpenStreetMap, ODbL).
