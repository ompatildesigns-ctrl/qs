"""
Background job scheduler for automated daily syncs.
Runs as a separate process managed by supervisor.
"""
import asyncio
import os
import logging
from datetime import datetime, time, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from jira_client import JiraAPIClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
jira_client = JiraAPIClient(db)


async def run_full_sync(connection_id: str, cloud_id: str):
    """
    Run a full sync for a connection.
    """
    try:
        logger.info(f"Starting scheduled sync for connection {connection_id}")
        
        # Fetch projects
        projects_data = await jira_client.get_projects(connection_id, cloud_id)
        logger.info(f"Fetched {len(projects_data)} projects")
        
        # Store projects
        for project in projects_data:
            await db.jira_projects.update_one(
                {"connection_id": connection_id, "project_id": project['id']},
                {"$set": {
                    "connection_id": connection_id,
                    "project_id": project['id'],
                    "key": project.get('key'),
                    "name": project.get('name'),
                    "data": project,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
        
        # Fetch issues (last 90 days with pagination)
        all_issues = []
        start_at = 0
        max_results = 100
        
        while True:
            issues_response = await jira_client.get_issues(
                connection_id, 
                cloud_id,
                jql="updated >= -90d ORDER BY updated DESC",
                start_at=start_at,
                max_results=max_results
            )
            
            issues = issues_response.get('issues', [])
            all_issues.extend(issues)
            
            total = issues_response.get('total', 0)
            logger.info(f"Fetched {len(all_issues)}/{total} issues")
            
            if len(all_issues) >= total:
                break
            
            start_at += max_results
            await asyncio.sleep(0.2)  # Rate limiting
        
        # Store issues
        for issue in all_issues:
            fields = issue.get('fields', {})
            assignee = fields.get('assignee') or {}
            reporter = fields.get('reporter') or {}
            status = fields.get('status') or {}
            
            created = fields.get('created')
            updated = fields.get('updated')
            resolved = fields.get('resolutiondate')
            
            await db.jira_issues.update_one(
                {"connection_id": connection_id, "issue_id": issue['id']},
                {"$set": {
                    "connection_id": connection_id,
                    "issue_id": issue['id'],
                    "key": issue.get('key'),
                    "summary": fields.get('summary'),
                    "description": fields.get('description'),
                    "status": status.get('name'),
                    "issue_type": fields.get('issuetype', {}).get('name'),
                    "priority": fields.get('priority', {}).get('name'),
                    "assignee": assignee.get('displayName'),
                    "reporter": reporter.get('displayName'),
                    "created": created,
                    "updated": updated,
                    "resolved": resolved,
                    "project_id": fields.get('project', {}).get('id'),
                    "data": issue,
                    "synced_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
        
        # Fetch statuses
        statuses_data = await jira_client.get_statuses(connection_id, cloud_id)
        logger.info(f"Fetched {len(statuses_data)} statuses")
        
        for status in statuses_data:
            await db.jira_statuses.update_one(
                {"connection_id": connection_id, "status_id": status['id']},
                {"$set": {
                    "connection_id": connection_id,
                    "status_id": status['id'],
                    "name": status.get('name'),
                    "category": status.get('statusCategory', {}).get('name'),
                    "data": status,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
        
        # Fetch users
        users_data = await jira_client.get_users(connection_id, cloud_id)
        logger.info(f"Fetched {len(users_data)} users")
        
        for user in users_data:
            await db.jira_users.update_one(
                {"connection_id": connection_id, "account_id": user['accountId']},
                {"$set": {
                    "connection_id": connection_id,
                    "account_id": user['accountId'],
                    "display_name": user.get('displayName'),
                    "active": user.get('active', True),
                    "data": user,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
        
        # Update connection with last sync time
        await db.jira_connections.update_one(
            {"id": connection_id},
            {"$set": {"last_full_sync_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        logger.info(f"Sync complete for connection {connection_id}: {len(all_issues)} issues, {len(projects_data)} projects, {len(users_data)} users")
        
    except Exception as e:
        logger.error(f"Error during scheduled sync for {connection_id}: {e}")


async def sync_all_connections():
    """
    Sync all active connections.
    """
    try:
        # Get all connections
        connections = await db.jira_connections.find({}, {"_id": 0}).to_list(None)
        
        if not connections:
            logger.info("No connections to sync")
            return
        
        logger.info(f"Found {len(connections)} connections to sync")
        
        for conn in connections:
            try:
                await run_full_sync(conn['id'], conn['cloud_id'])
            except Exception as e:
                logger.error(f"Failed to sync connection {conn['id']}: {e}")
                continue
        
        logger.info("All connections synced successfully")
        
    except Exception as e:
        logger.error(f"Error syncing connections: {e}")


async def wait_until(target_time: time):
    """
    Wait until the specified time today (or tomorrow if already passed).
    """
    now = datetime.now(timezone.utc)
    target = now.replace(hour=target_time.hour, minute=target_time.minute, second=0, microsecond=0)
    
    # If target time has passed today, schedule for tomorrow
    if target <= now:
        target = target.replace(day=target.day + 1)
    
    wait_seconds = (target - now).total_seconds()
    logger.info(f"Next sync scheduled at {target.isoformat()} (in {wait_seconds / 3600:.1f} hours)")
    
    await asyncio.sleep(wait_seconds)


async def scheduler_loop():
    """
    Main scheduler loop - runs daily at 2:00 AM UTC.
    """
    logger.info("Scheduler started")
    
    # Configure sync time (2:00 AM UTC)
    sync_time = time(hour=2, minute=0)
    
    while True:
        try:
            # Wait until next sync time
            await wait_until(sync_time)
            
            # Run sync
            logger.info("Starting scheduled sync...")
            await sync_all_connections()
            
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
            # Wait 1 hour before retrying on error
            await asyncio.sleep(3600)


if __name__ == "__main__":
    logger.info("Starting Jira Sync Scheduler...")
    try:
        asyncio.run(scheduler_loop())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler crashed: {e}")
        raise
