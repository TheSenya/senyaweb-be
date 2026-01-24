import os
import pytest
from unittest.mock import patch
from app.core.config import Settings

# Helper to clear singleton or re-instantiate Settings
def get_settings(env_vars=None):
    with patch.dict(os.environ, env_vars or {}, clear=True):
        return Settings()

class TestConfigKeyLoading:

    def test_load_private_key_from_env(self):
        """
        Test that PRIVATE_KEY is loaded from environment variable if present.
        """
        env = {
            "PRIVATE_KEY": "env_private_key",
            "ENV": "test"
        }
        with patch.dict(os.environ, env):
            settings = Settings()
            assert settings.PRIVATE_KEY == "env_private_key"
            # It should mostly ignore file if key is present

    def test_load_private_key_from_file_real(self):
        """
        Test that PRIVATE_KEY is loaded from real private.pem file if env var is missing.
        """
        # Ensure no env var
        with patch.dict(os.environ, {"ENV": "test"}, clear=True):
            # In this environment, private.pem exists in be/
            # and defaults are set to "private.pem"
            # make sure CWD is be/
            
            settings = Settings()
            
            # Check content
            assert settings.PRIVATE_KEY.startswith("-----BEGIN PRIVATE KEY-----")
            
            # Check if env var was set as requested by user
            assert os.environ.get("PRIVATE_KEY") == settings.PRIVATE_KEY

    def test_load_public_key_from_file_real(self):
        """
        Test that PUBLIC_KEY is loaded from real public.pem file.
        """
        with patch.dict(os.environ, {"ENV": "test"}, clear=True):
            settings = Settings()
            assert settings.PUBLIC_KEY.startswith("-----BEGIN PUBLIC KEY-----")
            assert os.environ.get("PUBLIC_KEY") == settings.PUBLIC_KEY
