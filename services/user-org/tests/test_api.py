"""
API Integration Tests for User-Org Service
Tests organization, company, event, and task endpoints.
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


class TestOrganizationEndpoints:
    """Test organization management endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_organization_details(
        self, 
        client: AsyncClient, 
        sample_user_data: dict,
        mock_email_service
    ):
        """Test getting organization details."""
        # Signup creates org
        signup_response = await client.post("/auth/signup", json=sample_user_data)
        token = signup_response.json()["access_token"]
        org = signup_response.json()["organization"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"/org/{org['id']}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_user_data["org_name"]
    
    @pytest.mark.asyncio
    async def test_list_organization_members(
        self, 
        client: AsyncClient, 
        sample_user_data: dict,
        mock_email_service
    ):
        """Test listing organization members."""
        signup_response = await client.post("/auth/signup", json=sample_user_data)
        token = signup_response.json()["access_token"]
        org = signup_response.json()["organization"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"/org/{org['id']}/members", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1  # At least the creator


class TestCompanyEndpoints:
    """Test company tracking endpoints."""
    
    @pytest.mark.asyncio
    async def test_add_company_to_track(
        self, 
        client: AsyncClient, 
        sample_user_data: dict,
        sample_company_data: dict,
        mock_email_service
    ):
        """Test adding a company to track."""
        signup_response = await client.post("/auth/signup", json=sample_user_data)
        token = signup_response.json()["access_token"]
        org = signup_response.json()["organization"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(
            f"/org/{org['id']}/companies",
            json=sample_company_data,
            headers=headers
        )
        
        assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_list_tracked_companies(
        self, 
        client: AsyncClient, 
        sample_user_data: dict,
        mock_email_service
    ):
        """Test listing tracked companies."""
        signup_response = await client.post("/auth/signup", json=sample_user_data)
        token = signup_response.json()["access_token"]
        org = signup_response.json()["organization"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"/org/{org['id']}/companies", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestTaskEndpoints:
    """Test task management endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_task(
        self, 
        client: AsyncClient, 
        sample_user_data: dict,
        sample_task_data: dict,
        mock_email_service
    ):
        """Test creating a new task."""
        signup_response = await client.post("/auth/signup", json=sample_user_data)
        token = signup_response.json()["access_token"]
        org = signup_response.json()["organization"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(
            f"/org/{org['id']}/tasks",
            json=sample_task_data,
            headers=headers
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["title"] == sample_task_data["title"]
    
    @pytest.mark.asyncio
    async def test_list_tasks(
        self, 
        client: AsyncClient, 
        sample_user_data: dict,
        mock_email_service
    ):
        """Test listing tasks."""
        signup_response = await client.post("/auth/signup", json=sample_user_data)
        token = signup_response.json()["access_token"]
        org = signup_response.json()["organization"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"/org/{org['id']}/tasks", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestEventEndpoints:
    """Test event endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_events(
        self, 
        client: AsyncClient, 
        sample_user_data: dict,
        mock_email_service
    ):
        """Test listing events for organization."""
        signup_response = await client.post("/auth/signup", json=sample_user_data)
        token = signup_response.json()["access_token"]
        org = signup_response.json()["organization"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"/org/{org['id']}/events", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAccessControl:
    """Test access control and authorization."""
    
    @pytest.mark.asyncio
    async def test_cannot_access_other_org(
        self, 
        client: AsyncClient, 
        sample_user_data: dict,
        mock_email_service
    ):
        """Test that users cannot access other organizations."""
        # Create first user/org
        signup_response = await client.post("/auth/signup", json=sample_user_data)
        token = signup_response.json()["access_token"]
        
        # Try to access random org ID
        random_org_id = str(uuid4())
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"/org/{random_org_id}", headers=headers)
        
        assert response.status_code in [403, 404]  # Forbidden or Not Found
    
    @pytest.mark.asyncio
    async def test_unauthenticated_access_denied(self, client: AsyncClient):
        """Test that unauthenticated requests are denied."""
        random_org_id = str(uuid4())
        response = await client.get(f"/org/{random_org_id}")
        
        assert response.status_code == 401


class TestInputValidation:
    """Test input validation."""
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client: AsyncClient):
        """Test that missing required fields return validation error."""
        incomplete_data = {"email": "test@example.com"}  # Missing password, name, org_name
        response = await client.post("/auth/signup", json=incomplete_data)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_invalid_uuid_format(
        self, 
        client: AsyncClient, 
        sample_user_data: dict,
        mock_email_service
    ):
        """Test that invalid UUID format returns error."""
        signup_response = await client.post("/auth/signup", json=sample_user_data)
        token = signup_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/org/not-a-valid-uuid", headers=headers)
        
        assert response.status_code in [400, 422]  # Bad Request or Validation Error
