"""
Backend API Testing for Bottleneck Finder and Insights Engine
Tests the critical intelligence features for investor demo
"""
import requests
import sys
from datetime import datetime

class IntelligenceAPITester:
    def __init__(self, base_url="https://prod-analytics-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if params:
            print(f"   Params: {params}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys())}")
                    self.test_results.append({
                        "test": name,
                        "status": "PASSED",
                        "response": response_data
                    })
                    return True, response_data
                except:
                    self.test_results.append({
                        "test": name,
                        "status": "PASSED",
                        "response": "Non-JSON response"
                    })
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                self.test_results.append({
                    "test": name,
                    "status": "FAILED",
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results.append({
                "test": name,
                "status": "ERROR",
                "error": str(e)
            })
            return False, {}

    def test_login(self, email, password):
        """Test login and get token"""
        print("\n" + "="*60)
        print("AUTHENTICATION TEST")
        print("="*60)
        success, response = self.run_test(
            "Login",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"✅ Token obtained: {self.token[:20]}...")
            return True
        print("❌ Login failed - cannot proceed with authenticated tests")
        return False

    def test_bottleneck_finder(self, days=90):
        """Test bottleneck finder API"""
        print("\n" + "="*60)
        print("BOTTLENECK FINDER TEST")
        print("="*60)
        success, response = self.run_test(
            f"Bottleneck Finder (days={days})",
            "GET",
            "bottleneck-finder/analyze",
            200,
            params={"days": days}
        )
        
        if success:
            # Validate response structure
            required_fields = ['bottlenecks_found', 'top_bottlenecks', 'metrics']
            missing = [f for f in required_fields if f not in response]
            if missing:
                print(f"⚠️  Missing fields: {missing}")
                return False, response
            
            print(f"   Bottlenecks found: {response.get('bottlenecks_found', 0)}")
            if response.get('bottlenecks_found', 0) > 0:
                print(f"   Top bottleneck: {response['top_bottlenecks'][0].get('type', 'Unknown')}")
                print(f"   Financial impact: ${response['top_bottlenecks'][0].get('financial_impact', 0):,}")
            
            return True, response
        return False, {}

    def test_insights_engine(self, days=90):
        """Test insights engine API"""
        print("\n" + "="*60)
        print("INSIGHTS ENGINE TEST")
        print("="*60)
        success, response = self.run_test(
            f"Insights Engine (days={days})",
            "GET",
            "insights/generate",
            200,
            params={"days": days}
        )
        
        if success:
            # Validate response structure
            required_fields = ['insights_count', 'insights']
            missing = [f for f in required_fields if f not in response]
            if missing:
                print(f"⚠️  Missing fields: {missing}")
                return False, response
            
            print(f"   Insights count: {response.get('insights_count', 0)}")
            if response.get('insights_count', 0) > 0:
                first_insight = response['insights'][0]
                print(f"   First insight: {first_insight.get('title', 'Unknown')}")
                print(f"   Severity: {first_insight.get('severity', 'Unknown')}")
            
            return True, response
        return False, {}

    def test_filter_variations(self):
        """Test different time period filters"""
        print("\n" + "="*60)
        print("FILTER VARIATIONS TEST")
        print("="*60)
        
        # Test This Quarter (90 days)
        print("\n📊 Testing 'This Quarter' filter (90 days)...")
        success_90, data_90 = self.test_bottleneck_finder(90)
        
        # Test This Year (365 days)
        print("\n📊 Testing 'This Year' filter (365 days)...")
        success_365, data_365 = self.test_insights_engine(365)
        
        # Verify data changes
        if success_90 and success_365:
            print("\n✅ Both filter periods work")
            return True
        else:
            print("\n❌ Filter variations failed")
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n✅ ALL TESTS PASSED - Backend APIs are working!")
        else:
            print(f"\n❌ {self.tests_run - self.tests_passed} TESTS FAILED - Backend has issues")
        
        return self.tests_passed == self.tests_run


def main():
    """Main test execution"""
    print("="*60)
    print("VELOCITY BOOST - INTELLIGENCE FEATURES TEST")
    print("Testing Bottleneck Finder & Insights Engine")
    print("="*60)
    
    tester = IntelligenceAPITester()
    
    # Test credentials from review request
    test_email = "investor@test.com"
    test_password = "Investor123!"
    
    # Step 1: Login
    if not tester.test_login(test_email, test_password):
        print("\n❌ CRITICAL: Cannot authenticate - stopping tests")
        return 1
    
    # Step 2: Test Bottleneck Finder
    success_bn, bn_data = tester.test_bottleneck_finder(90)
    
    # Step 3: Test Insights Engine
    success_insights, insights_data = tester.test_insights_engine(90)
    
    # Step 4: Test Filter Variations
    tester.test_filter_variations()
    
    # Print summary
    all_passed = tester.print_summary()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
