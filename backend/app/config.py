from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://scraper:scraper123@localhost:5432/scraper_db"

    # Browser
    browser_headless: bool = True
    browser_pool_size: int = 3

    # Application
    app_name: str = "Visual Builder Scraping"
    debug: bool = False

    # Workers
    worker_count: int = 2

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
