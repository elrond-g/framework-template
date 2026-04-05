from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Chatbot Framework"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    # Database
    database_url: str = "sqlite:///./chatbot.db"

    # LLM
    llm_api_key: str = ""
    llm_api_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.7

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
