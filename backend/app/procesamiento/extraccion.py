from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class ErrorProcesamiento(Exception):
    """Error con un mensaje que se le puede mostrar al usuario."""


def extraer_paginas(contenido: bytes) -> list[str]:
    """Devuelve el texto de cada página del PDF, en orden."""
    try:
        lector = PdfReader(BytesIO(contenido))
        if lector.is_encrypted and not lector.decrypt(""):
            raise ErrorProcesamiento("El PDF está protegido con contraseña.")
        return [pagina.extract_text() or "" for pagina in lector.pages]
    except PdfReadError as error:
        raise ErrorProcesamiento("El archivo PDF está dañado o no se puede leer.") from error