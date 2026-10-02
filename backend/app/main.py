from fastapi import FastAPI

from app.config import settings

app = FastAPI(
    title=settings.nombre_app,
    version="0.1.0",
    description="API que responde preguntas sobre documentos usando IA, citando la fuente.",
)


@app.get("/api/salud", tags=["Sistema"])
def salud() -> dict[str, str]:
    """Indica si la API está funcionando."""
    return {"estado": "ok", "entorno": settings.entorno}