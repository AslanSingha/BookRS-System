from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # App
    APP_NAME: str = "BookRS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "bookrs-secret-key"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://bookrs:bookrs123@localhost:5432/bookrs_db"

    # Paths
    DATA_DIR: str = "/home/singh/data"
    MODELS_DIR: str = "/home/singh/projects/BookRS/models"
    BOOKS_PARQUET: str = "bookrs_ucsd_books.parquet"
    INTERACTIONS_PARQUET: str = "bookrs_ucsd_interactions.parquet"

    # ML Settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    ALS_FACTORS: int = 128
    ALS_REGULARIZATION: float = 0.1
    ALS_ITERATIONS: int = 10
    ALPHA: float = 0.1

    @property
    def books_path(self) -> Path:
        return Path(self.DATA_DIR) / self.BOOKS_PARQUET

    @property
    def interactions_path(self) -> Path:
        return Path(self.DATA_DIR) / self.INTERACTIONS_PARQUET

    @property
    def models_path(self) -> Path:
        return Path(self.MODELS_DIR)

    class Config:
        env_file = ".env"

settings = Settings()
