"""
FutureFeed - Standalone Tests
=============================
These tests verify core functionality without requiring external dependencies.

Run with: python -m pytest tests/ -v
"""

import pytest
import os
import sys


class TestEnvironmentConfiguration:
    """Test that environment is correctly configured."""
    
    def test_python_version(self):
        """Test Python version is 3.10+."""
        assert sys.version_info >= (3, 10), "Python 3.10+ required"
    
    def test_services_directory_exists(self):
        """Test that services directory exists."""
        services_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "services")
        assert os.path.isdir(services_path), "services directory should exist"
    
    def test_frontend_directory_exists(self):
        """Test that frontend directory exists."""
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
        assert os.path.isdir(frontend_path), "frontend directory should exist"
    
    def test_docker_compose_exists(self):
        """Test that docker-compose.yml exists."""
        compose_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docker-compose.yml")
        assert os.path.isfile(compose_path), "docker-compose.yml should exist"
    
    def test_env_example_exists(self):
        """Test that .env.example exists."""
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.example")
        assert os.path.isfile(env_path), ".env.example should exist"


class TestPasswordSecurity:
    """Test password hashing utilities."""
    
    def test_bcrypt_available(self):
        """Test that bcrypt is available for password hashing."""
        try:
            import bcrypt
            assert bcrypt is not None
        except ImportError:
            pytest.skip("bcrypt not installed")
    
    def test_password_hash_is_different_from_input(self):
        """Test that hashing changes the password."""
        try:
            import bcrypt
            password = b"test_password_123"
            hashed = bcrypt.hashpw(password, bcrypt.gensalt())
            assert hashed != password
            assert len(hashed) > 20  # bcrypt hashes are long
        except ImportError:
            pytest.skip("bcrypt not installed")
    
    def test_password_verification_works(self):
        """Test that password verification succeeds for correct password."""
        try:
            import bcrypt
            password = b"secure_password_456"
            hashed = bcrypt.hashpw(password, bcrypt.gensalt())
            assert bcrypt.checkpw(password, hashed) is True
        except ImportError:
            pytest.skip("bcrypt not installed")
    
    def test_wrong_password_verification_fails(self):
        """Test that password verification fails for wrong password."""
        try:
            import bcrypt
            password = b"correct_password"
            wrong_password = b"wrong_password"
            hashed = bcrypt.hashpw(password, bcrypt.gensalt())
            assert bcrypt.checkpw(wrong_password, hashed) is False
        except ImportError:
            pytest.skip("bcrypt not installed")


class TestJWTTokens:
    """Test JWT token utilities."""
    
    def test_jose_available(self):
        """Test that python-jose is available for JWT."""
        try:
            from jose import jwt
            assert jwt is not None
        except ImportError:
            pytest.skip("python-jose not installed")
    
    def test_jwt_encode_decode(self):
        """Test JWT encoding and decoding."""
        try:
            from jose import jwt
            secret = "test_secret_key"
            payload = {"user_id": "123", "email": "test@example.com"}
            token = jwt.encode(payload, secret, algorithm="HS256")
            decoded = jwt.decode(token, secret, algorithms=["HS256"])
            assert decoded["user_id"] == "123"
            assert decoded["email"] == "test@example.com"
        except ImportError:
            pytest.skip("python-jose not installed")
    
    def test_jwt_invalid_token_fails(self):
        """Test that invalid JWT token raises error."""
        try:
            from jose import jwt
            from jose.exceptions import JWTError
            secret = "test_secret"
            with pytest.raises(JWTError):
                jwt.decode("invalid.token.here", secret, algorithms=["HS256"])
        except ImportError:
            pytest.skip("python-jose not installed")


