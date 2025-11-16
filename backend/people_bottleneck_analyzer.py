"""
People Bottleneck Analyzer
Identifies which individuals are bottlenecks and calculates their burden level
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from collections import Counter, defaultdict

from team_classifier import classify_team, get_team_label

logger = logging.getLogger(__name__)


class PeopleBottleneckAnalyzer:
    """
    Analyzes people as bottlenecks.
    Shows: Who is overloaded, why, how much value blocked, delegation recommendations.
    """
    
    # Actual company costs (provided by customer)
    # Sundew contractors: $20/hour
    # US employees (product, operations, marketing, design): $35/hour average
    SUNDEW_HOURLY_RATE = 20
    US_HOURLY_RATE = 35
    HOURS_PER_DAY = 8
    
    SUNDEW_DAILY_COST = SUNDEW_HOURLY_RATE * HOURS_PER_DAY  # $160/day
    US_DAILY_COST = US_HOURLY_RATE * HOURS_PER_DAY  # $280/day
    
    # Psychology-based burden thresholds
    OPTIMAL_WORKLOAD = 5  # issues per person
    OVERLOADED_THRESHOLD = 10  # 2x optimal
    CRITICAL_THRESHOLD = 15  # 3x optimal
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def analyze_people_bottlenecks(
        self,
        connection_id: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Identify which people are bottlenecks.
        Returns: Who, Why, How much value blocked, Burden level, Delegation recs.
        """
        # Get active issues
        active_issues = await self.db.jira_issues.find({
            "connection_id": connection_id,
            "status": {"$nin": ["Done", "Resolved", "Closed", "Cancelled"]}
        }).to_list(None)
        
        # Group by assignee
        assignee_workload = defaultdict(list)
        for issue in active_issues:
            assignee = issue.get('assignee') or 'Unassigned'
            assignee_workload[assignee].append(issue)
        
        # Analyze each person
        people_bottlenecks = []
        total_blocked_value = 0
        
        for assignee, issues in assignee_workload.items():
            if assignee == 'Unassigned':
                continue  # Handle separately
            
            workload = len(issues)
            
            # Calculate burden level (0-100%)
            burden_pct = min((workload / self.OPTIMAL_WORKLOAD) * 100, 100)
            
            # Determine if bottleneck
            is_bottleneck = workload >= self.OVERLOADED_THRESHOLD
            
            if is_bottleneck:
                # Calculate blocked value using actual company rates
                team = classify_team(assignee)
                daily_cost = self.SUNDEW_DAILY_COST if team == "sundew" else self.US_DAILY_COST
                
                # Stale issues for this person
                now = datetime.now(timezone.utc)
                stale_issues = [
                    i for i in issues 
                    if self._is_stale(i, now)
                ]
                
                # Value blocked = stale issues * avg days stale * daily cost
                total_stale_days = sum([
                    self._days_stale(i, now) for i in stale_issues
                ])
                avg_stale_days = total_stale_days / len(stale_issues) if stale_issues else 0
                blocked_value = len(stale_issues) * avg_stale_days * daily_cost
                
                total_blocked_value += blocked_value
                
                # Why they're a bottleneck
                reasons = []
                if workload >= self.CRITICAL_THRESHOLD:
                    reasons.append(f"Critically overloaded ({workload} issues, 3x optimal)")
                elif workload >= self.OVERLOADED_THRESHOLD:
                    reasons.append(f"Overloaded ({workload} issues, 2x optimal)")
                
                if len(stale_issues) > 5:
                    reasons.append(f"{len(stale_issues)} issues stale (avg {avg_stale_days:.0f} days)")
                
                if len(issues) - len(stale_issues) > 8:
                    reasons.append(f"Too much active work ({len(issues) - len(stale_issues)} non-stale)")
                
                # PRODUCT BLOCKING ANALYSIS
                blocked_projects = {}
                for issue in stale_issues:
                    project = issue.get('project', 'Unknown')
                    if project not in blocked_projects:
                        blocked_projects[project] = {
                            "count": 0,
                            "oldest_issue": None,
                            "oldest_days": 0,
                            "issue_keys": []
                        }
                    blocked_projects[project]["count"] += 1
                    blocked_projects[project]["issue_keys"].append(issue.get('key'))
                    
                    days = self._days_stale(issue, now)
                    if days > blocked_projects[project]["oldest_days"]:
                        blocked_projects[project]["oldest_days"] = days
                        blocked_projects[project]["oldest_issue"] = issue.get('key')
                
                # Sort projects by blocked count
                blocked_products = sorted(
                    blocked_projects.items(),
                    key=lambda x: x[1]["count"],
                    reverse=True
                )[:5]  # Top 5 products blocked
                
                people_bottlenecks.append({
                    "person": assignee,
                    "team": get_team_label(team),
                    "workload": workload,
                    "optimal_workload": self.OPTIMAL_WORKLOAD,
                    "burden_percentage": round(burden_pct, 1),
                    "burden_level": self._get_burden_level(burden_pct),
                    "stale_count": len(stale_issues),
                    "avg_stale_days": round(avg_stale_days, 1),
                    "blocked_value": round(blocked_value, 0),
                    "daily_cost": daily_cost,
                    "reasons": reasons,
                    "top_stale_issue": stale_issues[0].get('key') if stale_issues else None,
                    "blocked_products": [
                        {
                            "product": proj,
                            "stale_count": data["count"],
                            "oldest_issue": data["oldest_issue"],
                            "oldest_days": round(data["oldest_days"], 0),
                            "issue_keys": data["issue_keys"][:5]  # Top 5 issue keys
                        }
                        for proj, data in blocked_products
                    ],
                    "delegation_recommendation": self._generate_delegation_rec(assignee, workload, issues)
                })
        
        # Sort by blocked value
        people_bottlenecks.sort(key=lambda x: x['blocked_value'], reverse=True)
        
        # Get underloaded people for delegation
        underloaded = [
            {"person": assignee, "workload": len(issues), "capacity": self.OPTIMAL_WORKLOAD - len(issues)}
            for assignee, issues in assignee_workload.items()
            if assignee != 'Unassigned' and len(issues) < self.OPTIMAL_WORKLOAD
        ]
        underloaded.sort(key=lambda x: x['capacity'], reverse=True)
        
        return {
            "total_people_bottlenecks": len(people_bottlenecks),
            "total_blocked_value": total_blocked_value,
            "people_bottlenecks": people_bottlenecks[:10],  # Top 10
            "underloaded_people": underloaded[:5],  # Top 5 with capacity
            "delegation_opportunities": len(people_bottlenecks) * len(underloaded),
            "average_burden": round(sum([p['burden_percentage'] for p in people_bottlenecks]) / len(people_bottlenecks), 1) if people_bottlenecks else 0
        }
    
    def _is_stale(self, issue: Dict, now: datetime) -> bool:
        """Check if issue is stale"""
        if 'updated' not in issue or not issue['updated']:
            return False
        try:
            updated = datetime.fromisoformat(issue['updated'].replace('Z', '+00:00'))
            return (now - updated).total_seconds() / 86400 >= 14
        except:
            return False
    
    def _days_stale(self, issue: Dict, now: datetime) -> float:
        """Calculate days stale"""
        if 'updated' not in issue or not issue['updated']:
            return 0
        try:
            updated = datetime.fromisoformat(issue['updated'].replace('Z', '+00:00'))
            return (now - updated).total_seconds() / 86400
        except:
            return 0
    
    def _get_burden_level(self, burden_pct: float) -> str:
        """Get psychology-based burden level"""
        if burden_pct >= 300:  # 3x optimal
            return "Critical Burnout Risk"
        elif burden_pct >= 200:  # 2x optimal
            return "Severely Overloaded"
        elif burden_pct >= 150:
            return "Overloaded"
        elif burden_pct >= 100:
            return "At Capacity"
        elif burden_pct >= 80:
            return "Near Capacity"
        else:
            return "Available"
    
    def _generate_delegation_rec(self, assignee: str, workload: int, issues: List) -> str:
        """Generate delegation recommendation"""
        excess = workload - self.OPTIMAL_WORKLOAD
        
        if excess >= 10:
            return f"URGENT: Delegate {excess} issues immediately to prevent burnout. Prioritize oldest stale work for reassignment."
        elif excess >= 5:
            return f"Delegate {excess} issues to available team members. Focus on work that can be easily transferred."
        elif excess >= 3:
            return f"Consider delegating {excess} lower-priority issues to balance workload."
        else:
            return "Monitor workload - approaching capacity threshold."
