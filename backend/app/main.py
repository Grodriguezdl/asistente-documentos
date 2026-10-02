from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.routers import documentos
app = FastAPI(
    title=settings.nombre_app,
    version="0.1.0",
    description="API que responde preguntas sobre documentos usando IA, citando la fuente.",
)
app.include_router(documentos.router)

@app.get("/api/salud", tags=["Sistema"])
def salud(db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    """Indica si la API funciona y si la base de datos y pgvector están disponibles."""
    try:
        version = db.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).scalar()
        base_de_datos = "ok"
        pgvector = version or "no instalado"
    except SQLAlchemyError:
        base_de_datos = "sin conexión"
        pgvector = "desconocido"

    return {
        "estado": "ok",
        "entorno": settings.entorno,
        "base_de_datos": base_de_datos,
        "pgvector": pgvector,
    }