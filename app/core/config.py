# handles importing of env vars 
import os

from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings

# Determine the environment ('dev', 'prod', etc.). Defaults to 'dev' if ENV is not set.
ENV = os.getenv("ENV", "local") # TODO: find a better way to handle setting the env I don't think using ignore is the best option

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SenyaWeb"
    
    # DEBUG: Check if env var is present
    print(f"DEBUG ENV VAR: {os.environ.get('GOOGLE_AI_STUDIO_API_KEY')}")

    PASSCODE: str = ""
    CORS_ORIGINS: list[str] | str = []

    #### API KEYS ####
    GOOGLE_AI_STUDIO_API_KEY: str = ""
    OPENROUTER_KEY: str = ""
    
    # Private Key for JWE Encryption
    PRIVATE_KEY: str = ""
    PRIVATE_KEY_PATH: str = "private.pem" # Path to the private key file
    PUBLIC_KEY: str = ""
    PUBLIC_KEY_PATH: str = "public.pem" # Path to the public key file

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip().startswith("["):
            return [i.strip() for i in v.split(",")]
        return v

    @model_validator(mode="after")
    def load_keys(self) -> "Settings":
        if not self.PRIVATE_KEY and self.PRIVATE_KEY_PATH and os.path.exists(self.PRIVATE_KEY_PATH):
            try:
                with open(self.PRIVATE_KEY_PATH, "r") as f:
                    self.PRIVATE_KEY = f.read()
                # Set env var as requested
                os.environ["PRIVATE_KEY"] = self.PRIVATE_KEY
            except Exception as e:
                print(f"WARNING: Could not read PRIVATE_KEY from {self.PRIVATE_KEY_PATH}: {e}")

        if not self.PUBLIC_KEY and self.PUBLIC_KEY_PATH and os.path.exists(self.PUBLIC_KEY_PATH):
            try:
                with open(self.PUBLIC_KEY_PATH, "r") as f:
                    self.PUBLIC_KEY = f.read()
                # Set env var as requested
                os.environ["PUBLIC_KEY"] = self.PUBLIC_KEY
            except Exception as e:
                print(f"WARNING: Could not read PUBLIC_KEY from {self.PUBLIC_KEY_PATH}: {e}")
        return self

    # Define your variables here. They will be read from the .env file.
    # DATABASE_URL: str
    # SECRET_KEY: str

    

    class Config:
        env_file = f".env.{ENV}"
        extra = "ignore" # TODO: find a better solution to do this

settings = Settings()
