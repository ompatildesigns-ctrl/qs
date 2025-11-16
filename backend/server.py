from fastapi import FastAPI, APIRouter, HTTPException, Query, BackgroundTasks, Header, Depends, Request
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import asyncio
import httpx
import redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import json

from models import (
    OAuthAuthorizeResponse,
    OAuthCallbackResponse,
    AccessibleResource,
    JiraSyncJob,
    JiraSyncJobCreate,
    SyncStats,
    JiraConnection,
    JiraProject,
    JiraIssue,
    JiraStatus,
    JiraUser
)
from auth_models import User, UserCreate, UserLogin, UserResponse, TokenResponse
from auth import hash_password, verify_password, create_access_token, get_user_id_from_token
from jira_client import JiraAPIClient, JiraAPIError, JiraRateLimitError, JiraAuthError
from crypto_utils import get_encryptor
from analytics import JiraAnalytics
from investigation_analytics import InvestigationAnalytics
from financial_analytics import FinancialAnalytics
from actions import ActionEngine
from bottleneck_finder import BottleneckFinder
from insights_engine import InsightsEngine
from people_bottleneck_analyzer import PeopleBottleneckAnalyzer
from executive_report_generator import ExecutiveReportGenerator


# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis setup for caching (enterprise scale)
try:
    redis_client = redis.Redis(
        host=os.environ.get('REDIS_HOST', 'localhost'),
        port=int(os.environ.get('REDIS_PORT', 6379)),
        decode_responses=True,
        socket_connect_timeout=5
    )
    redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info("Redis connected successfully for caching")
except Exception as e:
    logger.warning(f"Redis not available, caching disabled: {e}")
    redis_client = None
    REDIS_AVAILABLE = False

# Rate limiter setup (prevent abuse at scale)
limiter = Limiter(key_func=get_remote_address)


# JWT Middleware - Extract user_id from all authenticated requests
async def get_current_user_id(authorization: str = Header(None)) -> str:
    """
    Dependency to get current user ID from JWT token.
    Use this in all protected endpoints.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated - missing token")
    
    token = authorization.split(" ")[1]
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user_id


# Optional auth - for endpoints that work with or without auth
async def get_current_user_id_optional(authorization: str = Header(None)) -> Optional[str]:
    """Optional authentication - returns None if not authenticated."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    return get_user_id_from_token(token)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', '').strip()
if not mongo_url or not (mongo_url.startswith('mongodb://') or mongo_url.startswith('mongodb+srv://')):
    logger.error(f"Invalid MONGO_URL: '{mongo_url}' (length: {len(mongo_url) if mongo_url else 0})")
    raise ValueError(f"MONGO_URL must start with 'mongodb://' or 'mongodb+srv://'. Got: '{mongo_url[:50] if mongo_url else 'EMPTY'}...'")
logger.info(f"MongoDB connection URL: {mongo_url[:30]}...")
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize Jira client and analytics
jira_client = JiraAPIClient(db)
analytics = JiraAnalytics(db)
investigation = InvestigationAnalytics(db)
financial = FinancialAnalytics(db)
actions = ActionEngine(db, jira_client)
bottleneck_finder = BottleneckFinder(db)
insights_engine = InsightsEngine(db)
people_analyzer = PeopleBottleneckAnalyzer(db)
executive_report = ExecutiveReportGenerator(db, bottleneck_finder, insights_engine, people_analyzer, financial)


# Helper function to get user's connection
async def get_user_connection(user_id: str):
    """Get Jira connection for authenticated user."""
    connection = await db.jira_connections.find_one({"user_id": user_id}, {"_id": 0})
    if not connection:
        raise HTTPException(status_code=404, detail="No Jira connection found. Please connect your Jira account first.")
    return connection


# Cache helper functions
def get_cache_key(prefix: str, *args) -> str:
    """Generate cache key from prefix and arguments."""
    return f"{prefix}:" + ":".join(str(arg) for arg in args)


async def get_cached_data(key: str):
    """Get data from Redis cache."""
    if not REDIS_AVAILABLE:
        return None
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning(f"Cache get error: {e}")
    return None


async def set_cached_data(key: str, data: dict, ttl: int = 300):
    """Set data in Redis cache with TTL (default 5 minutes)."""
    if not REDIS_AVAILABLE:
        return
    try:
        redis_client.setex(key, ttl, json.dumps(data))
    except Exception as e:
        logger.warning(f"Cache set error: {e}")


