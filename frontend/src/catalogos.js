// Enums compartidos. Fuente de verdad: .kiro/steering/api-contract.md
import distritosData from '../../data/distritos_piura.json'
import zonasData from '../../data/zonas_criticas.json'

export const DISTRITOS_DATA = distritosData
export const ZONAS_CRITICAS = zonasData
export const DISTRITOS = [...distritosData.map((d) => d.nombre), 'Otro (región)']

export const TIPOS = {
  inundacion_vivienda: { label: 'Inundación de vivienda', icono: '🏠' },
  aniego_via: { label: 'Aniego / cuenca ciega en vía', icono: '🌊' },
  desborde_rio_quebrada: { label: 'Desborde de río o quebrada', icono: '🏞️' },
  dren_colmatado: { label: 'Dren colmatado', icono: '🚧' },
  basura_cauce: { label: 'Basura u obstrucción en cauce', icono: '🗑️' },
  agua_estancada: { label: 'Agua estancada (foco de dengue)', icono: '🦟' },
  desague_colapsado: { label: 'Desagüe colapsado', icono: '🚽' },
  deslizamiento_huaico: { label: 'Deslizamiento / huaico / vía cortada', icono: '⛰️' },
  infraestructura_danada: { label: 'Infraestructura dañada', icono: '🌉' },
  otro: { label: 'Otro', icono: '❓' },
}

export const NECESIDADES = {
  agua: 'Agua',
  viveres: 'Víveres',
  evacuacion: 'Evacuación',
  atencion_medica: 'Atención médica',
  motobomba: 'Motobomba',
  abrigo_carpa: 'Abrigo / carpa',
  limpieza_dren: 'Limpieza de dren',
}

export const NIVELES = ['CRÍTICA', 'ALTA', 'MEDIA', 'BAJA']
export const COLOR_NIVEL = { 'CRÍTICA': '#c62828', ALTA: '#ef6c00', MEDIA: '#f9a825', BAJA: '#2e7d32' }

export const ESTADOS = {
  nuevo: 'Nuevo',
  verificado: 'Verificado',
  en_atencion: 'En atención',
  resuelto: 'Resuelto',
  descartado: 'Descartado',
}

export const CENTRO_PIURA = [-5.19, -80.64]

export const tipoLabel = (t) => TIPOS[t]?.label ?? t
export const fecha = (iso) =>
  new Date(iso).toLocaleString('es-PE', { timeZone: 'America/Lima', dateStyle: 'short', timeStyle: 'short' })