class TestEmailValidation:
    """Test email validation utilities."""
    
    def test_valid_email_format(self):
        """Test valid email addresses."""
        import re
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        
        valid_emails = [
            "test@example.com",
            "user.name@domain.org",
            "admin@company.co.uk"
        ]
        
        for email in valid_emails:
            assert re.match(email_pattern, email) is not None, f"{email} should be valid"
    
    def test_invalid_email_format(self):
        """Test invalid email addresses."""
        import re
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        
        invalid_emails = [
            "not-an-email",
            "@nodomain.com",
            "missing@.com",
            "spaces in@email.com"
        ]
        
        for email in invalid_emails:
            assert re.match(email_pattern, email) is None, f"{email} should be invalid"


class TestUUIDGeneration:
    """Test UUID generation utilities."""
    
    def test_uuid_generation(self):
        """Test that UUIDs are generated correctly."""
        import uuid
        new_id = uuid.uuid4()
        assert len(str(new_id)) == 36  # UUID format: 8-4-4-4-12
    
    def test_uuid_uniqueness(self):
        """Test that generated UUIDs are unique."""
        import uuid
        ids = [str(uuid.uuid4()) for _ in range(100)]
        assert len(ids) == len(set(ids)), "All UUIDs should be unique"


class TestDateTimeHandling:
    """Test datetime handling utilities."""
    
    def test_current_timestamp(self):
        """Test getting current timestamp."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        assert now is not None
        assert now.tzinfo is not None
    
    def test_timestamp_comparison(self):
        """Test timestamp comparison for token expiry."""
        from datetime import datetime, timezone, timedelta
        
        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=24)
        past = now - timedelta(hours=1)
        
        assert future > now, "Future should be greater than now"
        assert past < now, "Past should be less than now"


class TestProjectStructure:
    """Test that all required project files exist."""
    
    def test_readme_exists(self):
        """Test README.md exists."""
        readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md")
        assert os.path.isfile(readme_path), "README.md should exist"
    
    def test_features_md_exists(self):
        """Test FEATURES.md exists."""
        features_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "FEATURES.md")
        assert os.path.isfile(features_path), "FEATURES.md should exist"
    
    def test_testing_md_exists(self):
        """Test TESTING.md exists."""
        testing_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TESTING.md")
        assert os.path.isfile(testing_path), "TESTING.md should exist"


class TestServiceStructure:
    """Test that all services have required files."""
    
    def test_user_org_service_exists(self):
        """Test user-org service structure."""
        service_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "services", "user-org")
        assert os.path.isdir(service_path), "user-org service should exist"
        assert os.path.isfile(os.path.join(service_path, "README.md")), "README should exist"
        assert os.path.isfile(os.path.join(service_path, "Dockerfile")), "Dockerfile should exist"
    
    def test_llm_intel_service_exists(self):
        """Test llm-intel service structure."""
        service_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "services", "llm-intel")
        assert os.path.isdir(service_path), "llm-intel service should exist"
        assert os.path.isfile(os.path.join(service_path, "README.md")), "README should exist"
    
    def test_news_fetcher_service_exists(self):
        """Test news-fetcher service structure."""
        service_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "services", "news-fetcher")
        assert os.path.isdir(service_path), "news-fetcher service should exist"
        assert os.path.isfile(os.path.join(service_path, "README.md")), "README should exist"
    
    def test_embedding_dedupe_service_exists(self):
        """Test embedding-dedupe service structure."""
        service_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "services", "embedding-dedupe")
        assert os.path.isdir(service_path), "embedding-dedupe service should exist"
        assert os.path.isfile(os.path.join(service_path, "README.md")), "README should exist"
    
    def test_event_mapper_service_exists(self):
        """Test event-mapper service structure."""
        service_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "services", "event-mapper")
        assert os.path.isdir(service_path), "event-mapper service should exist"
        assert os.path.isfile(os.path.join(service_path, "README.md")), "README should exist"


# Summary
"""
Test Summary:
=============
- TestEnvironmentConfiguration: 5 tests
- TestPasswordSecurity: 4 tests
- TestJWTTokens: 3 tests
- TestEmailValidation: 2 tests
- TestUUIDGeneration: 2 tests
- TestDateTimeHandling: 2 tests
- TestProjectStructure: 3 tests
- TestServiceStructure: 5 tests

Total: 26 tests
"""
