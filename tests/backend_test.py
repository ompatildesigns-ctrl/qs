"""
Comprehensive Backend API Testing for Velocity Boost Dashboard
Tests all critical endpoints including intelligence engines
"""
import requests
import sys
from datetime import datetime

class VelocityBoostAPITester:
    def __init__(self, base_url="https://prod-analytics-4.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.connection_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "test": name,
                "error": str(e)
            })
            return False, {}

    def test_login(self, email, password):
        """Test login and get token"""
        success, response = self.run_test(
            "Login",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_get_connection(self):
        """Get Jira connection"""
        success, response = self.run_test(
            "Get Jira Connection",
            "GET",
            "auth/jira/connection",
            200
        )
        if success and 'id' in response:
            self.connection_id = response['id']
            print(f"   Connection ID: {self.connection_id}")
            return True
        return False

    def test_sync_stats(self):
        """Get sync statistics"""
        success, response = self.run_test(
            "Get Sync Stats",
            "GET",
            "sync/stats",
            200
        )
        if success:
            print(f"   Issues: {response.get('issues', 0)}, Projects: {response.get('projects', 0)}")
        return success

    def test_financial_summary(self):
        """Test financial summary endpoint"""
        success, response = self.run_test(
            "Financial Summary",
            "GET",
            "financial/summary",
            200
        )
        if success:
            print(f"   Recoverable Value: ${response.get('total_recoverable_value', 0):,.0f}")
        return success

    def test_cost_of_delay_with_filters(self):
        """Test Cost of Delay with different time periods"""
        print("\n📊 Testing Time Period Filters...")
        
        periods = [
            ("This Quarter (90 days)", 90),
            ("This Month (30 days)", 30),
            ("This Year (365 days)", 365)
        ]
        
        results = {}
        for period_name, days in periods:
            success, response = self.run_test(
                f"Cost of Delay - {period_name}",
                "GET",
                "financial/cost-of-delay",
                200,
                params={"days": days}
            )
            if success:
                total_cod = response.get('total_cost_of_delay', 0)
                issues = response.get('total_issues_analyzed', 0)
                results[period_name] = {"cod": total_cod, "issues": issues}
                print(f"   CoD: ${total_cod:,.0f}, Issues: {issues}")
        
        # Verify filters actually change data
        if len(results) >= 2:
            values = [r['cod'] for r in results.values()]
            if len(set(values)) > 1:
                print("✅ FILTERS WORKING: Different periods return different values")
                return True
            else:
                print("⚠️  WARNING: All periods return same value - filters may not be working")
                self.failed_tests.append({
                    "test": "Filter Verification",
                    "issue": "All time periods return identical values"
                })
                return False
        return False

    def test_bottleneck_finder(self):
        """Test Bottleneck Finder API (CRITICAL - NOT IN UI)"""
        print("\n🔍 Testing Bottleneck Finder (Intelligence Engine)...")
        success, response = self.run_test(
            "Bottleneck Finder Analysis",
            "GET",
            "bottleneck-finder/analyze",
            200,
            params={"days": 90}
        )
        if success:
            bottlenecks = response.get('top_bottlenecks', [])
            print(f"   Found {len(bottlenecks)} bottlenecks")
            for i, bn in enumerate(bottlenecks[:3], 1):
                print(f"   {i}. {bn.get('type', 'Unknown')}: ${bn.get('financial_impact', 0):,.0f} impact")
            
            if len(bottlenecks) == 0:
                print("   ⚠️  No bottlenecks detected (may be expected if data is clean)")
            return True
        return False

    def test_insights_engine(self):
        """Test Insights Engine API (CRITICAL - NOT IN UI)"""
        print("\n💡 Testing Insights Engine (Intelligence Engine)...")
        success, response = self.run_test(
            "Insights Generation",
            "GET",
            "insights/generate",
            200,
            params={"days": 90}
        )
        if success:
            insights = response.get('insights', [])
            count = response.get('insights_count', 0)
            print(f"   Generated {count} insights")
            for i, insight in enumerate(insights[:3], 1):
                print(f"   {i}. [{insight.get('severity', 'N/A')}] {insight.get('title', 'No title')}")
            
            if count == 0:
                print("   ⚠️  No insights generated (may indicate insufficient data)")
            return True
        return False

    def test_team_comparison(self):
        """Test team comparison endpoint"""
        success, response = self.run_test(
            "Team Comparison",
            "GET",
            "investigation/team-comparison",
            200,
            params={"days": 90}
        )
        if success:
            comparison = response.get('comparison', {})
            sundew = comparison.get('sundew', {})
            us = comparison.get('us', {})
            print(f"   Sundew: {sundew.get('completion_rate', 0)}% completion")
            print(f"   US Team: {us.get('completion_rate', 0)}% completion")
        return success

    def test_historical_trends(self):
        """Test historical trends endpoint"""
        success, response = self.run_test(
            "Historical Trends",
            "GET",
            "investigation/historical-trends",
            200,
            params={"months": 6}
        )
        if success:
            trends = response.get('monthly_trends', [])
            print(f"   Analyzed {len(trends)} months of data")
        return success

def main():
    print("=" * 80)
    print("VELOCITY BOOST DASHBOARD - COMPREHENSIVE BACKEND API TESTING")
    print("=" * 80)
    
    tester = VelocityBoostAPITester()
    
    # Test credentials
    test_email = "investor@test.com"
    test_password = "Investor123!"
    
    print(f"\n🔐 Authenticating as {test_email}...")
    if not tester.test_login(test_email, test_password):
        print("\n❌ CRITICAL: Login failed. Cannot proceed with testing.")
        print("   Please verify test account exists and credentials are correct.")
        return 1
    
    print("\n📡 Verifying Jira Connection...")
    if not tester.test_get_connection():
        print("\n❌ CRITICAL: No Jira connection found.")
        print("   User needs to connect Jira account first.")
        return 1
    
    print("\n📊 Testing Core Endpoints...")
    tester.test_sync_stats()
    tester.test_financial_summary()
    
    print("\n🎯 Testing Critical Features...")
    tester.test_cost_of_delay_with_filters()
    
    print("\n🚨 Testing Intelligence Engines (NOT IN UI - CRITICAL)...")
    tester.test_bottleneck_finder()
    tester.test_insights_engine()
    
    print("\n📈 Testing Investigation Endpoints...")
    tester.test_team_comparison()
    tester.test_historical_trends()
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.failed_tests:
        print("\n❌ FAILED TESTS:")
        for i, failure in enumerate(tester.failed_tests, 1):
            print(f"\n{i}. {failure.get('test', 'Unknown')}")
            if 'error' in failure:
                print(f"   Error: {failure['error']}")
            else:
                print(f"   Expected: {failure.get('expected')}, Got: {failure.get('actual')}")
                if 'response' in failure:
                    print(f"   Response: {failure['response']}")
    
    print("\n" + "=" * 80)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
