from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    SUPABASE_URL: str
    SUPABASE_JWT_SECRET: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()