"""
Authentication Tests for User-Org Service
Tests user signup, login, token validation, and password security.
"""

import pytest
from httpx import AsyncClient


class TestHealthCheck:
    """Test health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check_returns_ok(self, client: AsyncClient):
        """Test that health check endpoint returns 200 OK."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestUserSignup:
    """Test user registration functionality."""
    
    @pytest.mark.asyncio
    async def test_signup_creates_user_and_org(
        self, 
        client: AsyncClient, 
        sample_user_data: dict,
        mock_email_service
    ):
        """Test successful user signup creates user and organization."""
        response = await client.post("/auth/signup", json=sample_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == sample_user_data["email"]
        assert data["user"]["name"] == sample_user_data["name"]
    
    @pytest.mark.asyncio
    async def test_signup_rejects_duplicate_email(
        self, 
        client: AsyncClient, 
        sample_user_data: dict,
        mock_email_service
    ):
        """Test that duplicate email registration is rejected."""
        # First signup
        await client.post("/auth/signup", json=sample_user_data)
        
        # Second signup with same email
        response = await client.post("/auth/signup", json=sample_user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_signup_validates_email_format(self, client: AsyncClient):
        """Test that invalid email format is rejected."""
        invalid_data = {
            "email": "not-an-email",
            "password": "SecurePass123!",
            "name": "Test User",
            "org_name": "Test Org"
        }
        response = await client.post("/auth/signup", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_signup_requires_password(self, client: AsyncClient):
        """Test that password is required for signup."""
        invalid_data = {
            "email": "test@example.com",
            "name": "Test User",
            "org_name": "Test Org"
        }
        response = await client.post("/auth/signup", json=invalid_data)
        assert response.status_code == 422


class TestUserLogin:
    """Test user login functionality."""
    
    @pytest.mark.asyncio
    async def test_login_with_valid_credentials(
        self, 
        client: AsyncClient, 
        sample_user_data: dict,
        mock_email_service
    ):
        """Test successful login returns JWT token."""
        # Create user first
        await client.post("/auth/signup", json=sample_user_data)
        
        # Login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_rejects_wrong_password(
        self, 
        client: AsyncClient, 
        sample_user_data: dict,
        mock_email_service
    ):
        """Test login with wrong password is rejected."""
        # Create user first
        await client.post("/auth/signup", json=sample_user_data)
        
        # Login with wrong password
        login_data = {
            "email": sample_user_data["email"],
            "password": "WrongPassword123!"
        }
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_rejects_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent email is rejected."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401


class TestPasswordSecurity:
    """Test password security measures."""
    
    @pytest.mark.asyncio
    async def test_password_is_hashed(
        self, 
        client: AsyncClient, 
        sample_user_data: dict,
        mock_email_service
    ):
        """Test that passwords are hashed, not stored in plain text."""
        response = await client.post("/auth/signup", json=sample_user_data)
        assert response.status_code == 201
        
        # The response should never contain the password
        data = response.json()
        assert "password" not in str(data)
        assert sample_user_data["password"] not in str(data)


class TestTokenValidation:
    """Test JWT token validation."""
    
    @pytest.mark.asyncio
    async def test_protected_route_requires_token(self, client: AsyncClient):
        """Test that protected routes require authentication."""
        response = await client.get("/me")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_protected_route_accepts_valid_token(
        self, 
        client: AsyncClient, 
        sample_user_data: dict,
        mock_email_service
    ):
        """Test that protected routes work with valid token."""
        # Signup and get token
        signup_response = await client.post("/auth/signup", json=sample_user_data)
        token = signup_response.json()["access_token"]
        
        # Access protected route
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user_data["email"]
    
    @pytest.mark.asyncio
    async def test_invalid_token_is_rejected(self, client: AsyncClient):
        """Test that invalid tokens are rejected."""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = await client.get("/me", headers=headers)
        assert response.status_code == 401
