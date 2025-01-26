import pathlib,os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from dotenv import load_dotenv

load_dotenv()


# Project Directories
ROOT = pathlib.Path(__file__).resolve().parent


class Settings(BaseSettings):
    DATABASE_URL:str = os.environ.get('DATABASE_URL')
    SECRET_KEY:str = os.environ.get('SECRET_KEY')
    ACCESS_TOKEN_EXPIRE_MINUTES:str = '60'
    ALGORITHM:str = 'HS256'
    BACKEND_CORS_ORIGINS: List[str] = ['http://localhost:5173','https://personal-resource-tracker-app.onrender.com']
    TIME_ZONE:str = 'Africa/Lagos'

    # @validator("BACKEND_CORS_ORIGINS", pre=True)
    # def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
    #     if isinstance(v, str) and not v.startswith("["):
    #         return [i.strip() for i in v.split(",")]
    #     elif isinstance(v, (list, str)):
    #         return v
    #     raise ValueError(v)

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
