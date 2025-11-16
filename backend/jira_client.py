"""Jira API client with OAuth support, auto-refresh, and proper async HTTP."""
import os
import httpx
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from crypto_utils import get_encryptor

logger = logging.getLogger(__name__)


class JiraAPIError(Exception):
    """Base exception for Jira API errors."""
    pass


class JiraRateLimitError(JiraAPIError):
    """Raised when API rate limit is exceeded."""
    def __init__(self, retry_after: int, message: str = "Rate limit exceeded"):
        self.retry_after = retry_after
        super().__init__(message)


class JiraAuthError(JiraAPIError):
    """Raised when authentication fails."""
    pass


class JiraAPIClient:
    """Client for making authenticated requests to Jira Cloud API with proper async HTTP."""
    
    BASE_AUTH_URL = "https://auth.atlassian.com"
    BASE_API_URL = "https://api.atlassian.com"
    DEFAULT_TIMEOUT = 30.0
    MAX_RETRIES = 3
    
    def __init__(self, db: Any):
        """Initialize the Jira API client."""
        self.db = db
        self.client_id = os.environ.get('JIRA_CLIENT_ID')
        self.client_secret = os.environ.get('JIRA_CLIENT_SECRET')
        self.redirect_uri = os.environ.get('JIRA_REDIRECT_URI')
        self.encryptor = get_encryptor()
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client instance."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.DEFAULT_TIMEOUT),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._http_client
    
    async def close(self):
        """Close the HTTP client."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
    
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
        
        client = await self._get_http_client()
        headers = {"Content-Type": "application/json"}
        
        try:
            response = await client.post(token_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error exchanging code for token: {e.response.status_code} - {e.response.text}")
            raise JiraAuthError(f"Failed to exchange code for token: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error exchanging code for token: {e}")
            raise JiraAPIError(f"Network error during token exchange: {str(e)}")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh the access token using the refresh token."""
        token_url = f"{self.BASE_AUTH_URL}/oauth/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token
        }
        
        client = await self._get_http_client()
        headers = {"Content-Type": "application/json"}
        
        try:
            response = await client.post(token_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error refreshing token: {e.response.status_code} - {e.response.text}")
            raise JiraAuthError(f"Failed to refresh token: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error refreshing token: {e}")
            raise JiraAPIError(f"Network error during token refresh: {str(e)}")
    
    async def get_accessible_resources(self, access_token: str) -> List[Dict[str, Any]]:
        """Get list of accessible Jira/Confluence resources."""
        url = f"{self.BASE_API_URL}/oauth/token/accessible-resources"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        client = await self._get_http_client()
        
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting accessible resources: {e.response.status_code}")
            raise JiraAPIError(f"Failed to get accessible resources: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error getting accessible resources: {e}")
            raise JiraAPIError(f"Network error getting accessible resources: {str(e)}")
    
    async def get_connection_by_id(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get a Jira connection from the database."""
        try:
            connection = await self.db.jira_connections.find_one(
                {"id": connection_id},
                {"_id": 0}
            )
            return connection
        except Exception as e:
            logger.error(f"Database error getting connection: {e}")
            raise JiraAPIError(f"Failed to retrieve connection from database: {str(e)}")
    
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
            
            try:
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
                
                logger.info(f"Successfully refreshed token for connection {connection_id}")
                return new_access_token
            except JiraAuthError as e:
                logger.error(f"Auth error refreshing token for connection {connection_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error refreshing token for connection {connection_id}: {e}")
                raise JiraAPIError(f"Failed to refresh token: {str(e)}")
        
        # Token is still valid, decrypt and return
        return self.encryptor.decrypt(connection['enc_access_token'])
    
    async def make_api_request(
        self,
        connection_id: str,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request to Jira with retry logic and rate limit handling.
        
        Implements:
        - Automatic token refresh on 401
        - Exponential backoff on 429 (rate limit)
        - Retry on 5xx errors
        - Proper timeout handling
        """
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
        
        # Get HTTP client
        client = await self._get_http_client()
        
        # Request timeout
        request_timeout = timeout or self.DEFAULT_TIMEOUT
        
        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(self.MAX_RETRIES):
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    timeout=request_timeout
                )
                
                # Handle 401 (unauthorized) - refresh token and retry
                if response.status_code == 401:
                    if attempt == 0:  # Only retry once for 401
                        logger.warning(f"Got 401, refreshing token for connection {connection_id}")
                        
                        # Force refresh by setting expires_at to past
                        await self.db.jira_connections.update_one(
                            {"id": connection_id},
                            {"$set": {"expires_at": datetime.now(timezone.utc).isoformat()}}
                        )
                        
                        # Get new token and retry
                        access_token = await self.ensure_valid_token(connection_id)
                        headers["Authorization"] = f"Bearer {access_token}"
                        continue
                    else:
                        raise JiraAuthError(f"Authentication failed after retry for connection {connection_id}")
                
                # Handle 429 (rate limit) - exponential backoff with Retry-After header
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited (429) on attempt {attempt + 1}, waiting {retry_after}s (Retry-After header)")
                    
                    if attempt < self.MAX_RETRIES - 1:
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        raise JiraRateLimitError(
                            retry_after=retry_after,
                            message=f"Rate limit exceeded after {self.MAX_RETRIES} attempts"
                        )
                
                # Handle 5xx errors - exponential backoff
                if 500 <= response.status_code < 600:
                    if attempt < self.MAX_RETRIES - 1:
                        backoff_time = 2 ** attempt  # 1s, 2s, 4s
                        logger.warning(f"Server error {response.status_code} on attempt {attempt + 1}, retrying in {backoff_time}s")
                        await asyncio.sleep(backoff_time)
                        continue
                    else:
                        response.raise_for_status()
                
                # Raise for other HTTP errors
                response.raise_for_status()
                
                # Success - return JSON response
                return response.json()
                
            except httpx.HTTPStatusError as e:
                last_exception = e
                error_body = e.response.text if hasattr(e.response, 'text') else 'No response body'
                logger.error(f"HTTP error on attempt {attempt + 1}: {e.response.status_code} - Response: {error_body[:500]}")
                if attempt == self.MAX_RETRIES - 1:
                    raise JiraAPIError(f"HTTP error after {self.MAX_RETRIES} attempts: {e.response.status_code} - {error_body[:200]}")
                
            except httpx.TimeoutException as e:
                last_exception = e
                logger.error(f"Timeout on attempt {attempt + 1}: {e}")
                if attempt == self.MAX_RETRIES - 1:
                    raise JiraAPIError(f"Request timeout after {self.MAX_RETRIES} attempts")
                await asyncio.sleep(2 ** attempt)
                
            except httpx.RequestError as e:
                last_exception = e
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
                if attempt == self.MAX_RETRIES - 1:
                    raise JiraAPIError(f"Network error after {self.MAX_RETRIES} attempts: {str(e)}")
                await asyncio.sleep(2 ** attempt)
        
        # Should never reach here, but just in case
        if last_exception:
            raise JiraAPIError(f"Request failed after {self.MAX_RETRIES} attempts") from last_exception
        raise JiraAPIError(f"Request failed after {self.MAX_RETRIES} attempts")
