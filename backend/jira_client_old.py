"""Jira API client with OAuth support and auto-refresh."""
import os
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from crypto_utils import get_encryptor

logger = logging.getLogger(__name__)


class JiraAPIClient:
    """Client for making authenticated requests to Jira Cloud API."""
    
    BASE_AUTH_URL = "https://auth.atlassian.com"
    BASE_API_URL = "https://api.atlassian.com"
    
    def __init__(self, db: Any):
        """Initialize the Jira API client."""
        self.db = db
        self.client_id = os.environ.get('JIRA_CLIENT_ID')
        self.client_secret = os.environ.get('JIRA_CLIENT_SECRET')
        self.redirect_uri = os.environ.get('JIRA_REDIRECT_URI')
        self.encryptor = get_encryptor()
    
    def get_authorization_url(self, state: str = "random_state") -> str:
        """Generate the OAuth authorization URL."""
        scopes = "read:jira-work read:jira-user offline_access"
        params = {
            "audience": "api.atlassian.com",
            "client_id": self.client_id,
            "scope": scopes,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "response_type": "code",
            "prompt": "consent"
        }
        
        from urllib.parse import urlencode
        query_string = urlencode(params)
        return f"{self.BASE_AUTH_URL}/authorize?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        token_url = f"{self.BASE_AUTH_URL}/oauth/token"
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(token_url, json=payload, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh the access token using the refresh token."""
        token_url = f"{self.BASE_AUTH_URL}/oauth/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token
        }
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(token_url, json=payload, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    async def get_accessible_resources(self, access_token: str) -> List[Dict[str, Any]]:
        """Get list of accessible Jira/Confluence resources."""
        url = f"{self.BASE_API_URL}/oauth/token/accessible-resources"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    async def get_connection_by_id(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get a Jira connection from the database."""
        connection = await self.db.jira_connections.find_one(
            {"id": connection_id},
            {"_id": 0}
        )
        return connection
    
    async def ensure_valid_token(self, connection_id: str) -> str:
        """Ensure the connection has a valid access token, refreshing if necessary."""
        connection = await self.get_connection_by_id(connection_id)
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")
        
        # Check if token is expired or will expire soon (within 5 minutes)
        expires_at = datetime.fromisoformat(connection['expires_at']) if isinstance(connection['expires_at'], str) else connection['expires_at']
        now = datetime.now(timezone.utc)
        
        if expires_at <= now + timedelta(minutes=5):
            logger.info(f"Token expired or expiring soon for connection {connection_id}, refreshing...")
            
            # Decrypt refresh token
            refresh_token = self.encryptor.decrypt(connection['enc_refresh_token'])
            
            # Refresh the token
            token_response = await self.refresh_access_token(refresh_token)
            
            # Encrypt new tokens
            new_access_token = token_response['access_token']
            enc_access_token = self.encryptor.encrypt(new_access_token)
            
            # Update connection in database
            new_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_response['expires_in'])
            await self.db.jira_connections.update_one(
                {"id": connection_id},
                {
                    "$set": {
                        "enc_access_token": enc_access_token,
                        "expires_at": new_expires_at.isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            return new_access_token
        
        # Token is still valid, decrypt and return
        return self.encryptor.decrypt(connection['enc_access_token'])
    
    async def make_api_request(
        self,
        connection_id: str,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated API request to Jira."""
        # Get valid access token
        access_token = await self.ensure_valid_token(connection_id)
        
        # Get connection details
        connection = await self.get_connection_by_id(connection_id)
        cloud_id = connection['cloud_id']
        
        # Construct full URL
        url = f"{self.BASE_API_URL}/ex/jira/{cloud_id}{endpoint}"
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        if json_data:
            headers["Content-Type"] = "application/json"
        
        # Make request
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data
        )
        
        # Handle 401 (retry once after refresh)
        if response.status_code == 401:
            logger.warning(f"Got 401, attempting token refresh for connection {connection_id}")
            # Force refresh by setting expires_at to past
            await self.db.jira_connections.update_one(
                {"id": connection_id},
                {"$set": {"expires_at": datetime.now(timezone.utc).isoformat()}}
            )
            
            # Get new token and retry
            access_token = await self.ensure_valid_token(connection_id)
            headers["Authorization"] = f"Bearer {access_token}"
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            )
        
        response.raise_for_status()
        return response.json()
