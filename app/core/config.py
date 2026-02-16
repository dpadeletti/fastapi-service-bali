from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # FastAPI cerca app_name per il titolo della documentazione
    app_name: str = "Bali Travel API" 
    
    # Alembic e il DB cercano database_url
    database_url: str 
    
    # Il sistema di logging cerca log_level
    log_level: str = "INFO" 
    
    # Il tuo nuovo AIService usa questo per Ollama
    ollama_base_url: str = "http://host.docker.internal:11434"

    model_config = SettingsConfigDict(
        # Carica in ordine di priorità
        env_file=(".env.local"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()