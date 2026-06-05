from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openrouter_api_key: str
    hf_token: str = ""
    llm_model: str = "openai/gpt-4o-mini"
    llm_base_url: str = "https://openrouter.ai/api/v1"
    embeddings_model: str = "all-MiniLM-L6-v2"
    cors_origins: str = "http://localhost:3000"
    chunk_size: int = 800
    chunk_overlap: int = 100
    retriever_k: int = 6

    def cors_origins_list(self) -> list[str]:
        parts = [v.strip() for v in self.cors_origins.split(",") if v.strip()]
        return parts or ["http://localhost:3000"]


settings = Settings()
