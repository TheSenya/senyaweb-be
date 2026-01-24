from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from jwcrypto import jwk, jwe

import json  # Standard library for parsing JSON data
import time  # Standard library for getting the current system time (for replay protection)
import asyncio

from fastapi import Request

from app.core.config import settings

# only allows for requests that are 60 seconds or younger
MAX_REQUEST_AGE = 60

# convert the PEM string into a usable Key Object for the crypto library.
try:
    if settings.PRIVATE_KEY:
        server_key = jwk.JWK.from_pem(settings.PRIVATE_KEY.encode('utf-8'))
    else:
        print("WARNING: PRIVATE_KEY is missing in settings. Encryption middleware will fail.")
        server_key = None
except Exception as e:
    print(f"CRITICAL: Failed to load PRIVATE_KEY: {e}")
    server_key = None

class EncrpytionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that encrpyts outgoing traffic and decrpyts incoming network traffic
    """

    async def dispatch(self, request: Request, call_next):

        # Skip docs/options/health checks
        if request.method == "OPTIONS" or request.url.path in ["/docs", "/openapi.json"]:
            return await call_next(request)


        # ---------------------------------------------------------
        # A. INBOUND: DECRYPT & VALIDATE TIMESTAMP
        # ---------------------------------------------------------
        client_pub_key_json = None

        try:
            # 1. read the raw encrypted body
            body_bytes = await request.body()

            if body_bytes:
                # 2. PARSE JSON WRAPPER
                # the frontend sends valid JSON like { "content": "eyJh..." }, we need to extract what is located in content
                # what json.loads does is it translates either bytes or strings to python readable objects
                body_json = json.loads(body_bytes)
                encrypted_content = body_json.get("content")
                
                # check if the encrypted content is there
                if not encrypted_content:
                    return JSONResponse(status_code=400, content={"detail": "Content is missing"})
                
                # 3. DECRYPT JWE
                jwetoken = jwe.JWE()  # Create a JWE object
                jwetoken.deserialize(encrypted_content)  # Load the encrypted string
                jwetoken.decrypt(server_key)  # Decrypt it using our private key

                # 4. PARSE DECRYPTED PAYLOAD
                decrypted_wrapper = json.loads(jwetoken.payload)

                # --- SECURITY CHECK: REPLAY PROTECTION ---

                # get the timestamp sent by the frontend (defaults to 0 if missing).
                request_ts = decrypted_wrapper.get("ts", 0)

                # get current server time in milliseconds.
                current_ts = int(time.time() * 1000)

                # Calculate how old the request is (in seconds).
                age_seconds = (current_ts - request_ts) / 1000

                # if request is older than 60s, or "in the future" by >5s (clock skew), reject it.
                if age_seconds > MAX_REQUEST_AGE or age_seconds < -5:
                    print(f"SECURITY ALERT: Replay Attack Detected. Age: {age_seconds}s")
                    return JSONResponse(status_code=403, content={"detail": "Request expired"})

                # 5. EXTRACT DATA
                # WHY: Separate the actual API data from the crypto metadata.
                actual_payload = decrypted_wrapper.get("payload") # The real data (e.g., login creds)
                client_pub_key_json = decrypted_wrapper.get("client_public_key") # The key to reply with
                
                # 6. INJECT INTO REQUEST
                # WHY: FastAPI has not routed the request to the endpoint yet.
                # We overwrite the raw body with the *decrypted* JSON so the endpoint 
                # receives clean data and doesn't know encryption happened.
                async def get_body():
                    return json.dumps(actual_payload).encode()
                
                # Override the internal Request method to return our clean data.
                request._body = json.dumps(actual_payload).encode()
                
        except Exception as e:
            # Catch-all for bad crypto, bad JSON, or tampering.
            print(f"Decryption Error: {e}")
            return JSONResponse(status_code=400, content={"detail": "Handshake Failed"})

        
        # ---------------------------------------------------------
        # B. APP PROCESSING
        # ---------------------------------------------------------
        
        # WHY: Pass the request to the actual FastAPI endpoint (e.g., /login).
        # The endpoint processes the data and returns a 'response' object.
        response = await call_next(request)

        # ---------------------------------------------------------
        # C. OUTBOUND: ENCRYPT RESPONSE
        # ---------------------------------------------------------
        
        # Check: Did we get a client key? And is there a body to encrypt?
        if client_pub_key_json and hasattr(response, "body_iterator"):
            
            # 1. CONSUME RESPONSE
            # WHY: FastAPI streams responses. We must read the whole thing into memory to encrypt it.
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            try:
                # 2. PREPARE CLIENT KEY
                # WHY: Reconstitute the client's temporary public key object.
                client_key = jwk.JWK(**client_pub_key_json)
                
                # 3. ENCRYPT RESPONSE
                # WHY: Lock the response so only the specific client who asked can read it.
                protected_header = {"alg": "ECDH-ES+A256KW", "enc": "A256GCM"}
                jwetoken = jwe.JWE(response_body, json.dumps(protected_header))
                jwetoken.add_recipient(client_key)
                encrypted_response = jwetoken.serialize(compact=True)
                
                # 4. RETURN NEW RESPONSE
                # WHY: We discard the original cleartext response and return the encrypted JSON wrapper.
                return JSONResponse(
                    content={"content": encrypted_response},
                    status_code=response.status_code
                )
            except Exception as e:
                print(f"Encryption Error: {e}")
                return Response(status_code=500, content="Secure Channel Error")

        # If no encryption was needed (e.g. OPTIONS request), return original response.
        return response