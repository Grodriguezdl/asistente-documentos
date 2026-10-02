from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    nombre_app: str = "Asistente de Documentos"
    entorno: str = "desarrollo"

    # Se toma de la variable de entorno DATABASE_URL o del archivo .env
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/asistente"

    # Archivos subidos
    carpeta_almacenamiento: str = "almacenamiento"
    tamano_maximo_mb: int = 20

    # Procesamiento
    modelo_embeddings: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    tamano_fragmento: int = 1000
    solapamiento_fragmento: int = 200
    intervalo_worker_segundos: float = 2.0
    max_intentos_procesamiento: int = 3


settings = Settings()