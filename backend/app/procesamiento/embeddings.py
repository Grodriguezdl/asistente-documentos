from functools import lru_cache
from typing import Protocol

from app.config import settings


class Embedder(Protocol):
    """Cualquier clase que convierta textos en vectores."""

    def generar(self, textos: list[str]) -> list[list[float]]: ...


class FastEmbedEmbedder:
    """Genera los vectores en la propia computadora, sin servicios externos."""

    def __init__(self, modelo: str) -> None:
        # Se importa aquí para que las pruebas no tengan que cargar el modelo
        from fastembed import TextEmbedding

        self._modelo = TextEmbedding(model_name=modelo)

    def generar(self, textos: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._modelo.embed(textos, batch_size=32)]


@lru_cache
def obtener_embedder() -> Embedder:
    """Carga el modelo una sola vez y lo reutiliza."""
    return FastEmbedEmbedder(settings.modelo_embeddings)