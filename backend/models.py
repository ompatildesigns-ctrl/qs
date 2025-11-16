"""Pydantic models for Jira integration."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid


# Jira Connection Models
class JiraConnection(BaseModel):
    """Represents a Jira OAuth connection."""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # User who owns this connection (for multi-tenant)
    site_url: str
    cloud_id: str
    scopes: List[str]
    enc_access_token: str
    enc_refresh_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_full_sync_at: Optional[datetime] = None
    last_delta_sync_at: Optional[datetime] = None


class JiraConnectionCreate(BaseModel):
    """Input for creating a new Jira connection."""
    site_url: str
    cloud_id: str
    scopes: List[str]
    enc_access_token: str
    enc_refresh_token: str
    expires_at: datetime


# Jira Sync Job Models
class JiraSyncJob(BaseModel):
    """Represents a Jira sync job."""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    connection_id: str
    sync_type: str  # 'full' or 'delta'
    status: str  # 'queued', 'running', 'success', 'error'
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JiraSyncJobCreate(BaseModel):
    """Input for creating a sync job."""
    connection_id: str
    sync_type: str


# Jira Resource Models
class JiraProject(BaseModel):
    """Represents a Jira project."""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    connection_id: str
    cloud_id: str
    project_id: str
    key: str
    name: str
    project_type: Optional[str] = None
    data: Dict[str, Any]  # Raw JSON from Jira
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JiraIssue(BaseModel):
    """Represents a Jira issue."""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    connection_id: str
    cloud_id: str
    issue_id: str
    key: str
    project_id: str
    summary: Optional[str] = None
    status: Optional[str] = None
    issue_type: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    resolved: Optional[datetime] = None
    data: Dict[str, Any]  # Raw JSON from Jira
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JiraStatus(BaseModel):
    """Represents a Jira status."""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    connection_id: str
    cloud_id: str
    status_id: str
    name: str
    status_category: Optional[str] = None
    data: Dict[str, Any]  # Raw JSON from Jira
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JiraUser(BaseModel):
    """Represents a Jira user."""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    connection_id: str
    cloud_id: str
    account_id: str
    display_name: str
    active: bool = True
    data: Dict[str, Any]  # Raw JSON from Jira
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# API Response Models
class OAuthAuthorizeResponse(BaseModel):
    """Response for the authorize endpoint."""
    authorize_url: str


class OAuthCallbackResponse(BaseModel):
    """Response for the callback endpoint."""
    message: str
    connection_id: str
    cloud_id: str
    site_url: str


class AccessibleResource(BaseModel):
    """Represents an accessible Jira resource."""
    id: str
    name: str
    url: str
    scopes: List[str]
    avatar_url: Optional[str] = None


class SyncStats(BaseModel):
    """Statistics for synced data."""
    projects: int
    issues: int
    statuses: int
    users: int
    connection_id: Optional[str] = None
