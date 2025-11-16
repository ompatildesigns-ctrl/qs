"""
One-click actions for automated bottleneck resolution.
Integrates with Jira API to execute bulk operations with ROI tracking.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from collections import defaultdict, Counter

from team_classifier import classify_team, get_team_label
from jira_client import JiraAPIClient

logger = logging.getLogger(__name__)


class ActionEngine:
    """
    Execute one-click actions to resolve bottlenecks.
    
    Actions:
    1. Auto-assign unassigned issues (round-robin to available developers)
    2. Bulk archive stale issues (>90 days without update)
    3. Rebalance team workload (redistribute overloaded assignees)
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, jira_client: JiraAPIClient):
        self.db = db
        self.jira_client = jira_client
    
    async def preview_auto_assign(
        self,
        connection_id: str,
        max_issues: int = 100
    ) -> Dict[str, Any]:
        """
        Preview auto-assignment of unassigned issues.
        
        Returns:
        - Number of issues to be assigned
        - Suggested assignees with workload
        - Estimated ROI
        """
        # Get unassigned active issues
        unassigned_issues = await self.db.jira_issues.find(
            {
                "connection_id": connection_id,
                "assignee": None,
                "status": {"$nin": ["Done", "Resolved", "Closed", "Cancelled"]}
            },
            {
                "_id": 0,
                "key": 1,
                "summary": 1,
                "priority": 1,
                "status": 1
            }
        ).limit(max_issues).to_list(max_issues)
        
        # Get active users to distribute work
        users = await self.db.jira_users.find(
            {
                "connection_id": connection_id,
                "active": True
            },
            {
                "_id": 0,
                "account_id": 1,
                "display_name": 1
            }
        ).to_list(None)
        
        if not users:
            return {
                "success": False,
                "error": "No active users found to assign issues"
            }
        
        # Calculate current workload per user
        current_workload = defaultdict(int)
        all_assigned_issues = await self.db.jira_issues.find(
            {
                "connection_id": connection_id,
                "assignee": {"$ne": None},
                "status": {"$nin": ["Done", "Resolved", "Closed", "Cancelled"]}
            },
            {
                "_id": 0,
                "assignee": 1
            }
        ).to_list(None)
        
        for issue in all_assigned_issues:
            assignee = issue.get("assignee")
            if assignee:
                current_workload[assignee] += 1
        
        # Sort users by current workload (ascending) for round-robin
        user_names = [u['display_name'] for u in users]
        sorted_users = sorted(user_names, key=lambda u: current_workload.get(u, 0))
        
        # Simulate assignment distribution
        assignment_plan = []
        user_index = 0
        
        for issue in unassigned_issues:
            assignee = sorted_users[user_index % len(sorted_users)]
            assignment_plan.append({
                "issue_key": issue.get("key"),
                "issue_summary": issue.get("summary", "")[:60],
                "suggested_assignee": assignee,
                "current_workload": current_workload.get(assignee, 0)
            })
            current_workload[assignee] += 1
            user_index += 1
        
        # Calculate ROI (assume avg 30 days unassigned, blended rate $460/day)
        avg_days_unassigned = 30
        blended_daily_cost = 460
        total_cost_of_delay = len(unassigned_issues) * avg_days_unassigned * blended_daily_cost
        
        # New workload distribution
        workload_distribution = {user: current_workload[user] for user in sorted_users}
        
        return {
            "success": True,
            "action": "auto_assign",
            "issues_to_assign": len(unassigned_issues),
            "assignment_plan": assignment_plan[:20],  # Show top 20
            "workload_distribution": workload_distribution,
            "estimated_roi": {
                "recovery_potential": round(total_cost_of_delay, 0),
                "time_to_implement": "1 day",
                "risk_level": "Low"
            }
        }
    
    async def execute_auto_assign(
        self,
        connection_id: str,
        max_issues: int = 100,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Execute auto-assignment of unassigned issues.
        
        If dry_run=True, only simulates the action without making API calls.
        """
        preview = await self.preview_auto_assign(connection_id, max_issues)
        
        if not preview["success"]:
            return preview
        
        if dry_run:
            return {
                **preview,
                "executed": False,
                "message": "Dry run completed. No changes made to Jira."
            }
        
        # Execute assignments via Jira API
        assignment_plan = preview["assignment_plan"]
        successful_assignments = []
        failed_assignments = []
        
        for assignment in assignment_plan:
            try:
                # Get user account ID from display name
                user_doc = await self.db.jira_users.find_one({
                    "connection_id": connection_id,
                    "display_name": assignment["suggested_assignee"]
                })
                
                if not user_doc:
                    failed_assignments.append({
                        "issue_key": assignment["issue_key"],
                        "error": "User not found in database"
                    })
                    continue
                
                account_id = user_doc.get("account_id")
                
                # Get issue ID from key
                issue_doc = await self.db.jira_issues.find_one({
                    "connection_id": connection_id,
                    "key": assignment["issue_key"]
                })
                
                if not issue_doc:
                    failed_assignments.append({
                        "issue_key": assignment["issue_key"],
                        "error": "Issue not found in database"
                    })
                    continue
                
                issue_id = issue_doc.get("issue_id")
                
                # Update issue via Jira API
                update_payload = {
                    "fields": {
                        "assignee": {
                            "accountId": account_id
                        }
                    }
                }
                
                await self.jira_client.make_api_request(
                    connection_id,
                    f"/rest/api/3/issue/{issue_id}",
                    method="PUT",
                    json_data=update_payload
                )
                
                # Update local database
                await self.db.jira_issues.update_one(
                    {"connection_id": connection_id, "issue_id": issue_id},
                    {"$set": {
                        "assignee": assignment["suggested_assignee"],
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                successful_assignments.append(assignment["issue_key"])
                
            except Exception as e:
                logger.error(f"Failed to assign {assignment['issue_key']}: {e}")
                failed_assignments.append({
                    "issue_key": assignment["issue_key"],
                    "error": str(e)
                })
        
        return {
            "success": True,
            "executed": True,
            "action": "auto_assign",
            "successful_assignments": len(successful_assignments),
            "failed_assignments": len(failed_assignments),
            "successful_issues": successful_assignments,
            "failed_issues": failed_assignments,
            "estimated_roi": preview["estimated_roi"]
        }
    
    async def preview_bulk_archive(
        self,
        connection_id: str,
        days_stale: int = 90
    ) -> Dict[str, Any]:
        """
        Preview bulk archiving of stale issues.
        
        Identifies issues with no updates for X days.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_stale)
        
        stale_issues = await self.db.jira_issues.find(
            {
                "connection_id": connection_id,
                "updated": {"$lt": cutoff_date.isoformat()},
                "status": {"$nin": ["Done", "Resolved", "Closed", "Cancelled", "Archived"]}
            },
            {
                "_id": 0,
                "key": 1,
                "summary": 1,
                "updated": 1,
                "assignee": 1,
                "status": 1
            }
        ).to_list(None)
        
        # Calculate Cost of Delay
        total_cost = 0
        blended_daily_cost = 460
        
        issues_preview = []
        for issue in stale_issues:
            updated = issue.get("updated")
            if updated:
                if isinstance(updated, str):
                    updated = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                days_stale_calc = (datetime.now(timezone.utc) - updated).total_seconds() / 86400
                cost = blended_daily_cost * days_stale_calc
                total_cost += cost
                
                issues_preview.append({
                    "key": issue.get("key"),
                    "summary": issue.get("summary", "")[:60],
                    "assignee": issue.get("assignee", "Unassigned"),
                    "days_stale": round(days_stale_calc, 1),
                    "cost_of_delay": round(cost, 0)
                })
        
        issues_preview.sort(key=lambda x: x["days_stale"], reverse=True)
        
        return {
            "success": True,
            "action": "bulk_archive",
            "issues_to_archive": len(stale_issues),
            "issues_preview": issues_preview[:20],
            "estimated_roi": {
                "recovery_potential": round(total_cost, 0),
                "time_to_implement": "2 hours",
                "risk_level": "Medium"
            }
        }
    
    async def execute_bulk_archive(
        self,
        connection_id: str,
        days_stale: int = 90,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Execute bulk archiving by transitioning issues to "Closed" status.
        """
        preview = await self.preview_bulk_archive(connection_id, days_stale)
        
        if not preview["success"]:
            return preview
        
        if dry_run:
            return {
                **preview,
                "executed": False,
                "message": "Dry run completed. No changes made to Jira."
            }
        
        # Get issues to archive
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_stale)
        stale_issues = await self.db.jira_issues.find(
            {
                "connection_id": connection_id,
                "updated": {"$lt": cutoff_date.isoformat()},
                "status": {"$nin": ["Done", "Resolved", "Closed", "Cancelled", "Archived"]}
            },
            {
                "_id": 0,
                "issue_id": 1,
                "key": 1,
                "summary": 1
            }
        ).to_list(None)
        
        successful_archives = []
        failed_archives = []
        
        for issue in stale_issues:
            try:
                issue_id = issue.get("issue_id")
                issue_key = issue.get("key")
                
                # Transition to Closed status
                # Note: In production, you'd need to find the correct transition ID
                # For now, we'll update the status directly (may not work for all Jira configs)
                transitions_response = await self.jira_client.make_api_request(
                    connection_id,
                    f"/rest/api/3/issue/{issue_id}/transitions"
                )
                
                # Find "Close" or "Done" transition
                close_transition = None
                for transition in transitions_response.get("transitions", []):
                    if transition["name"].lower() in ["close", "closed", "done"]:
                        close_transition = transition
                        break
                
                if close_transition:
                    # Execute transition
                    await self.jira_client.make_api_request(
                        connection_id,
                        f"/rest/api/3/issue/{issue_id}/transitions",
                        method="POST",
                        json_data={
                            "transition": {
                                "id": close_transition["id"]
                            }
                        }
                    )
                    
                    # Update local database
                    await self.db.jira_issues.update_one(
                        {"connection_id": connection_id, "issue_id": issue_id},
                        {"$set": {
                            "status": "Closed",
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    
                    successful_archives.append(issue_key)
                else:
                    failed_archives.append({
                        "issue_key": issue_key,
                        "error": "No 'Close' transition available"
                    })
                
            except Exception as e:
                logger.error(f"Failed to archive {issue_key}: {e}")
                failed_archives.append({
                    "issue_key": issue_key,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "executed": True,
            "action": "bulk_archive",
            "successful_archives": len(successful_archives),
            "failed_archives": len(failed_archives),
            "successful_issues": successful_archives,
            "failed_issues": failed_archives,
            "estimated_roi": preview["estimated_roi"]
        }
    
    async def preview_rebalance_workload(
        self,
        connection_id: str
    ) -> Dict[str, Any]:
        """
        Preview team workload rebalancing.
        
        Identifies overloaded assignees and suggests redistribution.
        """
        # Get all active issues with assignees
        active_issues = await self.db.jira_issues.find(
            {
                "connection_id": connection_id,
                "assignee": {"$ne": None},
                "status": {"$nin": ["Done", "Resolved", "Closed", "Cancelled"]}
            },
            {
                "_id": 0,
                "key": 1,
                "assignee": 1,
                "summary": 1,
                "priority": 1
            }
        ).to_list(None)
        
        # Count workload per assignee
        workload = Counter(issue.get("assignee") for issue in active_issues)
        
        if not workload:
            return {
                "success": False,
                "error": "No assigned issues found"
            }
        
        # Calculate statistics
        avg_workload = sum(workload.values()) / len(workload)
        overloaded_threshold = avg_workload * 1.5
        
        overloaded_assignees = []
        underloaded_assignees = []
        
        for assignee, count in workload.items():
            if count > overloaded_threshold:
                overloaded_assignees.append({
                    "assignee": assignee,
                    "current_workload": count,
                    "excess": round(count - avg_workload, 0),
                    "team": get_team_label(classify_team(assignee))
                })
            elif count < avg_workload * 0.5:
                underloaded_assignees.append({
                    "assignee": assignee,
                    "current_workload": count,
                    "capacity": round(avg_workload - count, 0),
                    "team": get_team_label(classify_team(assignee))
                })
        
        overloaded_assignees.sort(key=lambda x: x["current_workload"], reverse=True)
        underloaded_assignees.sort(key=lambda x: x["current_workload"])
        
        # Calculate ROI (assume reducing overload improves velocity by 20%)
        potential_recovery = len(overloaded_assignees) * avg_workload * 7 * 460  # 1 week of work
        
        return {
            "success": True,
            "action": "rebalance_workload",
            "average_workload": round(avg_workload, 1),
            "overloaded_assignees": overloaded_assignees,
            "underloaded_assignees": underloaded_assignees,
            "rebalance_suggestions": f"Redistribute {sum(a['excess'] for a in overloaded_assignees)} issues from overloaded to underloaded team members",
            "estimated_roi": {
                "recovery_potential": round(potential_recovery, 0),
                "time_to_implement": "1 day",
                "risk_level": "Low"
            }
        }
