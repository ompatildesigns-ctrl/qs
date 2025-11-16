"""
Financial analytics for quantifying bottleneck costs and ROI.
Calculates Cost of Delay, Opportunity Cost, and Resource ROI.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from collections import defaultdict

from team_classifier import classify_team, get_team_label

logger = logging.getLogger(__name__)


class FinancialAnalytics:
    """
    Calculate financial impact of bottlenecks using industry-standard formulas.
    
    Default assumptions (industry standards for software teams):
    - US Developer: $150K/year = $600/day = $75/hour
    - Sundew Contractor: $80K/year = $320/day = $40/hour
    - Average Revenue per Developer: $250K/year
    - Working days: 250/year
    """
    
    # Actual company costs (provided by customer - Liberty Home Guard)
    # Sundew contractors: $20/hour
    # US employees (product, operations, marketing, design): $35/hour average
    SUNDEW_HOURLY_RATE = 20
    US_HOURLY_RATE = 35
    HOURS_PER_DAY = 8
    
    SUNDEW_DAILY_COST = SUNDEW_HOURLY_RATE * HOURS_PER_DAY  # $160/day
    US_DAILY_COST = US_HOURLY_RATE * HOURS_PER_DAY  # $280/day
    BLENDED_DAILY_COST = (SUNDEW_DAILY_COST + US_DAILY_COST) / 2  # $220/day
    
    # Liberty Home Guard actual revenue per employee
    # Company: ~$25M-$50M revenue, 229 employees
    # Revenue per employee: $109K-$219K (using midpoint $164K)
    REVENUE_PER_DEVELOPER_ANNUAL = 164000  # Actual Liberty Home Guard data
    WORKING_DAYS_PER_YEAR = 250
    REVENUE_PER_DEVELOPER_DAILY = REVENUE_PER_DEVELOPER_ANNUAL / WORKING_DAYS_PER_YEAR  # $656/day
    
    # WSJF Priority Multipliers (SAFe framework alignment)
    PRIORITY_MULTIPLIERS = {
        "Highest": 10,  # Customer-facing, revenue-blocking
        "High": 5,      # Important business value
        "Medium": 2,    # Standard work
        "Low": 1,       # Nice-to-have
        "Lowest": 1
    }
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    def _get_team_daily_cost(self, team: str) -> float:
        """Get daily cost for a team member."""
        if team == "us":
            return self.US_DAILY_COST
        elif team == "sundew":
            return self.SUNDEW_DAILY_COST
        else:
            return self.BLENDED_DAILY_COST
    
    async def get_cost_of_delay_analysis(
        self,
        connection_id: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Calculate Cost of Delay for all bottlenecks.
        
        Formula: CoD = (Daily Cost × Days Stuck) per issue
        
        Returns total CoD and breakdown by category:
        - Stale issues (no update in 14+ days)
        - Unassigned issues
        - Waiting/blocked issues
        - Cross-team handoffs
        """
        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(days=days)
        
        # Get active issues within the time period
        # Filter by created or updated date to get issues active in this period
        issues = await self.db.jira_issues.find(
            {
                "connection_id": connection_id,
                "status": {"$nin": ["Done", "Resolved", "Closed", "Cancelled"]},
                "$or": [
                    {"created": {"$gte": cutoff_date.isoformat()}},
                    {"updated": {"$gte": cutoff_date.isoformat()}}
                ]
            },
            {
                "_id": 0,
                "key": 1,
                "assignee": 1,
                "status": 1,
                "updated": 1,
                "created": 1,
                "priority": 1,
                "summary": 1
            }
        ).to_list(None)
        
        # Categorize and calculate CoD
        stale_cost = 0
        unassigned_cost = 0
        waiting_cost = 0
        total_issues_analyzed = 0
        
        stale_issues_detail = []
        unassigned_issues_detail = []
        waiting_issues_detail = []
        
        waiting_statuses = ["waiting", "blocked", "on hold", "pending", "paused"]
        
        for issue in issues:
            assignee = issue.get("assignee")
            status = (issue.get("status") or "").lower()
            updated = issue.get("updated")
            created = issue.get("created")
            
            # Determine daily cost based on assignee team
            if assignee:
                team = classify_team(assignee)
                daily_cost = self._get_team_daily_cost(team)
            else:
                daily_cost = self.BLENDED_DAILY_COST
            
            # Get priority multiplier for WSJF alignment (SAFe framework)
            priority = issue.get("priority")
            priority_multiplier = self.PRIORITY_MULTIPLIERS.get(priority, 2)  # Default to Medium
            
            total_issues_analyzed += 1
            
            # Calculate stale cost (no update in 14+ days)
            if updated:
                if isinstance(updated, str):
                    updated = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                days_stale = (now - updated).total_seconds() / 86400
                
                if days_stale >= 14:
                    cost = daily_cost * days_stale * priority_multiplier  # WSJF weighted
                    stale_cost += cost
                    stale_issues_detail.append({
                        "key": issue.get("key"),
                        "summary": issue.get("summary", "")[:60],
                        "assignee": assignee or "Unassigned",
                        "priority": priority or "Medium",
                        "days_stale": round(days_stale, 1),
                        "cost_of_delay": round(cost, 0),
                        "team": get_team_label(classify_team(assignee)) if assignee else "Unassigned"
                    })
            
            # Calculate unassigned cost
            if not assignee:
                if created:
                    if isinstance(created, str):
                        created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    days_unassigned = (now - created).total_seconds() / 86400
                    cost = self.BLENDED_DAILY_COST * days_unassigned * priority_multiplier  # WSJF weighted
                    unassigned_cost += cost
                    unassigned_issues_detail.append({
                        "key": issue.get("key"),
                        "summary": issue.get("summary", "")[:60],
                        "priority": priority or "Medium",
                        "days_unassigned": round(days_unassigned, 1),
                        "cost_of_delay": round(cost, 0)
                    })
            
            # Calculate waiting/blocked cost
            if any(ws in status for ws in waiting_statuses):
                if updated:
                    if isinstance(updated, str):
                        updated = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                    days_waiting = (now - updated).total_seconds() / 86400
                    cost = daily_cost * days_waiting * priority_multiplier  # WSJF weighted
                    waiting_cost += cost
                    waiting_issues_detail.append({
                        "key": issue.get("key"),
                        "summary": issue.get("summary", "")[:60],
                        "status": issue.get("status"),
                        "assignee": assignee or "Unassigned",
                        "priority": priority or "Medium",
                        "days_waiting": round(days_waiting, 1),
                        "cost_of_delay": round(cost, 0),
                        "team": get_team_label(classify_team(assignee)) if assignee else "Unassigned"
                    })
        
        # Sort by cost descending
        stale_issues_detail.sort(key=lambda x: x["cost_of_delay"], reverse=True)
        unassigned_issues_detail.sort(key=lambda x: x["cost_of_delay"], reverse=True)
        waiting_issues_detail.sort(key=lambda x: x["cost_of_delay"], reverse=True)
        
        total_cost_of_delay = stale_cost + unassigned_cost + waiting_cost
        
        # Calculate insights
        insights = []
        if total_cost_of_delay > 1000000:
            insights.append(f"🔴 CRITICAL: ${total_cost_of_delay/1000000:.1f}M in preventable costs identified")
        elif total_cost_of_delay > 500000:
            insights.append(f"⚠️ HIGH IMPACT: ${total_cost_of_delay/1000:.0f}K in preventable costs")
        
        if stale_cost > unassigned_cost and stale_cost > waiting_cost:
            insights.append(f"💰 Biggest opportunity: ${stale_cost/1000:.0f}K from {len(stale_issues_detail)} stale issues")
        elif unassigned_cost > waiting_cost:
            insights.append(f"💰 Biggest opportunity: ${unassigned_cost/1000:.0f}K from {len(unassigned_issues_detail)} unassigned issues")
        else:
            insights.append(f"💰 Biggest opportunity: ${waiting_cost/1000:.0f}K from {len(waiting_issues_detail)} waiting/blocked issues")
        
        return {
            "total_cost_of_delay": round(total_cost_of_delay, 0),
            "total_issues_analyzed": total_issues_analyzed,
            "breakdown": {
                "stale_issues": {
                    "count": len(stale_issues_detail),
                    "total_cost": round(stale_cost, 0),
                    "top_issues": stale_issues_detail[:15]
                },
                "unassigned_issues": {
                    "count": len(unassigned_issues_detail),
                    "total_cost": round(unassigned_cost, 0),
                    "top_issues": unassigned_issues_detail[:15]
                },
                "waiting_blocked_issues": {
                    "count": len(waiting_issues_detail),
                    "total_cost": round(waiting_cost, 0),
                    "top_issues": waiting_issues_detail[:15]
                }
            },
            "daily_burn_rate": round(total_cost_of_delay / max(days, 1), 0),
            "insights": insights,
            "cost_assumptions": {
                "us_developer_daily": self.US_DAILY_COST,
                "sundew_contractor_daily": self.SUNDEW_DAILY_COST,
                "blended_daily": self.BLENDED_DAILY_COST
            }
        }
    
    async def get_team_roi_analysis(
        self,
        connection_id: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Calculate ROI for each team.
        
        Formula: ROI = (Value Delivered / Cost) × 100
        - Cost = Daily Rate × Days Active
        - Value = Issues Completed × Revenue per Issue
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get completed issues in period
        issues = await self.db.jira_issues.find(
            {
                "connection_id": connection_id,
                "resolved": {"$gte": cutoff_date.isoformat()}
            },
            {
                "_id": 0,
                "assignee": 1,
                "created": 1,
                "resolved": 1,
                "priority": 1
            }
        ).to_list(None)
        
        # Calculate per team
        team_stats = {
            "sundew": {"issues_completed": 0, "total_cost": 0, "value_delivered": 0},
            "us": {"issues_completed": 0, "total_cost": 0, "value_delivered": 0}
        }
        
        for issue in issues:
            assignee = issue.get("assignee")
            if not assignee:
                continue
            
            team = classify_team(assignee)
            if team not in ["sundew", "us"]:
                continue
            
            created = issue.get("created")
            resolved = issue.get("resolved")
            
            if created and resolved:
                if isinstance(created, str):
                    created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                if isinstance(resolved, str):
                    resolved = datetime.fromisoformat(resolved.replace('Z', '+00:00'))
                
                cycle_days = (resolved - created).total_seconds() / 86400
                daily_cost = self._get_team_daily_cost(team)
                
                # Cost = daily rate × cycle time
                issue_cost = daily_cost * cycle_days
                
                # Value = revenue per developer × cycle time (what they could have generated)
                issue_value = self.REVENUE_PER_DEVELOPER_DAILY * cycle_days
                
                team_stats[team]["issues_completed"] += 1
                team_stats[team]["total_cost"] += issue_cost
                team_stats[team]["value_delivered"] += issue_value
        
        # Calculate ROI percentages (Industry Standard: Net Gain formula)
        results = {}
        for team, stats in team_stats.items():
            if stats["total_cost"] > 0:
                # Industry Standard ROI = (Value - Cost) / Cost × 100
                # This shows NET GAIN (profit above investment)
                roi = ((stats["value_delivered"] - stats["total_cost"]) / stats["total_cost"]) * 100
            else:
                roi = 0
            
            results[team] = {
                "team_label": get_team_label(team),
                "issues_completed": stats["issues_completed"],
                "total_cost": round(stats["total_cost"], 0),
                "value_delivered": round(stats["value_delivered"], 0),
                "roi_percentage": round(roi, 1),
                "cost_per_issue": round(stats["total_cost"] / stats["issues_completed"], 0) if stats["issues_completed"] > 0 else 0,
                "value_per_issue": round(stats["value_delivered"] / stats["issues_completed"], 0) if stats["issues_completed"] > 0 else 0
            }
        
        # Insights
        insights = []
        sundew_roi = results.get("sundew", {}).get("roi_percentage", 0)
        us_roi = results.get("us", {}).get("roi_percentage", 0)
        
        if sundew_roi > us_roi * 1.5:
            insights.append(f"💡 Sundew team delivers {sundew_roi/us_roi:.1f}x better ROI than US team")
            insights.append(f"💰 Consider shifting more work to Sundew for improved cost efficiency")
        elif us_roi > sundew_roi * 1.5:
            insights.append(f"💡 US team delivers {us_roi/sundew_roi:.1f}x better ROI than Sundew team")
        
        return {
            "period_days": days,
            "team_roi": results,
            "insights": insights
        }
    
    async def get_opportunity_cost_analysis(
        self,
        connection_id: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Calculate Opportunity Cost: revenue lost from delays.
        
        Formula: Opportunity Cost = Potential Revenue - Actual Revenue
        - Potential Revenue = Revenue per Dev × Available Dev Days
        - Actual Revenue = Issues Completed × Revenue per Issue
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get all users
        users = await self.db.jira_users.find(
            {
                "connection_id": connection_id,
                "active": True
            },
            {
                "_id": 0,
                "account_id": 1
            }
        ).to_list(None)
        
        total_developers = len(users)
        
        # Potential revenue if all devs worked optimally
        potential_revenue = total_developers * self.REVENUE_PER_DEVELOPER_DAILY * days
        
        # Get completed issues in period
        completed_issues = await self.db.jira_issues.count_documents({
            "connection_id": connection_id,
            "resolved": {"$gte": cutoff_date.isoformat()}
        })
        
        # Actual value delivered (simplified: issues × avg value)
        avg_value_per_issue = self.REVENUE_PER_DEVELOPER_DAILY * 3  # assume avg 3 days per issue
        actual_revenue = completed_issues * avg_value_per_issue
        
        # Opportunity cost
        opportunity_cost = potential_revenue - actual_revenue
        
        # Utilization rate
        utilization_rate = (actual_revenue / potential_revenue * 100) if potential_revenue > 0 else 0
        
        # Insights
        insights = []
        if utilization_rate < 50:
            insights.append(f"🔴 CRITICAL: Only {utilization_rate:.0f}% team utilization - ${opportunity_cost/1000000:.1f}M opportunity loss")
        elif utilization_rate < 70:
            insights.append(f"⚠️ Warning: {utilization_rate:.0f}% team utilization - significant improvement potential")
        else:
            insights.append(f"✅ Good: {utilization_rate:.0f}% team utilization")
        
        return {
            "period_days": days,
            "total_developers": total_developers,
            "potential_revenue": round(potential_revenue, 0),
            "actual_revenue": round(actual_revenue, 0),
            "opportunity_cost": round(opportunity_cost, 0),
            "utilization_rate": round(utilization_rate, 1),
            "insights": insights
        }
    
    async def get_bottleneck_impact_score(
        self,
        connection_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Rank bottlenecks by total financial impact.
        
        Combines:
        - Cost of Delay
        - Number of issues affected
        - Downstream impact (how many issues are blocked)
        """
        # Get cost of delay analysis
        cod_analysis = await self.get_cost_of_delay_analysis(connection_id, days)
        
        # Rank categories by cost
        bottlenecks = []
        
        for category, data in cod_analysis["breakdown"].items():
            if data["count"] > 0:
                bottlenecks.append({
                    "category": category.replace("_", " ").title(),
                    "count": data["count"],
                    "total_cost": data["total_cost"],
                    "avg_cost_per_issue": round(data["total_cost"] / data["count"], 0),
                    "recovery_potential": data["total_cost"]  # all cost is recoverable
                })
        
        # Sort by total cost
        bottlenecks.sort(key=lambda x: x["total_cost"], reverse=True)
        
        return {
            "period_days": days,
            "total_bottleneck_cost": cod_analysis["total_cost_of_delay"],
            "ranked_bottlenecks": bottlenecks,
            "quick_wins": [
                {
                    "action": f"Auto-assign {cod_analysis['breakdown']['unassigned_issues']['count']} unassigned issues",
                    "recovery_potential": cod_analysis['breakdown']['unassigned_issues']['total_cost'],
                    "effort": "1 day",
                    "roi": "Very High"
                },
                {
                    "action": f"Clear {cod_analysis['breakdown']['waiting_blocked_issues']['count']} waiting/blocked issues",
                    "recovery_potential": cod_analysis['breakdown']['waiting_blocked_issues']['total_cost'],
                    "effort": "1 week",
                    "roi": "High"
                },
                {
                    "action": f"Address {cod_analysis['breakdown']['stale_issues']['count']} stale issues",
                    "recovery_potential": cod_analysis['breakdown']['stale_issues']['total_cost'],
                    "effort": "2 weeks",
                    "roi": "High"
                }
            ]
        }
    
    async def get_financial_summary(
        self,
        connection_id: str
    ) -> Dict[str, Any]:
        """
        Get complete financial overview combining all metrics.
        """
        # Run all analyses
        cod_30 = await self.get_cost_of_delay_analysis(connection_id, days=30)
        cod_90 = await self.get_cost_of_delay_analysis(connection_id, days=90)
        roi = await self.get_team_roi_analysis(connection_id, days=90)
        opportunity = await self.get_opportunity_cost_analysis(connection_id, days=90)
        bottlenecks = await self.get_bottleneck_impact_score(connection_id, days=30)
        
        return {
            "cost_of_delay_30d": {
                "total": cod_30["total_cost_of_delay"],
                "daily_burn": cod_30["daily_burn_rate"],
                "top_insights": cod_30["insights"]
            },
            "cost_of_delay_90d": {
                "total": cod_90["total_cost_of_delay"],
                "daily_burn": cod_90["daily_burn_rate"]
            },
            "team_roi": roi["team_roi"],
            "opportunity_cost": {
                "total": opportunity["opportunity_cost"],
                "utilization_rate": opportunity["utilization_rate"]
            },
            "top_bottlenecks": bottlenecks["ranked_bottlenecks"][:3],
            "quick_wins": bottlenecks["quick_wins"],
            "total_recoverable_value": bottlenecks["total_bottleneck_cost"]
        }