# Health check
@api_router.get("/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Health check endpoint."""
    return {"status": "healthy", "service": "jira-sync-backend", "redis": REDIS_AVAILABLE}


# User Authentication Endpoints
@api_router.post("/auth/signup", response_model=TokenResponse)
@limiter.limit("5/minute")
async def signup(request: Request, user_data: UserCreate):
    """
    Create new user account.
    
    Returns JWT token and user info.
    """
    try:
        # Check if email already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Create user
        user = User(
            email=user_data.email,
            password_hash=password_hash,
            full_name=user_data.full_name
        )
        
        # Save to database
        await db.users.insert_one(user.model_dump())
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user.id})
        
        # Return token and user info
        return TokenResponse(
            access_token=access_token,
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                email_verified=user.email_verified,
                created_at=user.created_at,
                last_login=user.last_login
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/auth/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, credentials: UserLogin):
    """
    Login existing user.
    
    Returns JWT token and user info.
    """
    try:
        # Find user by email
        user_doc = await db.users.find_one({"email": credentials.email})
        if not user_doc:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        if not verify_password(credentials.password, user_doc["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Update last login
        await db.users.update_one(
            {"id": user_doc["id"]},
            {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user_doc["id"]})
        
        # Return token and user info
        return TokenResponse(
            access_token=access_token,
            user=UserResponse(
                id=user_doc["id"],
                email=user_doc["email"],
                full_name=user_doc.get("full_name"),
                email_verified=user_doc.get("email_verified", False),
                created_at=user_doc["created_at"],
                last_login=user_doc.get("last_login")
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user(authorization: str = Header(None)):
    """
    Get current authenticated user info from JWT token.
    
    Requires Authorization header: Bearer <token>
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Get user from database
    user_doc = await db.users.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user_doc["id"],
        email=user_doc["email"],
        full_name=user_doc.get("full_name"),
        email_verified=user_doc.get("email_verified", False),
        created_at=user_doc["created_at"],
        last_login=user_doc.get("last_login")
    )


# Database Index Creation
async def create_database_indexes():
    """Create database indexes for optimal query performance."""
    try:
        logger.info("Creating database indexes...")
        
        # jira_connections indexes
        await db.jira_connections.create_index("id", unique=True)
        await db.jira_connections.create_index("cloud_id")
        
        # jira_projects indexes
        await db.jira_projects.create_index([("connection_id", 1), ("project_id", 1)], unique=True)
        await db.jira_projects.create_index("connection_id")
        
        # jira_issues indexes
        await db.jira_issues.create_index([("connection_id", 1), ("issue_id", 1)], unique=True)
        await db.jira_issues.create_index("connection_id")
        await db.jira_issues.create_index("updated")  # For delta sync
        await db.jira_issues.create_index("project_id")
        await db.jira_issues.create_index("resolved")  # For cycle time queries
        await db.jira_issues.create_index([("connection_id", 1), ("status", 1)])  # For status filtering
        await db.jira_issues.create_index([("connection_id", 1), ("assignee", 1)])  # For workload queries
        await db.jira_issues.create_index([("connection_id", 1), ("resolved", 1)])  # For resolved queries
        
        # jira_statuses indexes
        await db.jira_statuses.create_index([("connection_id", 1), ("status_id", 1)], unique=True)
        await db.jira_statuses.create_index("connection_id")
        
        # jira_users indexes
        await db.jira_users.create_index([("connection_id", 1), ("account_id", 1)], unique=True)
        await db.jira_users.create_index("connection_id")
        
        # jira_sync_jobs indexes
        await db.jira_sync_jobs.create_index("connection_id")
        await db.jira_sync_jobs.create_index("status")
        await db.jira_sync_jobs.create_index("id", unique=True)
        
        logger.info("Database indexes created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")
        return False


# OAuth Endpoints
@api_router.get("/auth/jira/authorize", response_model=OAuthAuthorizeResponse)
async def jira_authorize(user_id: str = Query(None)):
    """
    Initiate Jira OAuth flow.
    
    Args:
        user_id: Optional user ID to associate connection with (for multi-tenant)
    """
    try:
        # Store user_id in state parameter for OAuth callback
        authorization_url = jira_client.get_authorization_url(state="jira_oauth_state")
        state = "jira_oauth_state"
        
        # If user_id provided, encode it in state for callback
        if user_id:
            state_with_user = f"{state}:{user_id}"
            # Re-build URL with new state
            authorization_url = authorization_url.replace(f"state={state}", f"state={state_with_user}")
            state = state_with_user
        
        # Store state in database for verification
        await db.oauth_states.insert_one({
            "state": state,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return OAuthAuthorizeResponse(authorize_url=authorization_url)
    except Exception as e:
        logger.error(f"Error initiating OAuth: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/auth/jira/callback")
async def jira_callback(code: str = Query(...), state: str = Query(...)):
    """
    Handle the OAuth callback from Jira.
    Exchanges the authorization code for tokens and stores them securely.
    Links connection to user_id if provided in state.
    """
    try:
        # Extract user_id from state if present (format: "oauth_state:user_id")
        user_id = None
        if ":" in state:
            state_parts = state.split(":")
            user_id = state_parts[1] if len(state_parts) > 1 else None
        
        # Exchange code for tokens
        token_response = await jira_client.exchange_code_for_token(code)
        
        access_token = token_response['access_token']
        refresh_token = token_response['refresh_token']
        expires_in = token_response['expires_in']
        scopes = token_response['scope'].split() if 'scope' in token_response else []
        
        # Get accessible resources to find cloud_id
        resources = await jira_client.get_accessible_resources(access_token)
        
        if not resources:
            raise HTTPException(status_code=400, detail="No accessible Jira resources found")
        
        # Use the first resource (for MVP, single-site setup)
        resource = resources[0]
        cloud_id = resource['id']
        site_url = resource['url']
        
        # Encrypt tokens
        encryptor = get_encryptor()
        enc_access_token = encryptor.encrypt(access_token)
        enc_refresh_token = encryptor.encrypt(refresh_token)
        
        # Calculate expiration time
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        
        # Create connection object with user_id
        connection = JiraConnection(
            user_id=user_id,  # Link to user for multi-tenant
            site_url=site_url,
            cloud_id=cloud_id,
            scopes=scopes,
            enc_access_token=enc_access_token,
            enc_refresh_token=enc_refresh_token,
            expires_at=expires_at
        )
        
        # Store in database
        connection_dict = connection.model_dump()
        connection_dict['expires_at'] = connection_dict['expires_at'].isoformat()
        connection_dict['created_at'] = connection_dict['created_at'].isoformat()
        connection_dict['updated_at'] = connection_dict['updated_at'].isoformat()
        
        # Check if user already has a connection (disconnect old one first)
        if user_id:
            existing_user_connection = await db.jira_connections.find_one({"user_id": user_id})
            if existing_user_connection:
                # Delete old connection and its data
                old_connection_id = existing_user_connection['id']
                await db.jira_issues.delete_many({"connection_id": old_connection_id})
                await db.jira_users.delete_many({"connection_id": old_connection_id})
                await db.jira_projects.delete_many({"connection_id": old_connection_id})
                await db.jira_statuses.delete_many({"connection_id": old_connection_id})
                await db.jira_sync_jobs.delete_many({"connection_id": old_connection_id})
                await db.jira_connections.delete_one({"id": old_connection_id})
                logger.info(f"Deleted old connection {old_connection_id} for user {user_id}")
        
        # Insert new connection
        await db.jira_connections.insert_one(connection_dict)
        connection_id = connection.id
        
        logger.info(f"Successfully stored Jira connection {connection_id} for user {user_id} at {site_url}")
        
        # Auto-login: Create JWT token for user if they don't have one
        if user_id:
            user_doc = await db.users.find_one({"id": user_id})
            if user_doc:
                # Create JWT token for auto-login
                access_token = create_access_token(data={"sub": user_id})
                
                # Redirect to frontend with connection info AND JWT token
                frontend_url = os.environ['FRONTEND_URL']  # No fallback - must be set
                redirect_url = f"{frontend_url}?connection_id={connection_id}&cloud_id={cloud_id}&oauth_success=true&token={access_token}"
                
                return RedirectResponse(url=redirect_url)
        
        # Fallback: No user_id (legacy)
        frontend_url = os.environ['FRONTEND_URL']  # No fallback - must be set
        redirect_url = f"{frontend_url}?connection_id={connection_id}&cloud_id={cloud_id}&oauth_success=true"
        
        return RedirectResponse(url=redirect_url)
    
    except JiraAuthError as e:
        logger.error(f"Auth error during OAuth callback: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    except JiraAPIError as e:
        logger.error(f"API error during OAuth callback: {e}")
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error during OAuth callback: {e.response.status_code}")
        raise HTTPException(status_code=400, detail=f"OAuth HTTP error: {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Request error during OAuth callback: {e}")
        raise HTTPException(status_code=503, detail=f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during OAuth callback: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@api_router.get("/auth/jira/connection")
async def get_current_connection(user_id: str = Depends(get_current_user_id_optional)):
    """
    Check if current user has an existing Jira connection.
    Returns connection if found, 404 if not.
    Supports both authenticated (with user_id) and legacy (without) modes.
    """
    try:
        # Multi-tenant: Filter by user_id if authenticated
        if user_id:
            connection = await db.jira_connections.find_one({"user_id": user_id}, {"_id": 0, "enc_access_token": 0, "enc_refresh_token": 0})
        else:
            # Legacy: Get any connection (for backward compatibility during migration)
            connection = await db.jira_connections.find_one({}, {"_id": 0, "enc_access_token": 0, "enc_refresh_token": 0})
        
        if not connection:
            raise HTTPException(status_code=404, detail="No Jira connection found")
        
        return connection
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Jira connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/jira/disconnect")
async def disconnect_jira(user_id: str = Depends(get_current_user_id)):
    """
    Disconnect user's Jira account and delete all associated data.
    User stays logged in - this only removes Jira connection.
    """
    try:
        # Find user's connection
        connection = await db.jira_connections.find_one({"user_id": user_id})
        
        if not connection:
            raise HTTPException(status_code=404, detail="No Jira connection to disconnect")
        
        connection_id = connection['id']
        
        # Delete all associated data
        issues_deleted = await db.jira_issues.delete_many({"connection_id": connection_id})
        users_deleted = await db.jira_users.delete_many({"connection_id": connection_id})
        projects_deleted = await db.jira_projects.delete_many({"connection_id": connection_id})
        statuses_deleted = await db.jira_statuses.delete_many({"connection_id": connection_id})
        jobs_deleted = await db.jira_sync_jobs.delete_many({"connection_id": connection_id})
        connection_deleted = await db.jira_connections.delete_one({"id": connection_id})
        
        logger.info(f"Disconnected Jira for user {user_id}: deleted {issues_deleted.deleted_count} issues, {connection_deleted.deleted_count} connections")
        
        return {
            "message": "Jira disconnected successfully",
            "deleted": {
                "issues": issues_deleted.deleted_count,
                "users": users_deleted.deleted_count,
                "projects": projects_deleted.deleted_count,
                "statuses": statuses_deleted.deleted_count,
                "sync_jobs": jobs_deleted.deleted_count,
                "connections": connection_deleted.deleted_count
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting Jira: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/auth/jira/connection/{connection_id}")
async def get_connection_details(connection_id: str):
    """
    Get details for a specific Jira connection.
    """
    try:
        connection = await db.jira_connections.find_one({"id": connection_id}, {"_id": 0})
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Return connection info (without tokens)
        return {
            "id": connection['id'],
            "cloud_id": connection['cloud_id'],
            "site_url": connection['site_url'],
            "created_at": connection['created_at'],
            "updated_at": connection['updated_at'],
            "last_full_sync_at": connection.get('last_full_sync_at')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching connection details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/auth/jira/refresh")
async def jira_refresh_token(connection_id: str):
    """
    Manually refresh the access token for a connection.
    """
    try:
        # This will automatically refresh if needed
        await jira_client.ensure_valid_token(connection_id)
        return {"message": "Token refreshed successfully", "token_valid": True}
    except ValueError as e:
        logger.error(f"Connection not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except JiraAuthError as e:
        logger.error(f"Auth error refreshing token: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except JiraAPIError as e:
        logger.error(f"API error refreshing token: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error refreshing token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/jira/resources", response_model=List[AccessibleResource])
async def get_jira_resources():
    """
    Get all accessible Jira resources for the authenticated user.
    Useful for debugging and verifying OAuth connection.
    """
    try:
        # Get the first (or only) connection
        connection = await db.jira_connections.find_one({}, {"_id": 0})
        if not connection:
            raise HTTPException(status_code=404, detail="No Jira connection found. Please authorize first.")
        
        # Get fresh access token
        access_token = await jira_client.ensure_valid_token(connection['id'])
        
        # Fetch accessible resources
        resources = await jira_client.get_accessible_resources(access_token)
        
        return [
            AccessibleResource(
                id=r['id'],
                name=r['name'],
                url=r['url'],
                scopes=r.get('scopes', []),
                avatar_url=r.get('avatarUrl')
            )
            for r in resources
        ]
    except HTTPException:
        raise
    except JiraAuthError as e:
        logger.error(f"Auth error fetching resources: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except JiraAPIError as e:
        logger.error(f"API error fetching resources: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error fetching resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Sync Endpoints
async def run_full_sync(connection_id: str, job_id: str):
    """Background task to run a full sync for a Jira connection."""
    logger.info(f"Starting full sync for connection {connection_id}, job {job_id}")
    
    try:
        # Update job status to running
        await db.jira_sync_jobs.update_one(
            {"id": job_id},
            {
                "$set": {
                    "status": "running",
                    "started_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        stats = {
            "projects": 0,
            "issues": 0,
            "statuses": 0,
            "users": 0,
            "api_calls": 0
        }
        
        # Get connection
        connection = await jira_client.get_connection_by_id(connection_id)
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")
        
        cloud_id = connection['cloud_id']
        
        # Sync Projects
        logger.info("Syncing projects...")
        try:
            projects_response = await jira_client.make_api_request(
                connection_id,
                "/rest/api/3/project"
            )
            stats['api_calls'] += 1
            
            for project in projects_response:
                project_doc = JiraProject(
                    connection_id=connection_id,
                    cloud_id=cloud_id,
                    project_id=project['id'],
                    key=project['key'],
                    name=project['name'],
                    project_type=project.get('projectTypeKey'),
                    data=project
                )
                
                # Upsert project
                project_dict = project_doc.model_dump()
                project_dict['fetched_at'] = project_dict['fetched_at'].isoformat()
                project_dict['updated_at'] = project_dict['updated_at'].isoformat()
                
                await db.jira_projects.update_one(
                    {"connection_id": connection_id, "project_id": project['id']},
                    {"$set": project_dict},
                    upsert=True
                )
                stats['projects'] += 1
            
            logger.info(f"Synced {stats['projects']} projects")
        except JiraRateLimitError as e:
            logger.error(f"Rate limit error syncing projects: {e}, retry_after={e.retry_after}s")
            stats['errors'] = stats.get('errors', [])
            stats['errors'].append(f"Projects: Rate limited, retry after {e.retry_after}s")
        except JiraAPIError as e:
            logger.error(f"API error syncing projects: {e}")
            stats['errors'] = stats.get('errors', [])
            stats['errors'].append(f"Projects: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error syncing projects: {e}")
            stats['errors'] = stats.get('errors', [])
            stats['errors'].append(f"Projects: {str(e)}")
        
        # Sync Issues (last 90 days)
        logger.info("Syncing issues from last 90 days...")
        try:
            max_results = 100
            next_page_token = None
            
            while True:
                # JQL query must have a restriction (not unbounded)
                # New pagination uses nextPageToken instead of startAt
                request_body = {
                    "jql": "updated >= -90d ORDER BY updated DESC",
                    "maxResults": max_results,
                    "fields": ["summary", "status", "issuetype", "priority", "assignee", "reporter", "created", "updated", "resolutiondate", "project"]
                }
                
                # Add nextPageToken for subsequent pages
                if next_page_token:
                    request_body["nextPageToken"] = next_page_token
                
                issues_response = await jira_client.make_api_request(
                    connection_id,
                    "/rest/api/3/search/jql",
                    method="POST",
                    json_data=request_body
                )
                stats['api_calls'] += 1
                
                issues = issues_response.get('issues', [])
                if not issues:
                    break
                
                for issue in issues:
                    fields = issue.get('fields', {})
                    
                    issue_doc = JiraIssue(
                        connection_id=connection_id,
                        cloud_id=cloud_id,
                        issue_id=issue['id'],
                        key=issue['key'],
                        project_id=fields.get('project', {}).get('id', ''),
                        summary=fields.get('summary'),
                        status=fields.get('status', {}).get('name'),
                        issue_type=fields.get('issuetype', {}).get('name'),
                        priority=fields.get('priority', {}).get('name') if fields.get('priority') else None,
                        assignee=fields.get('assignee', {}).get('displayName') if fields.get('assignee') else None,
                        reporter=fields.get('reporter', {}).get('displayName') if fields.get('reporter') else None,
                        created=datetime.fromisoformat(fields['created'].replace('Z', '+00:00')) if fields.get('created') else None,
                        updated=datetime.fromisoformat(fields['updated'].replace('Z', '+00:00')) if fields.get('updated') else None,
                        resolved=datetime.fromisoformat(fields['resolutiondate'].replace('Z', '+00:00')) if fields.get('resolutiondate') else None,
                        data=issue
                    )
                    
                    # Upsert issue
                    issue_dict = issue_doc.model_dump()
                    issue_dict['fetched_at'] = issue_dict['fetched_at'].isoformat()
                    issue_dict['updated_at'] = issue_dict['updated_at'].isoformat()
                    if issue_dict.get('created'):
                        issue_dict['created'] = issue_dict['created'].isoformat()
                    if issue_dict.get('updated'):
                        issue_dict['updated'] = issue_dict['updated'].isoformat()
                    if issue_dict.get('resolved'):
                        issue_dict['resolved'] = issue_dict['resolved'].isoformat()
                    
                    await db.jira_issues.update_one(
                        {"connection_id": connection_id, "issue_id": issue['id']},
                        {"$set": issue_dict},
                        upsert=True
                    )
                    stats['issues'] += 1
                
                # Check for next page token
                next_page_token = issues_response.get('nextPageToken')
                if not next_page_token:
                    break
                
                # Rate limiting - wait 200ms between requests (non-blocking)
                await asyncio.sleep(0.2)
            
            logger.info(f"Synced {stats['issues']} issues")
        except Exception as e:
            logger.error(f"Error syncing issues: {e}")
        
        # Sync Statuses
        logger.info("Syncing statuses...")
        try:
            statuses_response = await jira_client.make_api_request(
                connection_id,
                "/rest/api/3/status"
            )
            stats['api_calls'] += 1
            
            for status in statuses_response:
                status_doc = JiraStatus(
                    connection_id=connection_id,
                    cloud_id=cloud_id,
                    status_id=status['id'],
                    name=status['name'],
                    status_category=status.get('statusCategory', {}).get('name'),
                    data=status
                )
                
                # Upsert status
                status_dict = status_doc.model_dump()
                status_dict['fetched_at'] = status_dict['fetched_at'].isoformat()
                status_dict['updated_at'] = status_dict['updated_at'].isoformat()
                
                await db.jira_statuses.update_one(
                    {"connection_id": connection_id, "status_id": status['id']},
                    {"$set": status_dict},
                    upsert=True
                )
                stats['statuses'] += 1
            
            logger.info(f"Synced {stats['statuses']} statuses")
        except Exception as e:
            logger.error(f"Error syncing statuses: {e}")
        
        # Sync Users
        logger.info("Syncing users...")
        try:
            start_at = 0
            max_results = 100
            
            while True:
                users_response = await jira_client.make_api_request(
                    connection_id,
                    "/rest/api/3/users/search",
                    params={
                        "startAt": start_at,
                        "maxResults": max_results
                    }
                )
                stats['api_calls'] += 1
                
                if not users_response:
                    break
                
                for user in users_response:
                    user_doc = JiraUser(
                        connection_id=connection_id,
                        cloud_id=cloud_id,
                        account_id=user['accountId'],
                        display_name=user['displayName'],
                        active=user.get('active', True),
                        data=user
                    )
                    
                    # Upsert user
                    user_dict = user_doc.model_dump()
                    user_dict['fetched_at'] = user_dict['fetched_at'].isoformat()
                    user_dict['updated_at'] = user_dict['updated_at'].isoformat()
                    
                    await db.jira_users.update_one(
                        {"connection_id": connection_id, "account_id": user['accountId']},
                        {"$set": user_dict},
                        upsert=True
                    )
                    stats['users'] += 1
                
                # Check if there are more users
                if len(users_response) < max_results:
                    break
                
                start_at += max_results
                
                # Rate limiting (non-blocking)
                await asyncio.sleep(0.2)
            
            logger.info(f"Synced {stats['users']} users")
        except Exception as e:
            logger.error(f"Error syncing users: {e}")
        
        # Update connection's last_full_sync_at
        await db.jira_connections.update_one(
            {"id": connection_id},
            {
                "$set": {
                    "last_full_sync_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # Update job status to success
        await db.jira_sync_jobs.update_one(
            {"id": job_id},
            {
                "$set": {
                    "status": "success",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "stats": stats
                }
            }
        )
        
        logger.info(f"Full sync completed successfully for connection {connection_id}")
        logger.info(f"Stats: {stats}")
    
    except Exception as e:
        logger.error(f"Error during full sync: {e}")
        
        # Update job status to error
        await db.jira_sync_jobs.update_one(
            {"id": job_id},
            {
                "$set": {
                    "status": "error",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "error": str(e)
                }
            }
        )


@api_router.post("/sync/start", response_model=JiraSyncJob)
async def start_sync(
    background_tasks: BackgroundTasks,
    connection_id: str = Query(..., description="Connection ID to sync"),
    mode: str = Query("full", regex="^(full|delta)$"),
    user_id: str = Depends(get_current_user_id_optional)
):
    """
    Start a sync job for the Jira connection.
    Mode can be 'full' (all data from last 90 days) or 'delta' (only changes).
    """
    try:
        # Get the SPECIFIC connection by ID (and verify user owns it if authenticated)
        if user_id:
            connection = await db.jira_connections.find_one(
                {"id": connection_id, "user_id": user_id},
                {"_id": 0}
            )
        else:
            connection = await db.jira_connections.find_one(
                {"id": connection_id},
                {"_id": 0}
            )
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found or you don't have permission to access it")
        
        connection_id = connection['id']
        
        # Check if there's already a running job
        running_job = await db.jira_sync_jobs.find_one(
            {"connection_id": connection_id, "status": "running"}
        )
        if running_job:
            raise HTTPException(status_code=409, detail="A sync job is already running for this connection")
        
        # Create sync job
        job = JiraSyncJob(
            connection_id=connection_id,
            sync_type=mode,
            status="queued"
        )
        
        job_dict = job.model_dump()
        job_dict['created_at'] = job_dict['created_at'].isoformat()
        
        await db.jira_sync_jobs.insert_one(job_dict)
        
        # Start background task
        if mode == "full":
            background_tasks.add_task(run_full_sync, connection_id, job.id)
        else:
            # Delta sync not implemented yet
            raise HTTPException(status_code=501, detail="Delta sync not implemented yet")
        
        logger.info(f"Queued {mode} sync job {job.id} for connection {connection_id}")
        
        return job
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/sync/status/{job_id}", response_model=JiraSyncJob)
async def get_sync_status(job_id: str):
    """Get the status of a sync job."""
    try:
        job = await db.jira_sync_jobs.find_one({"id": job_id}, {"_id": 0})
        if not job:
            raise HTTPException(status_code=404, detail="Sync job not found")
        
        return JiraSyncJob(**job)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/sync/stats", response_model=SyncStats)
async def get_sync_stats(user_id: str = Depends(get_current_user_id_optional)):
    """Get sync statistics (supports multi-tenant and legacy modes)."""
    try:
        # Multi-tenant: Get user's connection
        if user_id:
            connection = await get_user_connection(user_id)
            connection_id = connection['id']
        else:
            # Legacy: Get any connection
            connection = await db.jira_connections.find_one({})
            if not connection:
                return SyncStats(projects=0, issues=0, statuses=0, users=0)
            connection_id = connection['id']
        
        # Count data for this connection only
        projects = await db.jira_projects.count_documents({"connection_id": connection_id})
        issues = await db.jira_issues.count_documents({"connection_id": connection_id})
        statuses = await db.jira_statuses.count_documents({"connection_id": connection_id})
        users = await db.jira_users.count_documents({"connection_id": connection_id})
        
        return SyncStats(
            projects=projects,
            issues=issues,
            statuses=statuses,
            users=users,
            connection_id=connection_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/admin/create-indexes")
async def create_indexes():
    """Create database indexes for optimal query performance. (Admin endpoint)"""
    try:
        success = await create_database_indexes()
        if success:
            return {"message": "Database indexes created successfully", "status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create some indexes")
    except Exception as e:
        logger.error(f"Error in create_indexes endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# CEO Analytics Endpoints
@api_router.get("/analytics/executive-summary")
@limiter.limit("30/minute")
async def get_executive_summary(request: Request, user_id: str = Depends(get_current_user_id)):
    """Get executive summary. REQUIRES AUTH. Cached for 5 minutes."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        connection_id = connection['id']
        
        # Check cache first
        cache_key = get_cache_key("exec_summary", connection_id)
        cached = await get_cached_data(cache_key)
        if cached:
            logger.info(f"Cache HIT: executive summary for {connection_id}")
            return cached
        
        # Cache miss - compute
        logger.info(f"Cache MISS: executive summary for {connection_id}")
        summary = await analytics.get_executive_summary(connection_id)
        
        # Store in cache (5 min TTL)
        await set_cached_data(cache_key, summary, ttl=300)
        
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting executive summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/analytics/bottlenecks")
@limiter.limit("30/minute")
async def get_bottleneck_analysis(request: Request, days: int = Query(30, ge=7, le=90), user_id: str = Depends(get_current_user_id)):
    """Get bottleneck analysis: issues stuck in statuses. REQUIRES AUTH. Cached."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        connection_id = connection['id']
        
        # Check cache
        cache_key = get_cache_key("bottlenecks", connection_id, days)
        cached = await get_cached_data(cache_key)
        if cached:
            return cached
        
        analysis = await analytics.get_bottleneck_analysis(connection_id, days=days)
        await set_cached_data(cache_key, analysis, ttl=300)
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bottleneck analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/analytics/workload")
@limiter.limit("30/minute")
async def get_workload_distribution(request: Request, user_id: str = Depends(get_current_user_id)):
    """Get workload distribution across team members. REQUIRES AUTH. Cached."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        connection_id = connection['id']
        
        # Check cache
        cache_key = get_cache_key("workload", connection_id)
        cached = await get_cached_data(cache_key)
        if cached:
            return cached
        
        workload = await analytics.get_workload_distribution(connection_id)
        await set_cached_data(cache_key, workload, ttl=300)
        return workload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workload distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/analytics/cycle-time")
async def get_cycle_time_analysis(days: int = Query(90, ge=30, le=365), user_id: str = Depends(get_current_user_id)):
    """Get cycle time analysis: created → resolved. REQUIRES AUTH."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        
        cycle_time = await analytics.get_cycle_time_analysis(connection['id'], days=days)
        return cycle_time
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cycle time analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/analytics/velocity")
async def get_velocity_trends(weeks: int = Query(12, ge=4, le=52), user_id: str = Depends(get_current_user_id)):
    """Get velocity trends: issues completed per week. REQUIRES AUTH."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        
        velocity = await analytics.get_velocity_trends(connection['id'], weeks=weeks)
        return velocity
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting velocity trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# Investigation Analytics Endpoints
@api_router.get("/investigation/team-comparison")
async def get_team_comparison(days: int = Query(90, ge=30, le=365), user_id: str = Depends(get_current_user_id)):
    """Compare Sundew vs US team performance. REQUIRES AUTH."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        
        comparison = await investigation.get_team_performance_comparison(connection['id'], days=days)
        return comparison
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/investigation/communication-breakdown")
async def get_communication_breakdown(days: int = Query(30, ge=7, le=90), user_id: str = Depends(get_current_user_id)):
    """Detect communication gaps. REQUIRES AUTH."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        
        breakdown = await investigation.get_communication_breakdown_analysis(connection['id'], days=days)
        return breakdown
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting communication breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/investigation/accountability")
async def get_accountability_tracking(days: int = Query(30, ge=7, le=90), user_id: str = Depends(get_current_user_id)):
    """Track stale issues, unassigned work. REQUIRES AUTH."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        
        accountability = await investigation.get_accountability_tracking(connection['id'], days=days)
        return accountability
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting accountability tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/investigation/historical-trends")
async def get_historical_trends(months: int = Query(6, ge=3, le=12), user_id: str = Depends(get_current_user_id)):
    """Analyze historical trends. REQUIRES AUTH."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        
        trends = await investigation.get_historical_trends(connection['id'], months=months)
        return trends
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Financial Analytics Endpoints
@api_router.get("/financial/cost-of-delay")
async def get_cost_of_delay(days: int = Query(90, ge=30, le=365), user_id: str = Depends(get_current_user_id)):
    """Calculate Cost of Delay for all bottlenecks. REQUIRES AUTH."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        
        cod = await financial.get_cost_of_delay_analysis(connection['id'], days=days)
        return cod
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating cost of delay: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/financial/team-roi")
async def get_team_roi(days: int = Query(90, ge=30, le=365), user_id: str = Depends(get_current_user_id)):
    """Calculate ROI for each team. REQUIRES AUTH."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        
        roi = await financial.get_team_roi_analysis(connection['id'], days=days)
        return roi
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating team ROI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/financial/opportunity-cost")
async def get_opportunity_cost(days: int = Query(90, ge=30, le=365), user_id: str = Depends(get_current_user_id)):
    """Calculate Opportunity Cost: revenue lost from delays. REQUIRES AUTH."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        
        opportunity = await financial.get_opportunity_cost_analysis(connection['id'], days=days)
        return opportunity
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating opportunity cost: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/financial/bottleneck-impact")
async def get_bottleneck_impact(days: int = Query(30, ge=7, le=90), user_id: str = Depends(get_current_user_id)):
    """Rank bottlenecks by total financial impact. REQUIRES AUTH."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        
        impact = await financial.get_bottleneck_impact_score(connection['id'], days=days)
        return impact
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating bottleneck impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/financial/summary")
async def get_financial_summary(user_id: str = Depends(get_current_user_id)):
    """Get complete financial overview. REQUIRES AUTH."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        
        summary = await financial.get_financial_summary(connection['id'])
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting financial summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Action Endpoints
@api_router.get("/actions/auto-assign/preview")
async def preview_auto_assign(max_issues: int = Query(100, ge=1, le=500), user_id: str = Depends(get_current_user_id)):
    """Preview auto-assignment. REQUIRES AUTH."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        
        preview = await actions.preview_auto_assign(connection['id'], max_issues=max_issues)
        return preview
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing auto-assign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/actions/auto-assign/execute")
async def execute_auto_assign(max_issues: int = Query(100, ge=1, le=500), dry_run: bool = Query(False), user_id: str = Depends(get_current_user_id)):
    """Execute auto-assignment. REQUIRES AUTH."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        
        result = await actions.execute_auto_assign(connection['id'], max_issues=max_issues, dry_run=dry_run)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing auto-assign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/actions/bulk-archive/preview")
async def preview_bulk_archive(days_stale: int = Query(90, ge=30, le=365), user_id: str = Depends(get_current_user_id)):
    """Preview bulk archive. REQUIRES AUTH."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        
        preview = await actions.preview_bulk_archive(connection['id'], days_stale=days_stale)
        return preview
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing bulk archive: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/actions/bulk-archive/execute")
async def execute_bulk_archive(days_stale: int = Query(90, ge=30, le=365), dry_run: bool = Query(False), user_id: str = Depends(get_current_user_id)):
    """Execute bulk archive. REQUIRES AUTH."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        
        result = await actions.execute_bulk_archive(connection['id'], days_stale=days_stale, dry_run=dry_run)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing bulk archive: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/actions/rebalance/preview")
async def preview_rebalance_workload(user_id: str = Depends(get_current_user_id)):
    """Preview rebalance. REQUIRES AUTH."""
    try:
        # Multi-tenant: Get user's connection (REQUIRED)
        connection = await get_user_connection(user_id)
        
        preview = await actions.preview_rebalance_workload(connection['id'])
        return preview
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing rebalance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GDPR/CCPA Compliance Endpoints
@api_router.get("/gdpr/export")
async def export_user_data(user_id: str = Depends(get_current_user_id)):
    """
    GDPR Article 15: Right to Access
    Export all user data in machine-readable format (JSON).
    REQUIRES AUTHENTICATION.
    """
    try:
        # Get all connections for this user
        connections = await db.jira_connections.find(
            {"user_id": user_id},
            {"_id": 0, "enc_access_token": 0, "enc_refresh_token": 0}
        ).to_list(None)
        
        # Get all synced data for these connections
        connection_ids = [c['id'] for c in connections]
        
        issues = await db.jira_issues.find(
            {"connection_id": {"$in": connection_ids}},
            {"_id": 0}
        ).to_list(None)
        
        users = await db.jira_users.find(
            {"connection_id": {"$in": connection_ids}},
            {"_id": 0}
        ).to_list(None)
        
        projects = await db.jira_projects.find(
            {"connection_id": {"$in": connection_ids}},
            {"_id": 0}
        ).to_list(None)
        
        return {
            "export_date": datetime.now(timezone.utc).isoformat(),
            "connections": connections,
            "jira_issues": issues,
            "jira_users": users,
            "jira_projects": projects,
            "note": "OAuth tokens excluded for security. This export contains all your business data."
        }
    except Exception as e:
        logger.error(f"Error exporting user data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/gdpr/delete")
async def delete_user_data(user_id: str = Depends(get_current_user_id)):
    """
    GDPR Article 17: Right to Erasure ('Right to be Forgotten')
    Delete all user data from system.
    REQUIRES AUTHENTICATION.
    """
    try:
        # Get all connections for this user
        connections = await db.jira_connections.find({"user_id": user_id}, {"_id": 0}).to_list(None)
        connection_ids = [c['id'] for c in connections]
        
        if not connection_ids:
            return {"message": "No data found to delete", "deleted": 0}
        
        # Delete all data for these connections
        issues_deleted = await db.jira_issues.delete_many({"connection_id": {"$in": connection_ids}})
        users_deleted = await db.jira_users.delete_many({"connection_id": {"$in": connection_ids}})
        projects_deleted = await db.jira_projects.delete_many({"connection_id": {"$in": connection_ids}})
        statuses_deleted = await db.jira_statuses.delete_many({"connection_id": {"$in": connection_ids}})
        jobs_deleted = await db.jira_sync_jobs.delete_many({"connection_id": {"$in": connection_ids}})
        connections_deleted = await db.jira_connections.delete_many({"id": {"$in": connection_ids}})
        
        # Delete user account
        await db.users.delete_one({"id": user_id})
        
        logger.info(f"GDPR deletion executed for user {user_id}: {len(connection_ids)} connections")
        
        return {
            "message": "All your data has been permanently deleted",
            "deleted": {
                "connections": connections_deleted.deleted_count,
                "issues": issues_deleted.deleted_count,
                "users": users_deleted.deleted_count,
                "projects": projects_deleted.deleted_count,
                "statuses": statuses_deleted.deleted_count,
                "sync_jobs": jobs_deleted.deleted_count
            },
            "deletion_date": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error deleting user data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/security/contact")
async def security_contact():
    """Security contact information and vulnerability disclosure."""
    return {
        "security_email": "security@quantumsprout.com",
        "privacy_email": "privacy@quantumsprout.com",
        "gdpr_email": "gdpr@quantumsprout.com",
        "legal_email": "legal@quantumsprout.com",
        "responsible_disclosure": {
            "policy": "We welcome security researchers to report vulnerabilities responsibly",
            "response_time": "Within 24 hours",
            "reward_program": "Bug bounty program planned for Q2 2025"
        },
        "encryption": {
            "in_transit": "HTTPS/TLS 1.2+",
            "tokens": "Fernet AES-128 CBC + HMAC",
            "at_rest": "MongoDB encryption available"
        }
    }


# Rule-Based Bottleneck Finder Endpoint
@api_router.get("/bottleneck-finder/analyze")
async def find_bottlenecks(days: int = Query(90, ge=30, le=365), user_id: str = Depends(get_current_user_id)):
    """
    Run Theory of Constraints based bottleneck analysis.
    Returns top 3 bottlenecks ranked by financial impact.
    """
    try:
        connection = await get_user_connection(user_id)
        result = await bottleneck_finder.find_bottlenecks(connection['id'], days=days)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bottleneck finder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Intelligent Insights Endpoint
@api_router.get("/insights/generate")
async def generate_insights(days: int = Query(90, ge=30, le=365), user_id: str = Depends(get_current_user_id)):
    """
    Generate intelligent insights from data.
    Analyzes trends, detects patterns, provides recommendations.
    """
    try:
        connection = await get_user_connection(user_id)
        insights = await insights_engine.generate_insights(connection['id'], current_period_days=days)
        return {
            "period_days": days,
            "insights_count": len(insights),
            "insights": insights
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# People Bottleneck Analyzer Endpoint
@api_router.get("/people-bottlenecks/analyze")
async def analyze_people_bottlenecks(days: int = Query(90, ge=30, le=365), user_id: str = Depends(get_current_user_id)):
    """
    Identify which individuals are bottlenecks.
    Shows workload burden, blocked value, delegation recommendations.
    """
    try:
        connection = await get_user_connection(user_id)
        result = await people_analyzer.analyze_people_bottlenecks(connection['id'], days=days)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing people bottlenecks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Executive Report Generator Endpoint
@api_router.get("/executive-report/generate")
async def generate_executive_report(days: int = Query(90, ge=30, le=365), user_id: str = Depends(get_current_user_id)):
    """
    Generate CEO-ready executive report as PowerPoint presentation.
    Simple explanations, graphs, actionable recommendations.
    """
    try:
        from ppt_generator import PowerPointDeckGenerator
        from fastapi.responses import StreamingResponse
        
        connection = await get_user_connection(user_id)
        report = await executive_report.generate_executive_report(connection['id'], period_days=days)
        
        # Generate PowerPoint
        ppt_gen = PowerPointDeckGenerator()
        ppt_buffer = ppt_gen.generate_deck(report)
        
        # Return as downloadable file
        return StreamingResponse(
            ppt_buffer,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f"attachment; filename=quantum-sprout-executive-report-{datetime.now().strftime('%Y%m%d')}.pptx"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating executive report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
