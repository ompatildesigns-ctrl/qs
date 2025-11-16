"""
Rule-Based Bottleneck Finder (RBBF)
Theory of Constraints + Flow Metrics based bottleneck detection
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from collections import defaultdict

from team_classifier import classify_team, get_team_label

logger = logging.getLogger(__name__)


class BottleneckFinder:
    """
    Rule-based bottleneck detection using Theory of Constraints.
    
    Flow Metrics:
    - Flow Efficiency: Active work time / Total cycle time
    - WIP: Work in progress count
    - Cycle Time: In Progress → Done
    - Waiting Time: Time in blocked/waiting statuses
    
    Bottleneck Categories:
    - Handoff Bottleneck: High waiting time + low flow efficiency
    - Capacity Bottleneck: High WIP + spiking cycle time
    - Stale Work Bottleneck: High stale count + high unassigned count
    """
    
    # Thresholds (Theory of Constraints based)
    FLOW_EFFICIENCY_THRESHOLD = 0.15  # Below 15% = bottleneck
    WIP_MULTIPLIER = 2.0  # WIP > 2x throughput = bottleneck
    CYCLE_TIME_SPIKE = 0.25  # 25% increase = bottleneck
    WAITING_TIME_RATIO = 0.50  # 50% of cycle time in waiting = bottleneck
    STALE_DAYS = 14  # No update in 14+ days
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def find_bottlenecks(
        self,
        connection_id: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Run complete bottleneck analysis.
        Returns top 3 bottlenecks ranked by financial impact.
        """
        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(days=days)
        
        # Get all active issues
        active_issues = await self.db.jira_issues.find({
            "connection_id": connection_id,
            "status": {"$nin": ["Done", "Resolved", "Closed", "Cancelled"]}
        }).to_list(None)
        
        # Calculate metrics
        flow_efficiency = await self._calculate_flow_efficiency(connection_id, days)
        wip_analysis = self._calculate_wip(active_issues)
        cycle_time_spike = await self._detect_cycle_time_spike(connection_id)
        waiting_analysis = self._calculate_waiting_time(active_issues)
        stale_analysis = self._analyze_stale_work(active_issues, now)
        
        # Run bottleneck rules
        bottlenecks = []
        
        # Rule 1: Handoff Bottleneck
        if waiting_analysis['waiting_ratio'] > self.WAITING_TIME_RATIO and flow_efficiency < self.FLOW_EFFICIENCY_THRESHOLD:
            bottlenecks.append({
                "type": "Handoff Bottleneck",
                "severity": "Critical",
                "metric_triggered": "Waiting Time + Flow Efficiency",
                "narrative": self._generate_handoff_narrative(waiting_analysis, flow_efficiency),
                "financial_impact": waiting_analysis['waiting_cost'],
                "affected_issues": waiting_analysis['waiting_count'],
                "action": "Trigger Review Alert",
                "action_endpoint": "/api/actions/notify-reviewers"
            })
        
        # Rule 2: Capacity Bottleneck
        if wip_analysis['wip_overload'] and cycle_time_spike['is_spiking']:
            bottlenecks.append({
                "type": "Capacity Bottleneck",
                "severity": "High",
                "metric_triggered": "WIP + Cycle Time",
                "narrative": self._generate_capacity_narrative(wip_analysis, cycle_time_spike),
                "financial_impact": wip_analysis['wip_cost'],
                "affected_issues": wip_analysis['wip_count'],
                "action": "Limit WIP",
                "action_endpoint": "/api/actions/limit-wip"
            })
        
        # Rule 3: Stale Work Bottleneck
        if stale_analysis['stale_count'] > 50 or stale_analysis['unassigned_count'] > 20:
            bottlenecks.append({
                "type": "Stale Work Bottleneck",
                "severity": "High",
                "metric_triggered": "Stale Issues + Unassigned",
                "narrative": self._generate_stale_narrative(stale_analysis),
                "financial_impact": stale_analysis['stale_cost'],
                "affected_issues": stale_analysis['stale_count'] + stale_analysis['unassigned_count'],
                "action": "Auto-Assign Stale",
                "action_endpoint": "/api/actions/auto-assign/execute"
            })
        
        # Sort by financial impact
        bottlenecks.sort(key=lambda x: x['financial_impact'], reverse=True)
        
        return {
            "timestamp": now.isoformat(),
            "period_days": days,
            "bottlenecks_found": len(bottlenecks),
            "top_bottlenecks": bottlenecks[:3],
            "metrics": {
                "flow_efficiency": round(flow_efficiency * 100, 1),
                "wip": wip_analysis['wip_count'],
                "avg_cycle_time": cycle_time_spike['current_avg'],
                "waiting_ratio": round(waiting_analysis['waiting_ratio'] * 100, 1)
            }
        }
    
    async def _calculate_flow_efficiency(self, connection_id: str, days: int) -> float:
        """Flow Efficiency = Active Work Time / Total Cycle Time"""
        # Simplified: Use resolved issues in period
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        resolved = await self.db.jira_issues.find({
            "connection_id": connection_id,
            "resolved": {"$gte": cutoff.isoformat()},
            "created": {"$exists": True},
            "resolved": {"$exists": True}
        }).to_list(100)
        
        if not resolved:
            return 0.20  # Default assumption
        
        total_cycle = 0
        total_active = 0
        
        for issue in resolved:
            # Skip issues with missing dates
            if not issue.get('created') or not issue.get('resolved'):
                continue
            
            try:
                created = datetime.fromisoformat(issue['created'].replace('Z', '+00:00'))
                resolved_dt = datetime.fromisoformat(issue['resolved'].replace('Z', '+00:00'))
                cycle_time = (resolved_dt - created).total_seconds() / 86400
                
                # Estimate active time as 25% of cycle (rest is waiting)
                active_time = cycle_time * 0.25
                
                total_cycle += cycle_time
                total_active += active_time
            except (ValueError, AttributeError):
                # Skip issues with invalid date formats
                continue
        
        return total_active / total_cycle if total_cycle > 0 else 0.20
    
    def _calculate_wip(self, active_issues: List[Dict]) -> Dict[str, Any]:
        """Calculate WIP and detect overload"""
        wip_count = len(active_issues)
        
        # Simple rule: WIP > 100 for typical team = overload
        wip_overload = wip_count > 100
        
        # Estimate cost (assume $500/day per item in WIP * avg 7 days)
        wip_cost = wip_count * 500 * 7
        
        return {
            "wip_count": wip_count,
            "wip_overload": wip_overload,
            "wip_cost": wip_cost
        }
    
    async def _detect_cycle_time_spike(self, connection_id: str) -> Dict[str, Any]:
        """Detect if cycle time is spiking"""
        now = datetime.now(timezone.utc)
        
        # Last 30 days avg
        recent_cutoff = now - timedelta(days=30)
        recent = await self.db.jira_issues.find({
            "connection_id": connection_id,
            "resolved": {"$gte": recent_cutoff.isoformat()}
        }).to_list(100)
        
        recent_avg = self._calc_avg_cycle_time(recent)
        
        # Previous 90 days avg
        historical_cutoff = now - timedelta(days=120)
        historical_start = now - timedelta(days=30)
        historical = await self.db.jira_issues.find({
            "connection_id": connection_id,
            "resolved": {"$gte": historical_cutoff.isoformat(), "$lt": historical_start.isoformat()}
        }).to_list(100)
        
        historical_avg = self._calc_avg_cycle_time(historical)
        
        # Spike if recent > 25% increase
        is_spiking = recent_avg > historical_avg * 1.25 if historical_avg > 0 else False
        
        return {
            "is_spiking": is_spiking,
            "current_avg": round(recent_avg, 1),
            "historical_avg": round(historical_avg, 1),
            "spike_pct": round(((recent_avg - historical_avg) / historical_avg * 100), 1) if historical_avg > 0 else 0
        }
    
    def _calc_avg_cycle_time(self, issues: List[Dict]) -> float:
        """Calculate average cycle time from issues"""
        if not issues:
            return 0
        
        total_days = 0
        count = 0
        
        for issue in issues:
            if 'created' in issue and 'resolved' in issue and issue['created'] and issue['resolved']:
                try:
                    created = datetime.fromisoformat(issue['created'].replace('Z', '+00:00'))
                    resolved = datetime.fromisoformat(issue['resolved'].replace('Z', '+00:00'))
                    days = (resolved - created).total_seconds() / 86400
                    total_days += days
                    count += 1
                except (ValueError, AttributeError):
                    continue
        
        return total_days / count if count > 0 else 0
    
    def _calculate_waiting_time(self, active_issues: List[Dict]) -> Dict[str, Any]:
        """Calculate waiting time ratio"""
        waiting_statuses = ["waiting", "blocked", "on hold", "pending", "review"]
        
        waiting_issues = [
            i for i in active_issues 
            if any(ws in (i.get('status') or '').lower() for ws in waiting_statuses)
        ]
        
        waiting_count = len(waiting_issues)
        total_count = len(active_issues)
        waiting_ratio = waiting_count / total_count if total_count > 0 else 0
        
        # Cost: $500/day per waiting issue * avg 10 days
        waiting_cost = waiting_count * 500 * 10
        
        return {
            "waiting_count": waiting_count,
            "total_count": total_count,
            "waiting_ratio": waiting_ratio,
            "waiting_cost": waiting_cost
        }
    
    def _analyze_stale_work(self, active_issues: List[Dict], now: datetime) -> Dict[str, Any]:
        """Analyze stale and unassigned work"""
        stale_issues = []
        unassigned_issues = []
        
        for issue in active_issues:
            # Check stale
            if 'updated' in issue:
                updated = datetime.fromisoformat(issue['updated'].replace('Z', '+00:00'))
                days_stale = (now - updated).total_seconds() / 86400
                if days_stale >= self.STALE_DAYS:
                    stale_issues.append(issue)
            
            # Check unassigned
            if not issue.get('assignee'):
                unassigned_issues.append(issue)
        
        stale_count = len(stale_issues)
        unassigned_count = len(unassigned_issues)
        
        # Cost
        stale_cost = stale_count * 500 * 20  # $500/day * 20 days avg stale
        
        return {
            "stale_count": stale_count,
            "unassigned_count": unassigned_count,
            "stale_cost": stale_cost
        }
    
    def _generate_handoff_narrative(self, waiting_analysis: Dict, flow_efficiency: float) -> str:
        """Generate handoff bottleneck narrative"""
        return f"Handoff Bottleneck detected: {waiting_analysis['waiting_count']} issues are waiting for review/approval, causing Flow Efficiency to drop to {round(flow_efficiency * 100, 1)}%. This indicates a constraint in the review/approval process. Cost: ${waiting_analysis['waiting_cost']:,}/period."
    
    def _generate_capacity_narrative(self, wip: Dict, cycle_time: Dict) -> str:
        """Generate capacity bottleneck narrative"""
        return f"Capacity Bottleneck detected: Work in Progress ({wip['wip_count']} issues) is overloading the team, causing Cycle Time to spike by {cycle_time['spike_pct']}% (from {cycle_time['historical_avg']} to {cycle_time['current_avg']} days). The team is starting too much work and not finishing enough. Cost: ${wip['wip_cost']:,}/period."
    
    def _generate_stale_narrative(self, stale: Dict) -> str:
        """Generate stale work bottleneck narrative"""
        return f"Stale Work Bottleneck detected: {stale['stale_count']} issues haven't been updated in 14+ days and {stale['unassigned_count']} issues are unassigned. This abandoned work is costing ${stale['stale_cost']:,}/period. Immediate action needed to recover value."
