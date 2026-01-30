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

    CORS_ORIGINS: list[str] | str = []

    #### API KEYS ####
    GOOGLE_AI_STUDIO_API_KEY: str = ""
    OPENROUTER_KEY: str = ""
    
    # Private Key for JWE Encryption
    PRIVATE_KEY: str = ""
    PRIVATE_KEY_PATH: str = "private.pem" # Path to the private key file
    PUBLIC_KEY: str = ""
    PUBLIC_KEY_PATH: str = "public.pem" # Path to the public key file

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 5

    JWT_SECRET_KEY: str= ""

    ALGORITHM: str = "HS256"

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
        extra = "ignore" # TODO: find a better solution to do this

    @model_validator(mode="after")
    def validate_env_vars_all_loaded(self) -> "Settings":
        """Validate that all required environment variables are loaded.
        In dev/local environments, print the actual values.
        In production, print that each env was set without showing values.
        """
        is_dev_or_local = ENV.lower() in ("dev", "local")
        validation_messages = {}
        missing_required = []

        # Check CORS_ORIGINS
        if self.CORS_ORIGINS:
            if is_dev_or_local:
                validation_messages["CORS_ORIGINS"] = f"✅ CORS_ORIGINS: {self.CORS_ORIGINS}"
            else:
                validation_messages["CORS_ORIGINS"] = "✅ CORS_ORIGINS: Set"
        else:
            validation_messages["CORS_ORIGINS"] = "❌ CORS_ORIGINS: Not set"

        # Check GOOGLE_AI_STUDIO_API_KEY
        if self.GOOGLE_AI_STUDIO_API_KEY:
            if is_dev_or_local:
                validation_messages["GOOGLE_AI_STUDIO_API_KEY"] = f"✅ GOOGLE_AI_STUDIO_API_KEY: {self.GOOGLE_AI_STUDIO_API_KEY}"
            else:
                validation_messages["GOOGLE_AI_STUDIO_API_KEY"] = "✅ GOOGLE_AI_STUDIO_API_KEY: Set"
        else:
            validation_messages["GOOGLE_AI_STUDIO_API_KEY"] = "⚠️ GOOGLE_AI_STUDIO_API_KEY: Not set (optional)"

        # Check OPENROUTER_KEY
        if self.OPENROUTER_KEY:
            if is_dev_or_local:
                validation_messages["OPENROUTER_KEY"] = f"✅ OPENROUTER_KEY: {self.OPENROUTER_KEY}"
            else:
                validation_messages["OPENROUTER_KEY"] = "✅ OPENROUTER_KEY: Set"
        else:
            validation_messages["OPENROUTER_KEY"] = "⚠️ OPENROUTER_KEY: Not set (optional)"

        # Check PRIVATE_KEY (required)
        if self.PRIVATE_KEY:
            if is_dev_or_local:
                validation_messages["PRIVATE_KEY"] = f"✅ PRIVATE_KEY: {self.PRIVATE_KEY[:50]}..."
            else:
                validation_messages["PRIVATE_KEY"] = "✅ PRIVATE_KEY: Set"
        else:
            validation_messages["PRIVATE_KEY"] = "❌ PRIVATE_KEY: Not set"
            missing_required.append("PRIVATE_KEY")

        # Check PUBLIC_KEY (required)
        if self.PUBLIC_KEY:
            if is_dev_or_local:
                validation_messages["PUBLIC_KEY"] = f"✅ PUBLIC_KEY: {self.PUBLIC_KEY[:50]}..."
            else:
                validation_messages["PUBLIC_KEY"] = "✅ PUBLIC_KEY: Set"
        else:
            validation_messages["PUBLIC_KEY"] = "❌ PUBLIC_KEY: Not set"
            missing_required.append("PUBLIC_KEY")

        # Check JWT_SECRET_KEY (required)
        if self.JWT_SECRET_KEY:
            if is_dev_or_local:
                validation_messages["JWT_SECRET_KEY"] = f"✅ JWT_SECRET_KEY: {self.JWT_SECRET_KEY}"
            else:
                validation_messages["JWT_SECRET_KEY"] = "✅ JWT_SECRET_KEY: Set"
        else:
            validation_messages["JWT_SECRET_KEY"] = "❌ JWT_SECRET_KEY: Not set"
            missing_required.append("JWT_SECRET_KEY")

        # Always print validation messages
        env_label = "DEV/LOCAL" if is_dev_or_local else "PRODUCTION"
        print("\n" + "=" * 50)
        print(f"🔧 Environment Variables Validation ({env_label})")
        print("=" * 50)
        for key, message in validation_messages.items():
            print(message)
        print("=" * 50 + "\n")

        # Raise error if required variables are missing
        if missing_required:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_required)}")

        return self


settings = Settings()
