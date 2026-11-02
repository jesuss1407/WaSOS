"""Enums y constantes de dominio. Fuente de verdad: .kiro/steering/api-contract.md."""

TIPOS = {
    "inundacion_vivienda": "Inundación de vivienda",
    "aniego_via": "Aniego / cuenca ciega en vía",
    "desborde_rio_quebrada": "Desborde de río o quebrada",
    "dren_colmatado": "Dren colmatado",
    "basura_cauce": "Basura u obstrucción en cauce",
    "agua_estancada": "Agua estancada (foco de dengue)",
    "desague_colapsado": "Desagüe colapsado",
    "deslizamiento_huaico": "Deslizamiento / huaico / vía cortada",
    "infraestructura_danada": "Infraestructura dañada",
    "otro": "Otro",
}

NECESIDADES = {
    "agua": "Agua",
    "viveres": "Víveres",
    "evacuacion": "Evacuación",
    "atencion_medica": "Atención médica",
    "motobomba": "Motobomba",
    "abrigo_carpa": "Abrigo / carpa",
    "limpieza_dren": "Limpieza de dren",
}

DISTRITOS = [
    "Piura",
    "Castilla",
    "Veintiséis de Octubre",
    "Catacaos",
    "Cura Mori",
    "El Tallán",
    "La Arena",
    "La Unión",
    "Las Lomas",
    "Tambogrande",
    "Otro (región)",
]

ESTADOS = ["nuevo", "verificado", "en_atencion", "resuelto", "descartado"]

# Flujo: nuevo -> verificado -> en_atencion (brigada) -> resuelto | descartado
TRANSICIONES = {
    "nuevo": {"verificado", "descartado"},
    "verificado": {"en_atencion", "descartado"},
    "en_atencion": {"resuelto", "descartado"},
    "resuelto": set(),
    "descartado": set(),
}

ESTADOS_ACTIVOS = {"nuevo", "verificado", "en_atencion"}

NIVELES = ["CRÍTICA", "ALTA", "MEDIA", "BAJA"]

# Peso del tipo en la fórmula de prioridad (0..1)
PESO_TIPO = {
    "desborde_rio_quebrada": 1.0,
    "deslizamiento_huaico": 1.0,
    "inundacion_vivienda": 1.0,
    "desague_colapsado": 0.8,
    "infraestructura_danada": 0.8,
    "aniego_via": 0.6,
    "dren_colmatado": 0.6,
    "agua_estancada": 0.5,
    "basura_cauce": 0.4,
    "otro": 0.3,
}

# Severidad por defecto cuando la IA no está disponible (fallback)
SEVERIDAD_POR_DEFECTO = {
    "desborde_rio_quebrada": 4,
    "deslizamiento_huaico": 4,
    "inundacion_vivienda": 4,
    "desague_colapsado": 3,
    "infraestructura_danada": 3,
    "aniego_via": 3,
    "dren_colmatado": 3,
    "agua_estancada": 2,
    "basura_cauce": 2,
    "otro": 2,
}

# Bounding box aproximado de la región Piura
BBOX = {"lat_min": -6.4, "lat_max": -4.0, "lon_min": -81.4, "lon_max": -79.2}

DESCRIPCION_MAX = 500
RADIO_ZONA_CRITICA_M = 300
