"""
Investigation analytics for diagnosing productivity decline.
Focuses on root cause analysis rather than static reporting.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from collections import defaultdict

from team_classifier import classify_team, get_team_label

logger = logging.getLogger(__name__)


class InvestigationAnalytics:
    """Analytics engine for CEO productivity investigation."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def get_team_performance_comparison(
        self,
        connection_id: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Compare Internal (US) vs External (Sundew) team performance.
        
        Metrics:
        - Issue completion rates
        - Average cycle times
        - Workload distribution
        - Quality indicators (reopened issues)
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get all issues from period
        issues = await self.db.jira_issues.find(
            {
                "connection_id": connection_id,
                "created": {"$gte": cutoff_date.isoformat()}
            },
            {
                "_id": 0,
                "assignee": 1,
                "reporter": 1,
                "created": 1,
                "resolved": 1,
                "status": 1
            }
        ).to_list(None)
        
        # Classify and aggregate by team
        team_stats = {
            "sundew": {"assigned": 0, "completed": 0, "cycle_times": [], "reopened": 0, "unassigned_created": 0},
            "us": {"assigned": 0, "completed": 0, "cycle_times": [], "reopened": 0, "unassigned_created": 0},
            "unknown": {"assigned": 0, "completed": 0, "cycle_times": [], "reopened": 0, "unassigned_created": 0}
        }
        
        for issue in issues:
            assignee = issue.get("assignee")
            reporter = issue.get("reporter")
            resolved = issue.get("resolved")
            created = issue.get("created")
            
            # Classify reporter (who created the issue)
            reporter_team = classify_team(reporter) if reporter else "unknown"
            
            # Track unassigned issues by creating team
            if not assignee:
                team_stats[reporter_team]["unassigned_created"] += 1
                continue
            
            # Classify assignee (who's working on it)
            assignee_team = classify_team(assignee)
            team_stats[assignee_team]["assigned"] += 1
            
            # Track completed issues
            if resolved:
                team_stats[assignee_team]["completed"] += 1
                
                # Calculate cycle time
                if created and resolved:
                    if isinstance(created, str):
                        created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    if isinstance(resolved, str):
                        resolved = datetime.fromisoformat(resolved.replace('Z', '+00:00'))
                    
                    cycle_days = (resolved - created).total_seconds() / 86400
                    team_stats[assignee_team]["cycle_times"].append(cycle_days)
        
        # Calculate aggregates
        comparison = {}
        for team, stats in team_stats.items():
            completion_rate = (stats["completed"] / stats["assigned"] * 100) if stats["assigned"] > 0 else 0
            avg_cycle_time = sum(stats["cycle_times"]) / len(stats["cycle_times"]) if stats["cycle_times"] else 0
            
            comparison[team] = {
                "team_label": get_team_label(team),
                "issues_assigned": stats["assigned"],
                "issues_completed": stats["completed"],
                "completion_rate": round(completion_rate, 1),
                "avg_cycle_time_days": round(avg_cycle_time, 1),
                "issues_created_unassigned": stats["unassigned_created"]
            }
        
        # Calculate insights
        insights = []
        sundew_completion = comparison["sundew"]["completion_rate"]
        us_completion = comparison["us"]["completion_rate"]
        
        if sundew_completion > us_completion + 10:
            insights.append(f"⚠️ Sundew team completing {sundew_completion - us_completion:.1f}% more issues than US team")
        elif us_completion > sundew_completion + 10:
            insights.append(f"⚠️ US team completing {us_completion - sundew_completion:.1f}% more issues than Sundew team")
        
        sundew_cycle = comparison["sundew"]["avg_cycle_time_days"]
        us_cycle = comparison["us"]["avg_cycle_time_days"]
        
        if sundew_cycle > us_cycle * 1.5:
            insights.append(f"🔴 Sundew cycle time ({sundew_cycle:.1f}d) is {(sundew_cycle/us_cycle - 1)*100:.0f}% slower than US team")
        elif us_cycle > sundew_cycle * 1.5:
            insights.append(f"🔴 US cycle time ({us_cycle:.1f}d) is {(us_cycle/sundew_cycle - 1)*100:.0f}% slower than Sundew team")
        
        return {
            "period_days": days,
            "comparison": comparison,
            "insights": insights
        }
    
    async def get_communication_breakdown_analysis(
        self,
        connection_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Detect communication gaps and handoff delays.
        
        Analyzes:
        - Issues stuck in "waiting" statuses
        - Cross-team handoffs (US creates, Sundew assigned)
        - Response time patterns
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get recent issues
        issues = await self.db.jira_issues.find(
            {
                "connection_id": connection_id,
                "updated": {"$gte": cutoff_date.isoformat()}
            },
            {
                "_id": 0,
                "key": 1,
                "status": 1,
                "assignee": 1,
                "reporter": 1,
                "created": 1,
                "updated": 1,
                "summary": 1
            }
        ).to_list(None)
        
        # Analyze waiting/blocked issues
        waiting_statuses = ["waiting", "blocked", "on hold", "pending", "paused"]
        waiting_issues = []
        cross_team_issues = []
        
        for issue in issues:
            status = (issue.get("status") or "").lower()
            assignee = issue.get("assignee")
            reporter = issue.get("reporter")
            updated = issue.get("updated")
            
            # Check if stuck in waiting status
            if any(ws in status for ws in waiting_statuses):
                if updated:
                    if isinstance(updated, str):
                        updated = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                    days_waiting = (datetime.now(timezone.utc) - updated).total_seconds() / 86400
                    
                    waiting_issues.append({
                        "key": issue.get("key"),
                        "summary": issue.get("summary", "")[:60],
                        "status": issue.get("status"),
                        "assignee": assignee,
                        "days_waiting": round(days_waiting, 1)
                    })
            
            # Detect cross-team assignments
            if assignee and reporter:
                assignee_team = classify_team(assignee)
                reporter_team = classify_team(reporter)
                
                if assignee_team != reporter_team and assignee_team != "unknown" and reporter_team != "unknown":
                    cross_team_issues.append({
                        "key": issue.get("key"),
                        "summary": issue.get("summary", "")[:60],
                        "created_by": f"{reporter} ({get_team_label(reporter_team)})",
                        "assigned_to": f"{assignee} ({get_team_label(assignee_team)})",
                        "status": issue.get("status")
                    })
        
        # Sort by severity
        waiting_issues.sort(key=lambda x: x["days_waiting"], reverse=True)
        
        return {
            "period_days": days,
            "waiting_issues_count": len(waiting_issues),
            "waiting_issues": waiting_issues[:20],
            "cross_team_handoffs_count": len(cross_team_issues),
            "cross_team_handoffs": cross_team_issues[:20],
            "insights": [
                f"🔴 {len(waiting_issues)} issues stuck in waiting/blocked status" if len(waiting_issues) > 10 else None,
                f"⚠️ {len(cross_team_issues)} cross-team handoffs detected" if len(cross_team_issues) > 20 else None
            ]
        }
    
    async def get_accountability_tracking(
        self,
        connection_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Track accountability issues.
        
        Identifies:
        - Issues reassigned multiple times (hot potato)
        - Stale issues (no updates for X days)
        - Unassigned issue trends
        - Who has most overdue issues
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        now = datetime.now(timezone.utc)
        
        # Get all active issues
        issues = await self.db.jira_issues.find(
            {
                "connection_id": connection_id,
                "status": {"$nin": ["Done", "Resolved", "Closed", "Cancelled"]}
            },
            {
                "_id": 0,
                "key": 1,
                "assignee": 1,
                "updated": 1,
                "created": 1,
                "status": 1,
                "summary": 1
            }
        ).to_list(None)
        
        # Track stale issues
        stale_issues = []
        unassigned_issues = []
        assignee_overdue_count = defaultdict(int)
        
        for issue in issues:
            assignee = issue.get("assignee")
            updated = issue.get("updated")
            created = issue.get("created")
            
            # Track unassigned
            if not assignee:
                if created:
                    if isinstance(created, str):
                        created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    days_unassigned = (now - created).total_seconds() / 86400
                    
                    unassigned_issues.append({
                        "key": issue.get("key"),
                        "summary": issue.get("summary", "")[:60],
                        "status": issue.get("status"),
                        "reporter": issue.get("reporter"),
                        "days_unassigned": round(days_unassigned, 1)
                    })
                continue
            
            # Track stale (no update in 14+ days)
            if updated:
                if isinstance(updated, str):
                    updated = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                days_stale = (now - updated).total_seconds() / 86400
                
                if days_stale > 14:
                    stale_issues.append({
                        "key": issue.get("key"),
                        "summary": issue.get("summary", "")[:60],
                        "status": issue.get("status"),
                        "assignee": assignee,
                        "days_stale": round(days_stale, 1),
                        "team": get_team_label(classify_team(assignee))
                    })
                    
                    assignee_overdue_count[assignee] += 1
        
        # Sort and get top offenders
        stale_issues.sort(key=lambda x: x["days_stale"], reverse=True)
        unassigned_issues.sort(key=lambda x: x["days_unassigned"], reverse=True)
        
        top_overdue_assignees = sorted(
            [{"assignee": k, "overdue_count": v, "team": get_team_label(classify_team(k))} 
             for k, v in assignee_overdue_count.items()],
            key=lambda x: x["overdue_count"],
            reverse=True
        )[:15]
        
        return {
            "stale_issues_count": len(stale_issues),
            "stale_issues": stale_issues[:20],
            "unassigned_issues_count": len(unassigned_issues),
            "unassigned_issues": unassigned_issues[:20],
            "top_overdue_assignees": top_overdue_assignees,
            "insights": [
                f"🔴 {len(stale_issues)} issues haven't been updated in 14+ days" if len(stale_issues) > 50 else None,
                f"⚠️ {len(unassigned_issues)} issues remain unassigned" if len(unassigned_issues) > 20 else None,
                f"🔴 {top_overdue_assignees[0]['assignee']} has {top_overdue_assignees[0]['overdue_count']} stale issues" if top_overdue_assignees and top_overdue_assignees[0]['overdue_count'] > 10 else None
            ]
        }
    
    async def get_historical_trends(
        self,
        connection_id: str,
        months: int = 6
    ) -> Dict[str, Any]:
        """
        Analyze month-over-month trends to identify when decline started.
        
        Tracks:
        - Monthly completion rate
        - Monthly velocity
        - Monthly cycle time
        - Team-specific trends
        """
        # Get all resolved issues
        issues = await self.db.jira_issues.find(
            {
                "connection_id": connection_id,
                "resolved": {"$ne": None}
            },
            {
                "_id": 0,
                "resolved": 1,
                "created": 1,
                "assignee": 1
            }
        ).to_list(None)
        
        # Group by month
        monthly_data = defaultdict(lambda: {
            "total": 0,
            "sundew": 0,
            "us": 0,
            "cycle_times": [],
            "sundew_cycle_times": [],
            "us_cycle_times": []
        })
        
        for issue in issues:
            resolved = issue.get("resolved")
            created = issue.get("created")
            assignee = issue.get("assignee")
            
            if not resolved:
                continue
            
            if isinstance(resolved, str):
                resolved = datetime.fromisoformat(resolved.replace('Z', '+00:00'))
            
            # Get month key (YYYY-MM)
            month_key = resolved.strftime("%Y-%m")
            
            # Classify team
            team = classify_team(assignee) if assignee else "unknown"
            
            monthly_data[month_key]["total"] += 1
            if team == "sundew":
                monthly_data[month_key]["sundew"] += 1
            elif team == "us":
                monthly_data[month_key]["us"] += 1
            
            # Calculate cycle time
            if created:
                if isinstance(created, str):
                    created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                
                cycle_days = (resolved - created).total_seconds() / 86400
                monthly_data[month_key]["cycle_times"].append(cycle_days)
                
                if team == "sundew":
                    monthly_data[month_key]["sundew_cycle_times"].append(cycle_days)
                elif team == "us":
                    monthly_data[month_key]["us_cycle_times"].append(cycle_days)
        
        # Convert to sorted list
        trends = []
        for month_key in sorted(monthly_data.keys())[-months:]:
            data = monthly_data[month_key]
            avg_cycle = sum(data["cycle_times"]) / len(data["cycle_times"]) if data["cycle_times"] else 0
            sundew_cycle = sum(data["sundew_cycle_times"]) / len(data["sundew_cycle_times"]) if data["sundew_cycle_times"] else 0
            us_cycle = sum(data["us_cycle_times"]) / len(data["us_cycle_times"]) if data["us_cycle_times"] else 0
            
            trends.append({
                "month": month_key,
                "total_completed": data["total"],
                "sundew_completed": data["sundew"],
                "us_completed": data["us"],
                "avg_cycle_time_days": round(avg_cycle, 1),
                "sundew_cycle_time_days": round(sundew_cycle, 1),
                "us_cycle_time_days": round(us_cycle, 1)
            })
        
        # Detect decline
        insights = []
        if len(trends) >= 3:
            recent_3 = trends[-3:]
            velocity_trend = [t["total_completed"] for t in recent_3]
            
            if velocity_trend[0] > velocity_trend[-1]:
                decline_pct = ((velocity_trend[0] - velocity_trend[-1]) / velocity_trend[0]) * 100
                insights.append(f"📉 Velocity declined {decline_pct:.0f}% over last 3 months")
            
            cycle_trend = [t["avg_cycle_time_days"] for t in recent_3]
            if cycle_trend[-1] > cycle_trend[0] * 1.3:
                increase_pct = ((cycle_trend[-1] - cycle_trend[0]) / cycle_trend[0]) * 100
                insights.append(f"⚠️ Cycle time increased {increase_pct:.0f}% over last 3 months")
        
        return {
            "months_analyzed": len(trends),
            "monthly_trends": trends,
            "insights": insights
        }
