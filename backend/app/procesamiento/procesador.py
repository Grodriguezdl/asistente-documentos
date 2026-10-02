from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.almacenamiento import AlmacenamientoLocal
from app.config import settings
from app.models import Documento, Fragmento
from app.procesamiento.embeddings import Embedder
from app.procesamiento.extraccion import ErrorProcesamiento, extraer_paginas
from app.procesamiento.fragmentacion import dividir_en_fragmentos

TAMANO_LOTE = 32


def procesar_documento(
    db: Session,
    documento: Documento,
    almacenamiento: AlmacenamientoLocal,
    embedder: Embedder,
) -> None:
    """Extrae el texto, lo fragmenta, genera los vectores y los guarda."""
    paginas = extraer_paginas(almacenamiento.leer(documento.ruta_archivo))
    documento.paginas = len(paginas)

    fragmentos = dividir_en_fragmentos(
        paginas, settings.tamano_fragmento, settings.solapamiento_fragmento
    )
    if not fragmentos:
        raise ErrorProcesamiento(
            "No se encontró texto en el documento. Si es un PDF escaneado, "
            "necesita reconocimiento de texto (OCR)."
        )

    # Si es un reintento, se borran los fragmentos que hayan quedado a medias
    db.execute(delete(Fragmento).where(Fragmento.documento_id == documento.id))

    for inicio in range(0, len(fragmentos), TAMANO_LOTE):
        lote = fragmentos[inicio : inicio + TAMANO_LOTE]
        vectores = embedder.generar([f.contenido for f in lote])

        db.add_all(
            Fragmento(
                documento_id=documento.id,
                orden=f.orden,
                pagina=f.pagina,
                contenido=f.contenido,
                embedding=vector,
            )
            for f, vector in zip(lote, vectores, strict=True)
        )
        documento.progreso = round((inicio + len(lote)) / len(fragmentos) * 100)
        db.commit()  # cada lote se guarda, así el usuario ve el avance