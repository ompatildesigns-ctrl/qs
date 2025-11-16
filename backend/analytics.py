"""Analytics engine for CEO dashboard metrics."""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class JiraAnalytics:
    """Calculate CEO-level metrics from Jira data."""
    
    def __init__(self, db):
        self.db = db
    
    async def get_bottleneck_analysis(self, connection_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Identify bottlenecks: issues stuck in specific statuses for too long.
        
        Returns:
        - Status-wise average time
        - Issues stuck > threshold
        - Worst offenders
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get all issues updated in last N days
        issues = await self.db.jira_issues.find(
            {
                "connection_id": connection_id,
                "updated": {"$gte": cutoff_date.isoformat()}
            },
            {
                "_id": 0,
                "key": 1,
                "status": 1,
                "created": 1,
                "updated": 1,
                "resolved": 1,
                "summary": 1,
                "assignee": 1,
                "project_id": 1
            }
        ).to_list(length=None)
        
        status_times = defaultdict(list)
        stuck_issues = []
        
        for issue in issues:
            status = issue.get('status', 'Unknown')
            created = datetime.fromisoformat(issue['created']) if issue.get('created') else None
            updated = datetime.fromisoformat(issue['updated']) if issue.get('updated') else None
            resolved = datetime.fromisoformat(issue['resolved']) if issue.get('resolved') else None
            
            if created and updated:
                # Calculate time in current status (days)
                time_in_status = (updated - created).days if not resolved else (resolved - created).days
                status_times[status].append(time_in_status)
                
                # Flag as stuck if > 14 days without resolution
                if not resolved and time_in_status > 14:
                    stuck_issues.append({
                        "key": issue['key'],
                        "summary": issue.get('summary', 'No summary'),
                        "status": status,
                        "days_in_status": time_in_status,
                        "assignee": issue.get('assignee', 'Unassigned'),
                        "project_id": issue.get('project_id')
                    })
        
        # Calculate averages per status
        status_analysis = []
        for status, times in status_times.items():
            avg_time = sum(times) / len(times) if times else 0
            status_analysis.append({
                "status": status,
                "avg_days": round(avg_time, 1),
                "issue_count": len(times),
                "is_bottleneck": avg_time > 10  # Flag if avg > 10 days
            })
        
        # Sort by avg time descending
        status_analysis.sort(key=lambda x: x['avg_days'], reverse=True)
        
        # Sort stuck issues by days descending
        stuck_issues.sort(key=lambda x: x['days_in_status'], reverse=True)
        
        return {
            "status_analysis": status_analysis[:10],  # Top 10 statuses
            "stuck_issues": stuck_issues[:20],  # Top 20 stuck issues
            "total_bottlenecks": len([s for s in status_analysis if s['is_bottleneck']]),
            "total_stuck_issues": len(stuck_issues)
        }
    
    async def get_workload_distribution(self, connection_id: str) -> Dict[str, Any]:
        """
        Analyze workload distribution across team members.
        
        Returns:
        - Active issues per assignee
        - Overloaded vs underutilized
        - Unassigned work
        """
        # Get all unresolved issues
        issues = await self.db.jira_issues.find(
            {
                "connection_id": connection_id,
                "resolved": None
            },
            {
                "_id": 0,
                "key": 1,
                "assignee": 1,
                "summary": 1,
                "status": 1,
                "priority": 1
            }
        ).to_list(length=None)
        
        assignee_workload = defaultdict(lambda: {"active": 0, "issues": []})
        unassigned_count = 0
        
        for issue in issues:
            assignee = issue.get('assignee')
            if not assignee or assignee == 'Unassigned':
                unassigned_count += 1
            else:
                assignee_workload[assignee]["active"] += 1
                assignee_workload[assignee]["issues"].append({
                    "key": issue['key'],
                    "summary": issue.get('summary', 'No summary')[:50],
                    "status": issue.get('status', 'Unknown'),
                    "priority": issue.get('priority', 'None')
                })
        
        # Convert to list and calculate stats
        workload_list = []
        for assignee, data in assignee_workload.items():
            workload_list.append({
                "assignee": assignee,
                "active_issues": data["active"],
                "issues": data["issues"][:5],  # Top 5 for preview
                "load_category": "overloaded" if data["active"] > 15 else "normal" if data["active"] > 5 else "underutilized"
            })
        
        # Sort by active issues descending
        workload_list.sort(key=lambda x: x['active_issues'], reverse=True)
        
        # Calculate totals
        total_assigned = sum(w['active_issues'] for w in workload_list)
        avg_workload = total_assigned / len(workload_list) if workload_list else 0
        
        return {
            "workload_distribution": workload_list,
            "summary": {
                "total_team_members": len(workload_list),
                "total_assigned_issues": total_assigned,
                "unassigned_issues": unassigned_count,
                "avg_workload": round(avg_workload, 1),
                "overloaded_count": len([w for w in workload_list if w['load_category'] == 'overloaded']),
                "underutilized_count": len([w for w in workload_list if w['load_category'] == 'underutilized'])
            }
        }
    
    async def get_cycle_time_analysis(self, connection_id: str, days: int = 90) -> Dict[str, Any]:
        """
        Calculate cycle time: created → resolved.
        
        Returns:
        - Overall avg cycle time
        - By project
        - By issue type
        - By assignee
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get resolved issues in last N days
        issues = await self.db.jira_issues.find(
            {
                "connection_id": connection_id,
                "resolved": {"$gte": cutoff_date.isoformat(), "$ne": None}
            },
            {
                "_id": 0,
                "key": 1,
                "created": 1,
                "resolved": 1,
                "project_id": 1,
                "issue_type": 1,
                "assignee": 1
            }
        ).to_list(length=None)
        
        cycle_times = []
        by_project = defaultdict(list)
        by_type = defaultdict(list)
        by_assignee = defaultdict(list)
        
        for issue in issues:
            created = datetime.fromisoformat(issue['created']) if issue.get('created') else None
            resolved = datetime.fromisoformat(issue['resolved']) if issue.get('resolved') else None
            
            if created and resolved:
                cycle_time_days = (resolved - created).days
                cycle_times.append(cycle_time_days)
                
                project_id = issue.get('project_id', 'Unknown')
                issue_type = issue.get('issue_type', 'Unknown')
                assignee = issue.get('assignee', 'Unassigned')
                
                by_project[project_id].append(cycle_time_days)
                by_type[issue_type].append(cycle_time_days)
                by_assignee[assignee].append(cycle_time_days)
        
        # Calculate overall stats
        avg_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else 0
        median_cycle_time = sorted(cycle_times)[len(cycle_times)//2] if cycle_times else 0
        
        # By project
        project_analysis = []
        for proj_id, times in by_project.items():
            avg = sum(times) / len(times) if times else 0
            project_analysis.append({
                "project_id": proj_id,
                "avg_cycle_time_days": round(avg, 1),
                "issues_resolved": len(times)
            })
        project_analysis.sort(key=lambda x: x['avg_cycle_time_days'], reverse=True)
        
        # By type
        type_analysis = []
        for issue_type, times in by_type.items():
            avg = sum(times) / len(times) if times else 0
            type_analysis.append({
                "issue_type": issue_type,
                "avg_cycle_time_days": round(avg, 1),
                "issues_resolved": len(times)
            })
        type_analysis.sort(key=lambda x: x['avg_cycle_time_days'], reverse=True)
        
        # By assignee
        assignee_analysis = []
        for assignee, times in by_assignee.items():
            avg = sum(times) / len(times) if times else 0
            assignee_analysis.append({
                "assignee": assignee,
                "avg_cycle_time_days": round(avg, 1),
                "issues_resolved": len(times)
            })
        assignee_analysis.sort(key=lambda x: x['avg_cycle_time_days'], reverse=True)
        
        return {
            "overall": {
                "avg_cycle_time_days": round(avg_cycle_time, 1),
                "median_cycle_time_days": median_cycle_time,
                "total_resolved": len(cycle_times),
                "fastest_resolution_days": min(cycle_times) if cycle_times else 0,
                "slowest_resolution_days": max(cycle_times) if cycle_times else 0
            },
            "by_project": project_analysis[:10],
            "by_type": type_analysis,
            "by_assignee": assignee_analysis[:15]
        }
    
    async def get_velocity_trends(self, connection_id: str, weeks: int = 12) -> Dict[str, Any]:
        """
        Calculate velocity: issues completed per week over time.
        
        Returns:
        - Weekly completion rate
        - Trend (increasing/decreasing)
        - Comparison to avg
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(weeks=weeks)
        
        # Get resolved issues
        issues = await self.db.jira_issues.find(
            {
                "connection_id": connection_id,
                "resolved": {"$gte": cutoff_date.isoformat(), "$ne": None}
            },
            {
                "_id": 0,
                "resolved": 1
            }
        ).to_list(length=None)
        
        # Group by week
        weekly_counts = defaultdict(int)
        for issue in issues:
            resolved = datetime.fromisoformat(issue['resolved']) if issue.get('resolved') else None
            if resolved:
                # Get ISO week number
                year_week = f"{resolved.year}-W{resolved.isocalendar()[1]:02d}"
                weekly_counts[year_week] += 1
        
        # Convert to list and sort
        velocity_data = []
        for week, count in sorted(weekly_counts.items()):
            velocity_data.append({
                "week": week,
                "issues_completed": count
            })
        
        # Calculate trend
        if len(velocity_data) >= 2:
            recent_avg = sum(v['issues_completed'] for v in velocity_data[-4:]) / min(4, len(velocity_data[-4:]))
            older_avg = sum(v['issues_completed'] for v in velocity_data[:-4]) / max(1, len(velocity_data[:-4]))
            trend = "increasing" if recent_avg > older_avg * 1.1 else "decreasing" if recent_avg < older_avg * 0.9 else "stable"
        else:
            recent_avg = sum(v['issues_completed'] for v in velocity_data) / len(velocity_data) if velocity_data else 0
            trend = "insufficient_data"
        
        overall_avg = sum(v['issues_completed'] for v in velocity_data) / len(velocity_data) if velocity_data else 0
        
        return {
            "velocity_by_week": velocity_data,
            "summary": {
                "avg_weekly_velocity": round(overall_avg, 1),
                "recent_4_week_avg": round(recent_avg, 1) if len(velocity_data) >= 2 else round(overall_avg, 1),
                "trend": trend,
                "total_weeks_analyzed": len(velocity_data),
                "highest_velocity_week": max(velocity_data, key=lambda x: x['issues_completed']) if velocity_data else None,
                "lowest_velocity_week": min(velocity_data, key=lambda x: x['issues_completed']) if velocity_data else None
            }
        }
    
    async def get_executive_summary(self, connection_id: str) -> Dict[str, Any]:
        """
        Get high-level executive summary for CEO dashboard homepage.
        
        Returns:
        - Key metrics at a glance
        - Red flags
        - Performance indicators
        """
        # Get quick stats
        total_issues = await self.db.jira_issues.count_documents({"connection_id": connection_id})
        active_issues = await self.db.jira_issues.count_documents({"connection_id": connection_id, "resolved": None})
        total_projects = await self.db.jira_projects.count_documents({"connection_id": connection_id})
        total_users = await self.db.jira_users.count_documents({"connection_id": connection_id, "active": True})
        
        # Get bottleneck summary
        bottleneck_data = await self.get_bottleneck_analysis(connection_id, days=30)
        workload_data = await self.get_workload_distribution(connection_id)
        cycle_time_data = await self.get_cycle_time_analysis(connection_id, days=30)
        velocity_data = await self.get_velocity_trends(connection_id, weeks=8)
        
        # Identify red flags
        red_flags = []
        if bottleneck_data['total_stuck_issues'] > 50:
            red_flags.append(f"{bottleneck_data['total_stuck_issues']} issues stuck >14 days")
        if workload_data['summary']['unassigned_issues'] > 100:
            red_flags.append(f"{workload_data['summary']['unassigned_issues']} unassigned issues")
        if workload_data['summary']['overloaded_count'] > 5:
            red_flags.append(f"{workload_data['summary']['overloaded_count']} team members overloaded (>15 issues)")
        if cycle_time_data['overall']['avg_cycle_time_days'] > 30:
            red_flags.append(f"High avg cycle time: {cycle_time_data['overall']['avg_cycle_time_days']} days")
        if velocity_data['summary']['trend'] == "decreasing":
            red_flags.append("Velocity trending downward")
        
        return {
            "overview": {
                "total_issues": total_issues,
                "active_issues": active_issues,
                "resolved_issues": total_issues - active_issues,
                "total_projects": total_projects,
                "active_team_members": total_users
            },
            "key_metrics": {
                "bottlenecks_detected": bottleneck_data['total_bottlenecks'],
                "stuck_issues": bottleneck_data['total_stuck_issues'],
                "unassigned_work": workload_data['summary']['unassigned_issues'],
                "overloaded_members": workload_data['summary']['overloaded_count'],
                "avg_cycle_time_days": cycle_time_data['overall']['avg_cycle_time_days'],
                "weekly_velocity": velocity_data['summary']['avg_weekly_velocity'],
                "velocity_trend": velocity_data['summary']['trend']
            },
            "red_flags": red_flags,
            "health_score": max(0, 100 - len(red_flags) * 15)  # Simple health score
        }
