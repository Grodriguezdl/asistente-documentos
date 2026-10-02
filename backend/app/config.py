from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    nombre_app: str = "Asistente de Documentos"
    entorno: str = "desarrollo"

    # Se toma de la variable de entorno DATABASE_URL o del archivo .env
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/asistente"


settings = Settings()