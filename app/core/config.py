from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "Bali Trip Planner API"
    env: str = "dev"
    log_level: str = "INFO"


settings = Settings()

