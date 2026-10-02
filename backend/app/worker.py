import logging
import signal
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.almacenamiento import AlmacenamientoLocal
from app.config import settings
from app.db import SessionLocal
from app.models import Documento, EstadoDocumento
from app.procesamiento.embeddings import Embedder, obtener_embedder
from app.procesamiento.extraccion import ErrorProcesamiento
from app.procesamiento.procesador import procesar_documento

logger = logging.getLogger("worker")

# Si un documento lleva más de este tiempo "procesando", el worker que lo tomaba se cayó
TIEMPO_ABANDONO = timedelta(minutes=15)


def tomar_siguiente(db: Session) -> Documento | None:
    """Toma el documento pendiente más antiguo, bloqueándolo para otros workers."""
    documento = db.scalars(
        select(Documento)
        .where(Documento.estado == EstadoDocumento.PENDIENTE)
        .order_by(Documento.creado_en)
        .limit(1)
        .with_for_update(skip_locked=True)
    ).first()

    if documento is not None:
        documento.estado = EstadoDocumento.PROCESANDO
        documento.iniciado_en = datetime.now(UTC)
        documento.intentos += 1
        documento.progreso = 0
        documento.error = None
        db.commit()

    return documento


def recuperar_abandonados(db: Session) -> None:
    """Devuelve a la cola los documentos que quedaron a medias por una caída."""
    limite = datetime.now(UTC) - TIEMPO_ABANDONO
    abandonados = db.scalars(
        select(Documento).where(
            Documento.estado == EstadoDocumento.PROCESANDO,
            Documento.iniciado_en < limite,
        )
    ).all()

    for documento in abandonados:
        if documento.intentos >= settings.max_intentos_procesamiento:
            documento.estado = EstadoDocumento.ERROR
            documento.error = "El procesamiento se interrumpió varias veces."
        else:
            documento.estado = EstadoDocumento.PENDIENTE
        logger.warning("Documento %s recuperado como %s", documento.id, documento.estado.value)

    db.commit()


def ejecutar_un_ciclo(db: Session, almacenamiento: AlmacenamientoLocal, embedder: Embedder) -> bool:
    """Procesa un documento. Devuelve False si no había nada pendiente."""
    documento = tomar_siguiente(db)
    if documento is None:
        return False

    documento_id = documento.id
    logger.info("Procesando %s (%s)", documento.nombre_archivo, documento_id)

    try:
        procesar_documento(db, documento, almacenamiento, embedder)
        documento.estado = EstadoDocumento.LISTO
        documento.progreso = 100
        documento.procesado_en = datetime.now(UTC)
        logger.info("Listo: %s", documento.nombre_archivo)
    except ErrorProcesamiento as error:
        db.rollback()
        documento = db.get(Documento, documento_id)
        documento.estado = EstadoDocumento.ERROR
        documento.error = str(error)
        logger.warning("No se pudo procesar %s: %s", documento_id, error)
    except Exception:
        logger.exception("Error inesperado procesando %s", documento_id)
        db.rollback()
        documento = db.get(Documento, documento_id)
        if documento.intentos >= settings.max_intentos_procesamiento:
            documento.estado = EstadoDocumento.ERROR
            documento.error = "Ocurrió un error inesperado al procesar el documento."
        else:
            documento.estado = EstadoDocumento.PENDIENTE  # se reintentará

    db.commit()
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    detener = False

    def al_recibir_senal(*_: object) -> None:
        nonlocal detener
        logger.info("Deteniendo el worker al terminar el documento actual...")
        detener = True

    signal.signal(signal.SIGINT, al_recibir_senal)
    signal.signal(signal.SIGTERM, al_recibir_senal)

    logger.info("Cargando el modelo de embeddings (la primera vez se descarga)...")
    embedder = obtener_embedder()
    almacenamiento = AlmacenamientoLocal(settings.carpeta_almacenamiento)

    with SessionLocal() as db:
        recuperar_abandonados(db)

    logger.info("Worker listo. Esperando documentos.")
    while not detener:
        with SessionLocal() as db:
            hubo_trabajo = ejecutar_un_ciclo(db, almacenamiento, embedder)
        if not hubo_trabajo:
            time.sleep(settings.intervalo_worker_segundos)


if __name__ == "__main__":
    main()