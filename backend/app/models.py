import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

# Tamaño de los vectores que genera el modelo de embeddings (lo elegimos en la fase 3)
DIMENSION_EMBEDDING = 384


class EstadoDocumento(str, enum.Enum):
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    LISTO = "listo"
    ERROR = "error"


class Documento(Base):
    __tablename__ = "documentos"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nombre_archivo: Mapped[str] = mapped_column(String(255))
    ruta_archivo: Mapped[str] = mapped_column(String(500))
    tamano_bytes: Mapped[int] = mapped_column(Integer)
    paginas: Mapped[int | None] = mapped_column(Integer)
    estado: Mapped[EstadoDocumento] = mapped_column(
        # Se guarda como texto ("listo") y no como número, igual que en el inventario
        Enum(
            EstadoDocumento,
            native_enum=False,
            length=20,
            values_callable=lambda estados: [e.value for e in estados],
        ),
        default=EstadoDocumento.PENDIENTE,
        index=True,
    )
    error: Mapped[str | None] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    procesado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    fragmentos: Mapped[list["Fragmento"]] = relationship(
        back_populates="documento",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Fragmento(Base):
    __tablename__ = "fragmentos"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    documento_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documentos.id", ondelete="CASCADE"), index=True
    )
    orden: Mapped[int] = mapped_column(Integer)
    pagina: Mapped[int] = mapped_column(Integer)
    contenido: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(DIMENSION_EMBEDDING))

    documento: Mapped[Documento] = relationship(back_populates="fragmentos")

    __table_args__ = (
        # Índice HNSW: permite encontrar los vectores más parecidos sin revisar uno por uno
        Index(
            "ix_fragmentos_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )