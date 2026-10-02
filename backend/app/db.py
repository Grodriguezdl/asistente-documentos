from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Clase base de todos los modelos."""


# pool_pre_ping revisa que la conexión siga viva antes de usarla.
# Es importante con Neon, que suspende la base tras unos minutos sin uso.
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Entrega una sesión por petición y la cierra al terminar."""
    with SessionLocal() as db:
        yield db