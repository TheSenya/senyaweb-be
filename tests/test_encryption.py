
# tests/test_encryption.py
import pytest
import json
import time
from unittest.mock import patch
from jwcrypto import jwk, jwe
from fastapi.testclient import TestClient

# Import the app
import app.main
# We need to patch 'server_key' in this module
import app.middleware.encryption 

# ─────────────────────────────────────────────────────────
# TEST DATA
# ─────────────────────────────────────────────────────────

import os
from pathlib import Path

# Load keys from the test directory
current_dir = os.path.dirname(os.path.abspath(__file__))

private_key_path = os.path.join(current_dir, "test_files", "test_private.pem")
if not os.path.exists(private_key_path):
    print(f"ERROR: File does not exist: {private_key_path}")

with open(private_key_path, "rb") as f:
    TEST_SERVER_PRIVATE_KEY_PEM = f.read()

with open(os.path.join(current_dir, "test_files", "test_public.pem"), "rb") as f:
    TEST_SERVER_PUBLIC_KEY_PEM = f.read()

# Create the JWK objects
test_server_key = jwk.JWK.from_pem(TEST_SERVER_PRIVATE_KEY_PEM)
test_server_public_key = jwk.JWK.from_pem(TEST_SERVER_PUBLIC_KEY_PEM)

# ─────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────

def create_encrypted_payload(data: dict, client_key_pair=None):
    """
    Helper to simulate a client encrypting data for the server.
    """
    wrapper = {
        "ts": int(time.time() * 1000),
        "payload": data
    }

    if client_key_pair:
        wrapper["client_public_key"] = client_key_pair.export_public(as_dict=True)

    wrapper_json = json.dumps(wrapper)

    # IMPORTANT: The Server Key is RSA. 
    # INBOUND request must use RSA-OAEP logic (or whatever matches RSA).
    # OUTBOUND response uses the Client's EC key (ECDH).
    
    protected_header = {"alg": "RSA-OAEP-256", "enc": "A256GCM"}
    
    # We encrypt using the TEST server PUBLIC key
    jwetoken = jwe.JWE(wrapper_json.encode('utf-8'), 
                       json.dumps(protected_header))
    jwetoken.add_recipient(test_server_public_key)
    
    return jwetoken.serialize(compact=True)


def decrypt_response(encrypted_response: str, client_key_pair):
    """
    Helper to Decrypt the server's response using the client's private key.
    """
    jwetoken = jwe.JWE()
    jwetoken.deserialize(encrypted_response)
    jwetoken.decrypt(client_key_pair)
    return jwetoken.payload

# ─────────────────────────────────────────────────────────
# TEST SUITE
# ─────────────────────────────────────────────────────────

class TestEncryptionMiddleware:
    
    @pytest.fixture(autouse=True)
    def patch_server_key(self):
        """
        Mock the 'server_key' in the encryption module to use our known Test Key.
        This ensures we don't need the real production keys to run tests.
        """
        with patch("app.middleware.encryption.server_key", test_server_key):
            yield

    @pytest.fixture
    def client(self):
        return TestClient(app.main.app)

    @pytest.fixture
    def client_key_pair(self):
        """Generates a temporary EC key pair for the 'client' (test runner)"""
        return jwk.JWK.generate(kty='EC', crv='P-256')

    # ─────────────────────────────────────────────────────────
    # Test 1: Full Round Trip 
    # ─────────────────────────────────────────────────────────
    def test_encryption_round_trip(self, client, client_key_pair):
        secret_data = {"passcode": "wrong_but_valid"}
        encrypted_body = create_encrypted_payload(secret_data, client_key_pair)

        response = client.post(
            "/auth/passcode",
            json={"content": encrypted_body}
        )

        assert response.status_code == 401
        resp_json = response.json()
        assert "content" in resp_json

        decrypted_bytes = decrypt_response(resp_json["content"], client_key_pair)
        decrypted_data = json.loads(decrypted_bytes)

        assert "detail" in decrypted_data
        assert decrypted_data["detail"] == "Invalid passcode"

    # ─────────────────────────────────────────────────────────
    # Test 2: Replay Attack (Old Timestamp)
    # ─────────────────────────────────────────────────────────
    def test_replay_attack_old_timestamp(self, client):
        old_ts = int((time.time() - 70) * 1000)
        wrapper = {
            "ts": old_ts,
            "payload": {"foo": "bar"}
        }
        
        protected_header = {"alg": "RSA-OAEP-256", "enc": "A256GCM"}
        # We encrypt using the TEST server PUBLIC key
        jwetoken = jwe.JWE(json.dumps(wrapper).encode('utf-8'), 
                           json.dumps(protected_header))
        jwetoken.add_recipient(test_server_public_key)
        encrypted_body = jwetoken.serialize(compact=True)

        response = client.post(
            "/auth/passcode",
            json={"content": encrypted_body}
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Request expired"

    # ─────────────────────────────────────────────────────────
    # Test 3: Replay Attack (Future Timestamp)
    # ─────────────────────────────────────────────────────────
    def test_replay_attack_future_timestamp(self, client):
        future_ts = int((time.time() + 10) * 1000)
        wrapper = {
            "ts": future_ts,
            "payload": {"foo": "bar"}
        }
        
        protected_header = {"alg": "RSA-OAEP-256", "enc": "A256GCM"}
        # We encrypt using the TEST server PUBLIC key
        jwetoken = jwe.JWE(json.dumps(wrapper).encode('utf-8'), 
                           json.dumps(protected_header))
        jwetoken.add_recipient(test_server_public_key)
        encrypted_body = jwetoken.serialize(compact=True)

        response = client.post(
            "/auth/passcode", 
            json={"content": encrypted_body}
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Request expired"

    # ─────────────────────────────────────────────────────────
    # Test 4: Malformed/Garbage Payload
    # ─────────────────────────────────────────────────────────
    def test_malformed_jwe(self, client):
        response = client.post(
            "/auth/passcode",
            json={"content": "not_a_valid_jwe_token"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Handshake Failed"

    # ─────────────────────────────────────────────────────────
    # Test 5: Missing 'content' field
    # ─────────────────────────────────────────────────────────
    def test_missing_content_structure(self, client):
        response = client.post(
            "/auth/passcode",
            json={"wrong_field": "some_data"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Content is missing"
