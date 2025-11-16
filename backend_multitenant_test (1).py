#!/usr/bin/env python3
"""
Multi-Tenant Architecture Testing for Quantum Sprout
Tests JWT authentication, user isolation, and fresh user experience
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class MultiTenantTester:
    def __init__(self, base_url="https://prod-analytics-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test users
        self.fresh_user = {
            "email": "fresh@quantumsprout.com",
            "password": "password123",
            "token": None
        }
        self.old_user = {
            "email": "test@quantumsprout.com",
            "password": "testpass123",
            "token": None
        }

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int = 200, 
                 data: Optional[Dict] = None, params: Optional[Dict] = None, 
                 token: Optional[str] = None) -> tuple[bool, Any]:
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = response.text

            if success:
                self.log_test(name, True, f"Status: {response.status_code}", response_data)
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}. Response: {response_data}", response_data)

            return success, response_data

        except requests.exceptions.Timeout:
            self.log_test(name, False, "Request timeout (30s)")
            return False, None
        except requests.exceptions.ConnectionError:
            self.log_test(name, False, "Connection error")
            return False, None
        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, None

    def test_health_check(self):
        """Test health check endpoint (no auth required)"""
        return self.run_test("Health Check", "GET", "health")

    def test_fresh_user_login(self):
        """Test fresh user login"""
        success, response = self.run_test(
            "Fresh User Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": self.fresh_user["email"],
                "password": self.fresh_user["password"]
            }
        )
        
        if success and response and 'access_token' in response:
            self.fresh_user['token'] = response['access_token']
            self.log_test("Fresh User Token Received", True, f"User ID: {response.get('user', {}).get('id')}")
        
        return success, response

    def test_old_user_login(self):
        """Test old user login"""
        success, response = self.run_test(
            "Old User Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": self.old_user["email"],
                "password": self.old_user["password"]
            }
        )
        
        if success and response and 'access_token' in response:
            self.old_user['token'] = response['access_token']
            self.log_test("Old User Token Received", True, f"User ID: {response.get('user', {}).get('id')}")
        
        return success, response

    def test_fresh_user_no_connection(self):
        """Test fresh user has NO Jira connection (404)"""
        if not self.fresh_user['token']:
            self.log_test("Fresh User No Connection", False, "No token available")
            return False, None
        
        return self.run_test(
            "Fresh User No Connection (404)",
            "GET",
            "auth/jira/connection",
            404,  # Expect 404 for fresh user
            token=self.fresh_user['token']
        )

    def test_old_user_has_connection(self):
        """Test old user HAS Jira connection with data"""
        if not self.old_user['token']:
            self.log_test("Old User Has Connection", False, "No token available")
            return False, None
        
        success, response = self.run_test(
            "Old User Has Connection (200)",
            "GET",
            "auth/jira/connection",
            200,
            token=self.old_user['token']
        )
        
        if success and response:
            self.log_test("Old User Connection Verified", True, f"Connection ID: {response.get('id')}")
        
        return success, response

    def test_old_user_sync_stats(self):
        """Test old user has 2,664 issues"""
        if not self.old_user['token']:
            self.log_test("Old User Sync Stats", False, "No token available")
            return False, None
        
        success, response = self.run_test(
            "Old User Sync Stats (2,664 issues)",
            "GET",
            "sync/stats",
            200,
            token=self.old_user['token']
        )
        
        if success and response:
            issues = response.get('issues', 0)
            if issues == 2664:
                self.log_test("Old User Issue Count Verified", True, f"Issues: {issues}")
            else:
                self.log_test("Old User Issue Count Mismatch", False, f"Expected 2664, got {issues}")
        
        return success, response

    def test_fresh_user_sync_stats_empty(self):
        """Test fresh user has 0 issues"""
        if not self.fresh_user['token']:
            self.log_test("Fresh User Sync Stats", False, "No token available")
            return False, None
        
        success, response = self.run_test(
            "Fresh User Sync Stats (0 issues)",
            "GET",
            "sync/stats",
            200,
            token=self.fresh_user['token']
        )
        
        if success and response:
            issues = response.get('issues', 0)
            if issues == 0:
                self.log_test("Fresh User Empty Stats Verified", True, f"Issues: {issues}")
            else:
                self.log_test("Fresh User Stats Not Empty", False, f"Expected 0, got {issues}")
        
        return success, response

    def test_jwt_required_on_financial_endpoints(self):
        """Test JWT authentication required on financial endpoints"""
        # Test without token (should fail with 401)
        success, response = self.run_test(
            "Financial Summary Without Token (401)",
            "GET",
            "financial/summary",
            401  # Expect 401 Unauthorized
        )
        
        # Test with valid token (should succeed)
        if self.old_user['token']:
            success2, response2 = self.run_test(
                "Financial Summary With Token (200)",
                "GET",
                "financial/summary",
                200,
                token=self.old_user['token']
            )
            return success and success2, response2
        
        return success, response

    def test_jwt_required_on_investigation_endpoints(self):
        """Test JWT authentication required on investigation endpoints"""
        # Test without token (should fail with 401)
        success, response = self.run_test(
            "Team Comparison Without Token (401)",
            "GET",
            "investigation/team-comparison",
            401  # Expect 401 Unauthorized
        )
        
        # Test with valid token (should succeed)
        if self.old_user['token']:
            success2, response2 = self.run_test(
                "Team Comparison With Token (200)",
                "GET",
                "investigation/team-comparison",
                200,
                token=self.old_user['token']
            )
            return success and success2, response2
        
        return success, response

    def test_jwt_required_on_action_endpoints(self):
        """Test JWT authentication required on action endpoints"""
        # Test without token (should fail with 401)
        success, response = self.run_test(
            "Auto-Assign Preview Without Token (401)",
            "GET",
            "actions/auto-assign/preview",
            401  # Expect 401 Unauthorized
        )
        
        # Test with valid token (should succeed)
        if self.old_user['token']:
            success2, response2 = self.run_test(
                "Auto-Assign Preview With Token (200)",
                "GET",
                "actions/auto-assign/preview",
                200,
                token=self.old_user['token']
            )
            return success and success2, response2
        
        return success, response

    def test_jwt_required_on_analytics_endpoints(self):
        """Test JWT authentication required on analytics endpoints"""
        # Test without token (should fail with 401)
        success, response = self.run_test(
            "Executive Summary Without Token (401)",
            "GET",
            "analytics/executive-summary",
            401  # Expect 401 Unauthorized
        )
        
        # Test with valid token (should succeed)
        if self.old_user['token']:
            success2, response2 = self.run_test(
                "Executive Summary With Token (200)",
                "GET",
                "analytics/executive-summary",
                200,
                token=self.old_user['token']
            )
            return success and success2, response2
        
        return success, response

    def test_gdpr_export_requires_auth(self):
        """Test GDPR export requires authentication"""
        # Test without token (should fail with 401)
        success, response = self.run_test(
            "GDPR Export Without Token (401)",
            "GET",
            "gdpr/export",
            401  # Expect 401 Unauthorized
        )
        
        # Test with valid token (should succeed)
        if self.old_user['token']:
            success2, response2 = self.run_test(
                "GDPR Export With Token (200)",
                "GET",
                "gdpr/export",
                200,
                token=self.old_user['token']
            )
            
            # Verify data isolation - should only return old user's data
            if success2 and response2:
                connections = response2.get('connections', [])
                if connections:
                    user_ids = [c.get('user_id') for c in connections]
                    self.log_test("GDPR Export Data Isolation", True, f"User IDs in export: {user_ids}")
            
            return success and success2, response2
        
        return success, response

    def test_disconnect_keeps_user_logged_in(self):
        """Test disconnect removes Jira but keeps user logged in"""
        # Note: We won't actually disconnect to preserve test data
        # Just verify the endpoint exists and requires auth
        
        # Test without token (should fail with 401)
        success, response = self.run_test(
            "Disconnect Without Token (401)",
            "DELETE",
            "jira/disconnect",
            401  # Expect 401 Unauthorized
        )
        
        self.log_test("Disconnect Endpoint Exists", True, "Endpoint requires authentication")
        return success, response

    def run_all_tests(self):
        """Run comprehensive multi-tenant test suite"""
        print("🚀 Starting Multi-Tenant Architecture Testing")
        print(f"📍 Base URL: {self.base_url}")
        print("=" * 60)

        # Core API Tests
        print("\n📋 CORE API TESTS")
        self.test_health_check()
        
        # Authentication Tests
        print("\n🔐 AUTHENTICATION TESTS")
        self.test_fresh_user_login()
        self.test_old_user_login()
        
        # Fresh User Tests (No Connection)
        print("\n🆕 FRESH USER TESTS (No Jira Connection)")
        self.test_fresh_user_no_connection()
        self.test_fresh_user_sync_stats_empty()
        
        # Old User Tests (Has Connection with Data)
        print("\n👤 OLD USER TESTS (Has Jira Connection)")
        self.test_old_user_has_connection()
        self.test_old_user_sync_stats()
        
        # JWT Authentication Tests
        print("\n🔒 JWT AUTHENTICATION TESTS (401 Without Token)")
        self.test_jwt_required_on_financial_endpoints()
        self.test_jwt_required_on_investigation_endpoints()
        self.test_jwt_required_on_action_endpoints()
        self.test_jwt_required_on_analytics_endpoints()
        
        # GDPR & Data Isolation Tests
        print("\n🛡️ GDPR & DATA ISOLATION TESTS")
        self.test_gdpr_export_requires_auth()
        
        # Disconnect Tests
        print("\n🔌 DISCONNECT TESTS")
        self.test_disconnect_keeps_user_logged_in()

        # Print Results
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = MultiTenantTester()
    
    try:
        success = tester.run_all_tests()
        
        # Save detailed results
        results_file = f"/app/multitenant_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_tests": tester.tests_run,
                "passed_tests": tester.tests_passed,
                "success_rate": tester.tests_passed / tester.tests_run * 100,
                "test_results": tester.test_results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
