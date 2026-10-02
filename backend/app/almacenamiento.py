import uuid
from pathlib import Path

from app.config import settings


class AlmacenamientoLocal:
    """Guarda los archivos en una carpeta del servidor.

    Al estar en una clase, en producción se puede reemplazar por un almacenamiento
    en la nube sin cambiar el resto del código.
    """

    def __init__(self, carpeta: str | Path) -> None:
        self._raiz = Path(carpeta).resolve()
        self._raiz.mkdir(parents=True, exist_ok=True)

    def guardar(self, contenido: bytes, extension: str) -> str:
        # Nombre aleatorio: nunca se usa el nombre que envía el usuario
        nombre = f"{uuid.uuid4().hex}{extension}"
        (self._raiz / nombre).write_bytes(contenido)
        return nombre

    def leer(self, ruta: str) -> bytes:
        return self._ruta_segura(ruta).read_bytes()

    def eliminar(self, ruta: str) -> None:
        self._ruta_segura(ruta).unlink(missing_ok=True)

    def _ruta_segura(self, ruta: str) -> Path:
        # Impide rutas como "../../otro_archivo" que escapen de la carpeta
        completa = (self._raiz / ruta).resolve()
        if not completa.is_relative_to(self._raiz):
            raise ValueError("Ruta de archivo no válida.")
        return completa


def obtener_almacenamiento() -> AlmacenamientoLocal:
    return AlmacenamientoLocal(settings.carpeta_almacenamiento)