# handles importing of env vars 
import os

from pydantic import BaseSettings

# Determine the environment ('dev', 'prod', etc.). Defaults to 'dev' if APP_ENV is not set.
APP_ENV = os.getenv("APP_ENV", "dev")

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SenyaWeb"

    # Define your variables here. They will be read from the .env file.
    # DATABASE_URL: str
    # SECRET_KEY: str

    class Config:
        env_file = f".env.{APP_ENV}"

settings = Settings()
