from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import find_dotenv


class Settings(BaseSettings):
    DB_HOST: str = ...
    DB_PORT: int = ...
    DB_USER: str = ...
    DB_PASSWORD: str = ...
    DB_NAME: str = ...
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 14
    JWT_REFRESH_COOKIE_NAME: str = 'refresh_token'
    JWT_REFRESH_COOKIE_SECURE: bool = False
    JWT_REFRESH_COOKIE_SAMESITE: str = 'lax'


    @property
    def database_url(self):
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'


    model_config = SettingsConfigDict(
        env_file=find_dotenv(),
        extra='ignore',
    )


settings = Settings()
