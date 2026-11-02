"""Trabajos asíncronos de la insignia "Asíncrono o agente" (Kiro IAthon). Funciones puras, sin I/O."""

ESPERA_MS = 2000  # el trabajo queda listo 2 s después de crearse (se resuelve al leer)


def procesar(entrada: str) -> str:
    """Invierte el texto carácter por carácter: "abc1" -> "1cba"."""
    return entrada[::-1]


def estado(entrada: str, listo_en_ms: int, ahora_ms: int) -> dict:
    if ahora_ms >= listo_en_ms:
        return {"status": "done", "output": procesar(entrada)}
    return {"status": "queued", "output": None}
