"""
Intelligent Insights Engine
Analyzes trends, detects patterns, generates insights and recommendations
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class InsightsEngine:
    """
    Generates intelligent insights from Jira data.
    Detects trends, patterns, and provides actionable recommendations.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def generate_insights(
        self,
        connection_id: str,
        current_period_days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Generate intelligent insights from data.
        Returns list of insights ranked by importance.
        """
        insights = []
        
        # Get current and previous period data for comparison
        current = await self._get_period_metrics(connection_id, current_period_days)
        previous = await self._get_period_metrics(connection_id, current_period_days * 2, offset_days=current_period_days)
        
        # Trend 1: Velocity Change
        if previous['velocity'] > 0:
            velocity_change = ((current['velocity'] - previous['velocity']) / previous['velocity']) * 100
            if abs(velocity_change) > 10:  # Significant change
                direction = "increased" if velocity_change > 0 else "decreased"
                severity = "positive" if velocity_change > 0 else "critical"
                insights.append({
                    "type": "velocity_trend",
                    "severity": severity,
                    "title": f"Velocity {direction} {abs(velocity_change):.0f}%",
                    "description": f"Your team completed {current['velocity']} issues this period vs {previous['velocity']} last period.",
                    "insight": self._explain_velocity_change(velocity_change, current, previous),
                    "recommendation": self._recommend_velocity_action(velocity_change, current),
                    "impact_score": abs(velocity_change)
                })
        
        # Trend 2: Cycle Time Change
        if previous['avg_cycle_time'] > 0:
            cycle_change = ((current['avg_cycle_time'] - previous['avg_cycle_time']) / previous['avg_cycle_time']) * 100
            if abs(cycle_change) > 15:
                direction = "increased" if cycle_change > 0 else "decreased"
                severity = "critical" if cycle_change > 0 else "positive"
                insights.append({
                    "type": "cycle_time_trend",
                    "severity": severity,
                    "title": f"Cycle time {direction} {abs(cycle_change):.0f}%",
                    "description": f"Average time to complete work is now {current['avg_cycle_time']:.1f} days (was {previous['avg_cycle_time']:.1f}).",
                    "insight": self._explain_cycle_time_change(cycle_change, current),
                    "recommendation": self._recommend_cycle_time_action(cycle_change),
                    "impact_score": abs(cycle_change)
                })
        
        # Trend 3: Stale Work Growing
        stale_change = current['stale_count'] - previous['stale_count']
        if stale_change > 20:
            insights.append({
                "type": "stale_growth",
                "severity": "critical",
                "title": f"Stale work growing ({stale_change} new in last period)",
                "description": f"You now have {current['stale_count']} stale issues (14+ days no update), up from {previous['stale_count']}.",
                "insight": "Pattern suggests: Team is starting more work than they can finish, or priorities are shifting and work is being abandoned.",
                "recommendation": f"Immediately archive the {int(stale_change * 0.3)} oldest stale issues to free team capacity, then address root cause (likely overcommitment or unclear priorities).",
                "impact_score": stale_change
            })
        
        # Pattern 4: Team Performance Divergence
        if current['sundew_velocity'] > 0 and current['us_velocity'] > 0:
            sundew_efficiency = current['sundew_velocity'] / max(current['sundew_assigned'], 1)
            us_efficiency = current['us_velocity'] / max(current['us_assigned'], 1)
            
            if sundew_efficiency > us_efficiency * 1.5:
                insights.append({
                    "type": "team_efficiency",
                    "severity": "insight",
                    "title": "Sundew team 50%+ more efficient than US team",
                    "description": f"Sundew completes {sundew_efficiency:.1f} issues per active developer vs {us_efficiency:.1f} for US team.",
                    "insight": "Pattern suggests: Contractors may have fewer distractions, clearer focus, or different skill alignment with assigned work.",
                    "recommendation": f"Consider shifting {int(current['us_assigned'] * 0.2)} issues from US team to Sundew team to optimize overall throughput and reduce CoD.",
                    "impact_score": 30
                })
        
        # Sort by impact
        insights.sort(key=lambda x: x['impact_score'], reverse=True)
        
        return insights[:10]  # Top 10
    
    async def _get_period_metrics(
        self,
        connection_id: str,
        days: int,
        offset_days: int = 0
    ) -> Dict[str, Any]:
        """Get metrics for a specific time period"""
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days + offset_days)
        end = now - timedelta(days=offset_days)
        
        # Query issues in period
        completed = await self.db.jira_issues.find({
            "connection_id": connection_id,
            "resolved": {"$gte": start.isoformat(), "$lt": end.isoformat()}
        }).to_list(None)
        
        active = await self.db.jira_issues.find({
            "connection_id": connection_id,
            "status": {"$nin": ["Done", "Resolved", "Closed"]},
            "updated": {"$gte": start.isoformat()}
        }).to_list(None)
        
        # Calculate metrics
        velocity = len(completed)
        avg_cycle = sum([self._calc_cycle_days(i) for i in completed]) / len(completed) if completed else 0
        stale_count = len([i for i in active if self._is_stale(i, now)])
        
        # Team breakdown
        sundew_completed = [i for i in completed if self._is_sundew(i.get('assignee'))]
        us_completed = [i for i in completed if self._is_us(i.get('assignee'))]
        
        return {
            "velocity": velocity,
            "avg_cycle_time": avg_cycle,
            "stale_count": stale_count,
            "sundew_velocity": len(sundew_completed),
            "us_velocity": len(us_completed),
            "sundew_assigned": len([i for i in active if self._is_sundew(i.get('assignee'))]),
            "us_assigned": len([i for i in active if self._is_us(i.get('assignee'))])
        }
    
    def _calc_cycle_days(self, issue: Dict) -> float:
        """Calculate cycle time in days"""
        if 'created' not in issue or 'resolved' not in issue:
            return 0
        created = datetime.fromisoformat(issue['created'].replace('Z', '+00:00'))
        resolved = datetime.fromisoformat(issue['resolved'].replace('Z', '+00:00'))
        return (resolved - created).total_seconds() / 86400
    
    def _is_stale(self, issue: Dict, now: datetime) -> bool:
        """Check if issue is stale (14+ days no update)"""
        if 'updated' not in issue:
            return False
        updated = datetime.fromisoformat(issue['updated'].replace('Z', '+00:00'))
        return (now - updated).total_seconds() / 86400 >= 14
    
    def _is_sundew(self, assignee: str) -> bool:
        """Check if assignee is Sundew team"""
        if not assignee:
            return False
        from team_classifier import classify_team
        return classify_team(assignee) == "sundew"
    
    def _is_us(self, assignee: str) -> bool:
        """Check if assignee is US team"""
        if not assignee:
            return False
        from team_classifier import classify_team
        return classify_team(assignee) == "us"
    
    def _explain_velocity_change(self, change_pct: float, current: Dict, previous: Dict) -> str:
        """Explain why velocity changed"""
        if change_pct < -20:
            return f"Sharp decline from {previous['velocity']} to {current['velocity']} issues suggests: Team capacity reduced, priorities shifted, or external blockers introduced. Check for: New team members onboarding, process changes, or dependency bottlenecks."
        elif change_pct > 20:
            return f"Strong improvement from {previous['velocity']} to {current['velocity']} issues suggests: Team found efficiency gains, removed blockers, or increased focus. Sustain by: Documenting what changed and replicating across teams."
        else:
            return f"Stable velocity around {current['velocity']} issues per period indicates consistent team performance."
    
    def _recommend_velocity_action(self, change_pct: float, current: Dict) -> str:
        """Recommend action based on velocity trend"""
        if change_pct < -20:
            return f"URGENT: Investigate root cause of {abs(change_pct):.0f}% velocity decline. Interview team to identify blockers. Consider: Reducing WIP, removing non-essential meetings, or adding temporary capacity."
        elif change_pct > 20:
            return f"Capitalize on momentum: Document what's working and share learnings across teams. Consider: Taking on higher-value work now that capacity exists."
        else:
            return "Maintain current practices. Monitor for early signs of degradation."
    
    def _explain_cycle_time_change(self, change_pct: float, current: Dict) -> str:
        """Explain why cycle time changed"""
        if change_pct > 15:
            return f"Cycle time increased {change_pct:.0f}%, indicating work is taking longer to complete. Likely causes: Increased complexity, more handoffs, skill gaps, or external dependencies. Check: Code review backlog, QA bottlenecks, or blocked status issues."
        else:
            return f"Cycle time improved {abs(change_pct):.0f}%, indicating work is flowing faster. Sustain by maintaining current team focus and process discipline."
    
    def _recommend_cycle_time_action(self, change_pct: float) -> str:
        """Recommend action for cycle time"""
        if change_pct > 15:
            return "Focus on: (1) Reducing handoffs between teams, (2) Limiting WIP to force completion, (3) Pairing developers on complex work to reduce skill gaps. Target: Return cycle time to previous baseline within 30 days."
        else:
            return "Keep doing what's working. Document the process improvements that led to faster cycle time."
