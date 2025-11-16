"""
CRITICAL TEST: OAuth → Onboarding → Sync Flow
Tests the complete chain from OAuth callback to sync execution
"""
import asyncio
import httpx
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import sys

# Load environment variables
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / '.env')

# Configuration
BACKEND_URL = "https://prod-analytics-4.preview.emergentagent.com"
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

class OAuthSyncFlowTester:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.tests_passed = 0
        self.tests_failed = 0
        self.critical_issues = []
        
    async def close(self):
        await self.http_client.aclose()
        self.client.close()
    
    def log_pass(self, test_name):
        print(f"✅ PASS: {test_name}")
        self.tests_passed += 1
    
    def log_fail(self, test_name, reason, is_critical=False):
        print(f"❌ FAIL: {test_name}")
        print(f"   Reason: {reason}")
        self.tests_failed += 1
        if is_critical:
            self.critical_issues.append(f"{test_name}: {reason}")
    
    def log_info(self, message):
        print(f"ℹ️  {message}")
    
    async def test_database_state(self):
        """TEST 1: Check database for orphaned connections (connections without sync jobs)"""
        print("\n" + "="*80)
        print("TEST 1: Database State - Connections vs Sync Jobs")
        print("="*80)
        
        try:
            # Get all connections
            connections = await self.db.jira_connections.find({}, {"_id": 0, "id": 1, "user_id": 1, "created_at": 1}).to_list(None)
            total_connections = len(connections)
            
            self.log_info(f"Found {total_connections} total connections in database")
            
            if total_connections == 0:
                self.log_fail("Database State", "No connections found in database", is_critical=True)
                return
            
            # Check each connection for sync jobs
            orphaned_connections = []
            connections_with_jobs = []
            
            for conn in connections:
                conn_id = conn['id']
                sync_jobs = await self.db.jira_sync_jobs.find({"connection_id": conn_id}, {"_id": 0}).to_list(None)
                
                if len(sync_jobs) == 0:
                    orphaned_connections.append(conn)
                    self.log_info(f"  ❌ Connection {conn_id} (user: {conn.get('user_id', 'N/A')}) - NO SYNC JOBS")
                else:
                    connections_with_jobs.append(conn)
                    self.log_info(f"  ✅ Connection {conn_id} (user: {conn.get('user_id', 'N/A')}) - {len(sync_jobs)} sync jobs")
            
            print(f"\n📊 Summary:")
            print(f"   Total connections: {total_connections}")
            print(f"   Connections with sync jobs: {len(connections_with_jobs)}")
            print(f"   Orphaned connections (NO SYNC JOBS): {len(orphaned_connections)}")
            
            if len(orphaned_connections) > 0:
                self.log_fail(
                    "Database State", 
                    f"{len(orphaned_connections)} connections have ZERO sync jobs - OnboardingFlow is NOT triggering sync!",
                    is_critical=True
                )
                
                # Show details of orphaned connections
                print("\n🔍 Orphaned Connections Details:")
                for conn in orphaned_connections[:3]:  # Show first 3
                    print(f"   - ID: {conn['id']}")
                    print(f"     User: {conn.get('user_id', 'N/A')}")
                    print(f"     Created: {conn.get('created_at', 'N/A')}")
                
                return orphaned_connections
            else:
                self.log_pass("Database State - All connections have sync jobs")
                return []
                
        except Exception as e:
            self.log_fail("Database State", f"Error checking database: {str(e)}", is_critical=True)
            return []
    
    async def test_sync_start_endpoint(self, connection_id=None):
        """TEST 2: Test /api/sync/start endpoint directly"""
        print("\n" + "="*80)
        print("TEST 2: Sync Start Endpoint")
        print("="*80)
        
        try:
            # If no connection_id provided, get the first one
            if not connection_id:
                conn = await self.db.jira_connections.find_one({}, {"_id": 0, "id": 1, "user_id": 1})
                if not conn:
                    self.log_fail("Sync Start Endpoint", "No connections found to test", is_critical=True)
                    return None
                connection_id = conn['id']
                user_id = conn.get('user_id')
            else:
                conn = await self.db.jira_connections.find_one({"id": connection_id}, {"_id": 0, "user_id": 1})
                user_id = conn.get('user_id') if conn else None
            
            self.log_info(f"Testing sync start for connection: {connection_id}")
            
            # Get or create a test user token
            headers = {}
            if user_id:
                # Try to get user and create token
                user_doc = await self.db.users.find_one({"id": user_id})
                if user_doc:
                    # Create a test token (we'll use the auth module)
                    from auth import create_access_token
                    token = create_access_token(data={"sub": user_id})
                    headers['Authorization'] = f'Bearer {token}'
                    self.log_info(f"Using auth token for user: {user_id}")
            
            # Call /api/sync/start
            url = f"{BACKEND_URL}/api/sync/start?connection_id={connection_id}"
            self.log_info(f"POST {url}")
            
            response = await self.http_client.post(url, headers=headers)
            
            if response.status_code == 200:
                job = response.json()
                job_id = job.get('id')
                self.log_pass(f"Sync Start Endpoint - Created job {job_id}")
                return job_id
            elif response.status_code == 409:
                self.log_info("Sync already running for this connection")
                return None
            elif response.status_code == 404:
                self.log_fail("Sync Start Endpoint", f"Connection {connection_id} not found", is_critical=True)
                return None
            else:
                self.log_fail(
                    "Sync Start Endpoint", 
                    f"HTTP {response.status_code}: {response.text}",
                    is_critical=True
                )
                return None
                
        except Exception as e:
            self.log_fail("Sync Start Endpoint", f"Error: {str(e)}", is_critical=True)
            return None
    
    async def test_sync_job_execution(self, job_id):
        """TEST 3: Monitor sync job execution"""
        print("\n" + "="*80)
        print("TEST 3: Sync Job Execution")
        print("="*80)
        
        if not job_id:
            self.log_fail("Sync Job Execution", "No job_id provided", is_critical=False)
            return
        
        try:
            self.log_info(f"Monitoring job: {job_id}")
            
            max_attempts = 30  # 60 seconds max
            for attempt in range(max_attempts):
                # Check job status in database
                job = await self.db.jira_sync_jobs.find_one({"id": job_id}, {"_id": 0})
                
                if not job:
                    self.log_fail("Sync Job Execution", f"Job {job_id} not found in database", is_critical=True)
                    return
                
                status = job.get('status')
                stats = job.get('stats', {})
                
                self.log_info(f"  Attempt {attempt + 1}: Status={status}, Stats={stats}")
                
                if status == 'success':
                    projects = stats.get('projects', 0)
                    issues = stats.get('issues', 0)
                    
                    if projects > 0 or issues > 0:
                        self.log_pass(f"Sync Job Execution - Completed with {projects} projects, {issues} issues")
                        return
                    else:
                        self.log_fail(
                            "Sync Job Execution", 
                            "Job completed but NO DATA synced (0 projects, 0 issues)",
                            is_critical=True
                        )
                        return
                
                elif status == 'error':
                    error = job.get('error', 'Unknown error')
                    self.log_fail("Sync Job Execution", f"Job failed: {error}", is_critical=True)
                    return
                
                elif status in ['queued', 'running']:
                    await asyncio.sleep(2)
                    continue
                
                else:
                    self.log_fail("Sync Job Execution", f"Unknown status: {status}", is_critical=True)
                    return
            
            # Timeout
            self.log_fail("Sync Job Execution", "Job did not complete within 60 seconds", is_critical=True)
            
        except Exception as e:
            self.log_fail("Sync Job Execution", f"Error: {str(e)}", is_critical=True)
    
    async def test_onboarding_flow_simulation(self):
        """TEST 4: Simulate OnboardingFlow behavior"""
        print("\n" + "="*80)
        print("TEST 4: OnboardingFlow Simulation")
        print("="*80)
        
        try:
            # Get a connection without sync jobs (orphaned)
            connections = await self.db.jira_connections.find({}, {"_id": 0, "id": 1}).to_list(None)
            
            orphaned_conn = None
            for conn in connections:
                sync_jobs = await self.db.jira_sync_jobs.find({"connection_id": conn['id']}).to_list(None)
                if len(sync_jobs) == 0:
                    orphaned_conn = conn
                    break
            
            if not orphaned_conn:
                self.log_info("No orphaned connections found - creating test scenario")
                # All connections have jobs, which is good
                self.log_pass("OnboardingFlow Simulation - No orphaned connections to fix")
                return
            
            connection_id = orphaned_conn['id']
            self.log_info(f"Found orphaned connection: {connection_id}")
            self.log_info("Simulating OnboardingFlow.startSync() call...")
            
            # This simulates what OnboardingFlow.jsx does in useEffect
            job_id = await self.test_sync_start_endpoint(connection_id)
            
            if job_id:
                self.log_pass("OnboardingFlow Simulation - Successfully triggered sync")
                await self.test_sync_job_execution(job_id)
            else:
                self.log_fail(
                    "OnboardingFlow Simulation", 
                    "Failed to trigger sync - this is why users see 'nothing happens'",
                    is_critical=True
                )
        
        except Exception as e:
            self.log_fail("OnboardingFlow Simulation", f"Error: {str(e)}", is_critical=True)
    
    async def test_oauth_callback_redirect(self):
        """TEST 5: Verify OAuth callback redirect includes all required params"""
        print("\n" + "="*80)
        print("TEST 5: OAuth Callback Redirect Parameters")
        print("="*80)
        
        try:
            # Check if FRONTEND_URL is set correctly
            frontend_url = os.environ.get('FRONTEND_URL', 'https://prod-analytics-4.preview.emergentagent.com')
            self.log_info(f"FRONTEND_URL: {frontend_url}")
            
            # Get a recent connection to check if it was created via OAuth
            recent_conn = await self.db.jira_connections.find_one(
                {},
                {"_id": 0, "id": 1, "cloud_id": 1, "user_id": 1, "created_at": 1},
                sort=[("created_at", -1)]
            )
            
            if not recent_conn:
                self.log_fail("OAuth Callback Redirect", "No connections found", is_critical=False)
                return
            
            self.log_info(f"Recent connection: {recent_conn['id']}")
            self.log_info(f"  Cloud ID: {recent_conn.get('cloud_id', 'N/A')}")
            self.log_info(f"  User ID: {recent_conn.get('user_id', 'N/A')}")
            
            # Check if user_id is set (required for auth)
            if not recent_conn.get('user_id'):
                self.log_fail(
                    "OAuth Callback Redirect",
                    "Connection has no user_id - OAuth callback not linking to user properly",
                    is_critical=True
                )
            else:
                self.log_pass("OAuth Callback Redirect - Connection has user_id")
            
            # Verify the redirect URL would have all params
            expected_params = ['connection_id', 'cloud_id', 'oauth_success', 'token']
            self.log_info(f"Expected redirect params: {', '.join(expected_params)}")
            
            # Check if connection has all required fields
            has_cloud_id = bool(recent_conn.get('cloud_id'))
            has_user_id = bool(recent_conn.get('user_id'))
            
            if has_cloud_id and has_user_id:
                self.log_pass("OAuth Callback Redirect - All required fields present")
            else:
                missing = []
                if not has_cloud_id:
                    missing.append('cloud_id')
                if not has_user_id:
                    missing.append('user_id')
                self.log_fail(
                    "OAuth Callback Redirect",
                    f"Missing fields: {', '.join(missing)}",
                    is_critical=True
                )
        
        except Exception as e:
            self.log_fail("OAuth Callback Redirect", f"Error: {str(e)}", is_critical=False)
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n" + "="*80)
        print("🔍 CRITICAL OAUTH → ONBOARDING → SYNC FLOW TEST")
        print("="*80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"MongoDB: {MONGO_URL}")
        print(f"Database: {DB_NAME}")
        print(f"Started: {datetime.now(timezone.utc).isoformat()}")
        
        try:
            # TEST 1: Check database state
            orphaned_connections = await self.test_database_state()
            
            # TEST 5: Check OAuth callback redirect
            await self.test_oauth_callback_redirect()
            
            # TEST 4: Simulate OnboardingFlow
            await self.test_onboarding_flow_simulation()
            
            # Print summary
            print("\n" + "="*80)
            print("📊 TEST SUMMARY")
            print("="*80)
            print(f"✅ Tests Passed: {self.tests_passed}")
            print(f"❌ Tests Failed: {self.tests_failed}")
            
            if self.critical_issues:
                print(f"\n🚨 CRITICAL ISSUES ({len(self.critical_issues)}):")
                for i, issue in enumerate(self.critical_issues, 1):
                    print(f"   {i}. {issue}")
            
            print("\n" + "="*80)
            
            # Return exit code
            return 0 if len(self.critical_issues) == 0 else 1
            
        except Exception as e:
            print(f"\n❌ FATAL ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            await self.close()


async def main():
    tester = OAuthSyncFlowTester()
    exit_code = await tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
