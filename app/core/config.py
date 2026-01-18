# handles importing of env vars 
import os

from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings

# Determine the environment ('dev', 'prod', etc.). Defaults to 'dev' if ENV is not set.
ENV = os.getenv("ENV", "local") # TODO: find a better way to handle setting the env I don't think using ignore is the best option

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SenyaWeb"

    PASSCODE: str = ""
    CORS_ORIGINS: list[str] | str = []

    #### API KEYS ####
    GOOGLE_AI_STUDIO_API_KEY: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip().startswith("["):
            return [i.strip() for i in v.split(",")]
        return v

    # Define your variables here. They will be read from the .env file.
    # DATABASE_URL: str
    # SECRET_KEY: str

    class Config:
        env_file = f".env.{ENV}"
        extra = "ignore" # TODO: find a better solution to do this

settings = Settings()
