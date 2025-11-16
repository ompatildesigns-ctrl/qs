"""
Data retention policy automation for GDPR/CCPA compliance.
Automatically deletes data from disconnected users after retention period.
"""
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Retention period: 12 hours (fresh sync on every login)
RETENTION_HOURS = 12


async def cleanup_old_connections():
    """
    Delete data from connections that have been inactive for > RETENTION_HOURS.
    
    Retention Policy:
    - Active users: Data deleted 12 hours after last sync
    - On re-login: Fresh sync pulls latest data
    - No long-term storage (privacy-first)
    - Anonymous aggregated data: Not stored
    """
    logger.info("Starting 12-hour data retention cleanup...")
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=RETENTION_HOURS)
    
    try:
        # Find connections that haven't synced in RETENTION_DAYS
        old_connections = await db.jira_connections.find({
            "last_full_sync_at": {"$lt": cutoff_time.isoformat()}
        }).to_list(None)
        
        if not old_connections:
            logger.info("No old connections found for cleanup")
            return
        
        logger.info(f"Found {len(old_connections)} connections eligible for deletion")
        
        for connection in old_connections:
            connection_id = connection['id']
            last_sync = connection.get('last_full_sync_at', 'Unknown')
            
            logger.info(f"Deleting data for connection {connection_id} (last sync: {last_sync})")
            
            # Delete all associated data
            issues_result = await db.jira_issues.delete_many({"connection_id": connection_id})
            users_result = await db.jira_users.delete_many({"connection_id": connection_id})
            projects_result = await db.jira_projects.delete_many({"connection_id": connection_id})
            statuses_result = await db.jira_statuses.delete_many({"connection_id": connection_id})
            jobs_result = await db.jira_sync_jobs.delete_many({"connection_id": connection_id})
            connection_result = await db.jira_connections.delete_one({"id": connection_id})
            
            logger.info(f"Deleted: {issues_result.deleted_count} issues, "
                       f"{users_result.deleted_count} users, "
                       f"{projects_result.deleted_count} projects, "
                       f"{statuses_result.deleted_count} statuses, "
                       f"{jobs_result.deleted_count} jobs, "
                       f"{connection_result.deleted_count} connections")
        
        logger.info(f"Data retention cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during data retention cleanup: {e}")
        raise


async def main():
    """Run cleanup job."""
    try:
        await cleanup_old_connections()
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
