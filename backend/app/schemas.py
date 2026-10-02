import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import EstadoDocumento


class DocumentoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre_archivo: str
    tamano_bytes: int
    paginas: int | None
    estado: EstadoDocumento
    progreso: int
    error: str | None
    creado_en: datetime
    procesado_en: datetime | None