# tests/test_rate_limit.py
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app
from app.middleware import security
from app.middleware.security import Blocked, BLOCKED, MAX_FAILURES
from app.core.config import settings

client = TestClient(app)

class TestRateLimiting:
    """Test suite for rate limiting functionality"""
    
    def setup_method(self):
        """Clear blocked IPs before each test"""
        security.BLOCKED.clear()
        # Patch the passcode setting directly
        settings.PASSCODE = "correct_passcode"
    
    # ─────────────────────────────────────────────────────────
    # Test 1: Successful login doesn't increment attempts
    # ─────────────────────────────────────────────────────────
    def test_successful_login_no_block(self):
        """Valid passcode should not count as failure"""
        response = client.post(
            "/auth/passcode",
            json={"passcode": "correct_passcode"}  # Use your actual passcode
        )
        
        assert response.status_code == 200
        assert len(BLOCKED) == 0  # No IPs should be tracked
    
    # ─────────────────────────────────────────────────────────
    # Test 2: Failed login increments attempts
    # ─────────────────────────────────────────────────────────
    def test_failed_login_increments_attempts(self):
        """Wrong passcode should increment attempt counter"""
        response = client.post(
            "/auth/passcode",
            json={"passcode": "wrong_password"}
        )
        
        assert response.status_code == 401  # After you fix auth to raise 401
        assert "testclient" in BLOCKED or len(BLOCKED) == 1
        
        # Get the blocked entry (TestClient uses 'testclient' as host)
        blocked_ip = list(BLOCKED.keys())[0]
        assert BLOCKED[blocked_ip].attempts == 1
    
    # ─────────────────────────────────────────────────────────
    # Test 3: User gets blocked after MAX_FAILURES
    # ─────────────────────────────────────────────────────────
    def test_block_after_max_failures(self):
        """User should be blocked after 5 failed attempts"""
        # Make MAX_FAILURES failed attempts
        for i in range(MAX_FAILURES):
            response = client.post(
                "/auth/passcode",
                json={"passcode": "wrong"}
            )
        
        blocked_ip = list(BLOCKED.keys())[0]
        assert BLOCKED[blocked_ip].attempts == MAX_FAILURES
        assert BLOCKED[blocked_ip].block_timeout is not None
        
        # Next request should be blocked with 403
        response = client.post(
            "/auth/passcode",
            json={"passcode": "wrong"}
        )
        assert response.status_code == 403
        assert "Too many attempts" in response.json()["detail"]
    
    # ─────────────────────────────────────────────────────────
    # Test 4: Block expires after timeout
    # ─────────────────────────────────────────────────────────
    def test_block_expires_after_timeout(self):
        """User should be unblocked after timeout expires"""
        # Manually create an expired block
        test_ip = "testclient"
        BLOCKED[test_ip] = Blocked(
            ip=test_ip,
            user_agent="test",
            attempts=5,
            block_timeout=datetime.now() - timedelta(seconds=1),  # Already expired
            first_attempt_time=datetime.now(),
            last_attempt_time=datetime.now()
        )
        
        # Request should succeed (block expired)
        response = client.post(
            "/auth/passcode",
            json={"passcode": "correct_passcode"}
        )
        assert response.status_code == 200
    
    # ─────────────────────────────────────────────────────────
    # Test 5: Active block prevents access
    # ─────────────────────────────────────────────────────────
    def test_active_block_prevents_access(self):
        """User with active block should get 403"""
        test_ip = "testclient"
        BLOCKED[test_ip] = Blocked(
            ip=test_ip,
            user_agent="test",
            attempts=5,
            block_timeout=datetime.now() + timedelta(minutes=15),  # Still active
            first_attempt_time=datetime.now(),
            last_attempt_time=datetime.now()
        )
        
        response = client.post(
            "/auth/passcode",
            json={"passcode": "correct_passcode"}
        )
        assert response.status_code == 403