from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MESH"
    env: str = "development"
    database_url: str = "sqlite:///./mesh.db"

    class Config:
        env_file = ".env"


settings = Settings()