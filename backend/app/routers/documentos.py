import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.almacenamiento import AlmacenamientoLocal, obtener_almacenamiento
from app.config import settings
from app.db import get_db
from app.models import Documento, EstadoDocumento
from app.schemas import DocumentoResponse

router = APIRouter(prefix="/api/documentos", tags=["Documentos"])

SesionDb = Annotated[Session, Depends(get_db)]
Almacenamiento = Annotated[AlmacenamientoLocal, Depends(obtener_almacenamiento)]


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=DocumentoResponse)
def subir_documento(archivo: UploadFile, db: SesionDb, almacenamiento: Almacenamiento) -> Documento:
    """Recibe un PDF y lo deja en cola para procesarlo en segundo plano."""
    nombre = Path(archivo.filename or "").name
    if not nombre.lower().endswith(".pdf"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Solo se aceptan archivos PDF.")

    limite = settings.tamano_maximo_mb * 1024 * 1024
    contenido = archivo.file.read(limite + 1)
    if len(contenido) > limite:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"El archivo supera el máximo de {settings.tamano_maximo_mb} MB.",
        )

    # Todo PDF real empieza con "%PDF": no basta con que el nombre termine en .pdf
    if not contenido.startswith(b"%PDF"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El archivo no es un PDF válido.")

    documento = Documento(
        nombre_archivo=nombre[:255],
        ruta_archivo=almacenamiento.guardar(contenido, ".pdf"),
        tamano_bytes=len(contenido),
    )
    db.add(documento)
    db.commit()
    db.refresh(documento)
    return documento


@router.get("", response_model=list[DocumentoResponse])
def listar_documentos(db: SesionDb) -> list[Documento]:
    return list(db.scalars(select(Documento).order_by(Documento.creado_en.desc())))


@router.get("/{documento_id}", response_model=DocumentoResponse)
def obtener_documento(documento_id: uuid.UUID, db: SesionDb) -> Documento:
    documento = db.get(Documento, documento_id)
    if documento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El documento no existe.")
    return documento


@router.delete("/{documento_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_documento(documento_id: uuid.UUID, db: SesionDb, almacenamiento: Almacenamiento) -> None:
    documento = db.get(Documento, documento_id)
    if documento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El documento no existe.")
    if documento.estado == EstadoDocumento.PROCESANDO:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El documento se está procesando. Espera a que termine para eliminarlo.",
        )

    ruta = documento.ruta_archivo
    db.delete(documento)  # los fragmentos se borran en cascada
    db.commit()
    almacenamiento.eliminar(ruta)