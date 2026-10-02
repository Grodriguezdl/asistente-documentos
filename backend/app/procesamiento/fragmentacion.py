import re
from dataclasses import dataclass

# Se intenta cortar primero por párrafos, luego por líneas, oraciones y palabras
SEPARADORES = ["\n\n", "\n", ". ", " "]


@dataclass(frozen=True)
class FragmentoTexto:
    orden: int
    pagina: int
    contenido: str


def limpiar_texto(texto: str) -> str:
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _partir(texto: str, tamano: int, separadores: list[str]) -> list[str]:
    """Parte el texto en piezas de como máximo `tamano` caracteres."""
    if len(texto) <= tamano:
        return [texto]
    if not separadores:
        # Último recurso: cortar a la fuerza
        return [texto[i : i + tamano] for i in range(0, len(texto), tamano)]

    separador, *resto = separadores
    if separador not in texto:
        return _partir(texto, tamano, resto)

    partes = texto.split(separador)
    # Se conserva el separador al final de cada parte, para no perder puntos ni saltos
    partes = [parte + separador for parte in partes[:-1]] + [partes[-1]]

    piezas: list[str] = []
    for parte in partes:
        if parte:
            piezas.extend(_partir(parte, tamano, resto))
    return piezas


def _agrupar(piezas: list[str], tamano: int, solapamiento: int) -> list[str]:
    """Une piezas pequeñas en fragmentos de hasta `tamano`, repitiendo el final del anterior."""
    fragmentos: list[str] = []
    actual: list[str] = []
    largo = 0

    for pieza in piezas:
        if actual and largo + len(pieza) > tamano:
            fragmentos.append("".join(actual).strip())
            # Se conservan las últimas piezas como solapamiento, sin pasarse del tamaño
            while actual and (largo > solapamiento or largo + len(pieza) > tamano):
                largo -= len(actual.pop(0))
        actual.append(pieza)
        largo += len(pieza)

    if actual:
        fragmentos.append("".join(actual).strip())

    return [fragmento for fragmento in fragmentos if fragmento]


def dividir_en_fragmentos(paginas: list[str], tamano: int, solapamiento: int) -> list[FragmentoTexto]:
    """Divide cada página por separado, para que cada fragmento pertenezca a una sola página."""
    resultado: list[FragmentoTexto] = []

    for numero_pagina, texto in enumerate(paginas, start=1):
        limpio = limpiar_texto(texto)
        if not limpio:
            continue
        for contenido in _agrupar(_partir(limpio, tamano, SEPARADORES), tamano, solapamiento):
            resultado.append(FragmentoTexto(orden=len(resultado), pagina=numero_pagina, contenido=contenido))

    return resultado