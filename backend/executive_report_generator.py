"""
Executive Report Generator
Creates CEO-ready report with graphs and simple explanations
"""
from datetime import datetime, timezone
from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class ExecutiveReportGenerator:
    """
    Generates executive summary report.
    Explains everything like you're a child.
    Includes graphs, key findings, recommendations.
    """
    
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        bottleneck_finder,
        insights_engine,
        people_analyzer,
        financial_analytics
    ):
        self.db = db
        self.bottleneck_finder = bottleneck_finder
        self.insights_engine = insights_engine
        self.people_analyzer = people_analyzer
        self.financial = financial_analytics
    
    async def generate_executive_report(
        self,
        connection_id: str,
        period_days: int = 90
    ) -> Dict[str, Any]:
        """
        Generate complete executive report.
        Returns structured data for CEO deck.
        """
        # Gather all data
        bottlenecks = await self.bottleneck_finder.find_bottlenecks(connection_id, days=period_days)
        insights = await self.insights_engine.generate_insights(connection_id, current_period_days=period_days)
        people = await self.people_analyzer.analyze_people_bottlenecks(connection_id, days=period_days)
        financial = await self.financial.get_financial_summary(connection_id)
        
        # Get basic stats
        stats = await self._get_basic_stats(connection_id)
        
        # Generate report
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": self._period_label(period_days),
            "period_days": period_days,
            
            # Executive Summary (ELI5)
            "executive_summary": {
                "headline": self._generate_headline(bottlenecks, people, financial),
                "tldr": self._generate_tldr(bottlenecks, people, financial, stats),
                "key_numbers": {
                    "total_blocked_value": financial.get('cost_of_delay_30d', {}).get('total', 0),
                    "people_bottlenecks": people.get('total_people_bottlenecks', 0),
                    "process_bottlenecks": bottlenecks.get('bottlenecks_found', 0),
                    "recovery_potential": financial.get('total_recoverable_value', 0)
                }
            },
            
            # Key Findings
            "key_findings": [
                {
                    "title": "Your Biggest Problem",
                    "simple_explanation": self._explain_biggest_problem(bottlenecks, people),
                    "what_it_means": "This is costing you money every single day it's not fixed.",
                    "data": bottlenecks.get('top_bottlenecks', [])[0] if bottlenecks.get('top_bottlenecks') else None
                },
                {
                    "title": "Who's Overloaded",
                    "simple_explanation": self._explain_people_overload(people),
                    "what_it_means": "These people have too much work. They can't finish it all.",
                    "data": people.get('people_bottlenecks', [])[:3]
                },
                {
                    "title": "How Much It's Costing",
                    "simple_explanation": f"${financial.get('cost_of_delay_30d', {}).get('total', 0) / 1000000:.1f} million in the last month",
                    "what_it_means": "This is money you're losing because work isn't getting done fast enough.",
                    "data": financial.get('cost_of_delay_30d', {})
                }
            ],
            
            # Recommendations (Simple Actions)
            "recommendations": self._generate_simple_recommendations(bottlenecks, people, insights),
            
            # Data for Graphs
            "graph_data": {
                "bottleneck_flow": bottlenecks.get('top_bottlenecks', []),
                "people_burden": people.get('people_bottlenecks', []),
                "financial_breakdown": financial.get('breakdown', {}),
                "team_roi": financial.get('team_roi', {})
            },
            
            # Metadata
            "company_stats": stats
        }
        
        return report
    
    def _period_label(self, days: int) -> str:
        """Convert days to executive label"""
        if days <= 30:
            return "This Month"
        elif days <= 90:
            return "This Quarter"
        elif days <= 180:
            return "Last 6 Months"
        else:
            return "This Year"
    
    def _generate_headline(self, bottlenecks, people, financial) -> str:
        """Generate attention-grabbing headline"""
        total_blocked = financial.get('cost_of_delay_30d', {}).get('total', 0)
        return f"Your team has ${total_blocked / 1000000:.1f} million in hidden bottlenecks"
    
    def _generate_tldr(self, bottlenecks, people, financial, stats) -> str:
        """Generate 3-sentence summary"""
        num_people = people.get('total_people_bottlenecks', 0)
        num_process = bottlenecks.get('bottlenecks_found', 0)
        total_blocked = financial.get('cost_of_delay_30d', {}).get('total', 0)
        
        return f"We found {num_people} people and {num_process} process bottlenecks blocking ${total_blocked / 1000000:.1f}M in value. The biggest problem is work piling up faster than your team can finish it. Fix the top 3 issues and you'll recover ${financial.get('total_recoverable_value', 0) / 1000000:.1f}M."
    
    async def _get_basic_stats(self, connection_id: str) -> Dict:
        """Get basic company stats"""
        projects = await self.db.jira_projects.count_documents({"connection_id": connection_id})
        issues = await self.db.jira_issues.count_documents({"connection_id": connection_id})
        users = await self.db.jira_users.count_documents({"connection_id": connection_id})
        
        return {
            "projects": projects,
            "total_issues": issues,
            "team_size": users
        }
    
    def _explain_biggest_problem(self, bottlenecks, people) -> str:
        """Explain biggest bottleneck in simple terms"""
        if not bottlenecks.get('top_bottlenecks'):
            return "No major bottlenecks detected - your team is operating efficiently."
        
        top = bottlenecks['top_bottlenecks'][0]
        impact = top.get('financial_impact', 0)
        
        if 'Stale' in top.get('type', ''):
            return f"You have work that's been sitting untouched for weeks. It's costing ${impact / 1000000:.1f}M. Someone needs to either finish it or delete it."
        elif 'Handoff' in top.get('type', ''):
            return f"Work is getting stuck waiting for approvals or reviews. ${impact / 1000000:.1f}M worth of work is just waiting. Speed up your review process."
        elif 'Capacity' in top.get('type', ''):
            return f"Your team is starting too much work and not finishing enough. ${impact / 1000000:.1f}M is stuck in progress. Limit how much new work you start."
        else:
            return f"There's a ${impact / 1000000:.1f}M bottleneck in your workflow."
    
    def _explain_people_overload(self, people) -> str:
        """Explain people overload in simple terms"""
        if not people.get('people_bottlenecks'):
            return "Your team workload is balanced. No one is critically overloaded."
        
        top_person = people['people_bottlenecks'][0]
        name = top_person.get('person', 'Unknown')
        workload = top_person.get('workload', 0)
        optimal = top_person.get('optimal_workload', 5)
        
        return f"{name} has {workload} active tasks (should be around {optimal}). They're {int(workload/optimal)}x overloaded. They literally can't finish all this work."
    
    def _generate_simple_recommendations(self, bottlenecks, people, insights) -> List[Dict]:
        """Generate 1-2-3 action plan"""
        recs = []
        
        # Rec 1: Fix biggest bottleneck
        if bottlenecks.get('top_bottlenecks'):
            top = bottlenecks['top_bottlenecks'][0]
            recs.append({
                "priority": 1,
                "action": top.get('action', 'Fix bottleneck'),
                "why": f"This will recover ${top.get('financial_impact', 0) / 1000000:.1f}M immediately",
                "how": top.get('narrative', ''),
                "effort": "1 day",
                "impact": "High"
            })
        
        # Rec 2: Rebalance people
        if people.get('people_bottlenecks'):
            top_person = people['people_bottlenecks'][0]
            recs.append({
                "priority": 2,
                "action": f"Delegate work from {top_person.get('person', 'overloaded person')}",
                "why": f"They have {top_person.get('workload', 0)} tasks, blocking ${top_person.get('blocked_value', 0) / 1000000:.1f}M",
                "how": top_person.get('delegation_recommendation', 'Reassign excess work'),
                "effort": "1 day",
                "impact": "Medium"
            })
        
        # Rec 3: Process improvement (if insights suggest)
        if insights and len(insights) > 0:
            top_insight = insights[0]
            recs.append({
                "priority": 3,
                "action": "Improve process based on data",
                "why": top_insight.get('title', ''),
                "how": top_insight.get('recommendation', ''),
                "effort": "1 week",
                "impact": "Medium"
            })
        
        return recs[:3]  # Top 3
