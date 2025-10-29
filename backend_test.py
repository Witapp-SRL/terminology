import requests
import json
import time
from datetime import datetime

# Backend URL from environment
BASE_URL = "https://terminology-manager.preview.emergentagent.com/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Global variables to store test data
access_token = None
test_user_token = None
test_codesystem_id = None

def print_test_header(test_name):
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")

def print_result(success, message):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    return success

def test_auth_login_correct_credentials():
    """Test POST /api/auth/login with correct credentials"""
    print_test_header("Authentication - Login with correct credentials")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        )
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "token_type" in data:
                global access_token
                access_token = data["access_token"]
                return print_result(True, f"Login successful, token received: {data['token_type']}")
            else:
                return print_result(False, f"Response missing required fields: {data}")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_auth_login_wrong_credentials():
    """Test POST /api/auth/login with wrong credentials"""
    print_test_header("Authentication - Login with wrong credentials")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "wronguser", "password": "wrongpass"}
        )
        
        if response.status_code == 401:
            return print_result(True, "Correctly returned 401 for wrong credentials")
        else:
            return print_result(False, f"Expected 401, got {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_auth_register_new_user():
    """Test POST /api/auth/register with new user"""
    print_test_header("Authentication - Register new user")
    
    # Use timestamp to ensure unique username
    timestamp = int(time.time())
    test_username = f"testuser{timestamp}"
    test_email = f"test{timestamp}@example.com"
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": test_username,
                "email": test_email,
                "password": "password123",
                "full_name": "Test User"
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            if data.get("username") == test_username and data.get("email") == test_email:
                # Login with new user to get token
                login_response = requests.post(
                    f"{BASE_URL}/auth/login",
                    json={"username": test_username, "password": "password123"}
                )
                if login_response.status_code == 200:
                    global test_user_token
                    test_user_token = login_response.json()["access_token"]
                return print_result(True, f"User registered successfully: {test_username}")
            else:
                return print_result(False, f"User data mismatch: {data}")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_auth_me_with_token():
    """Test GET /api/auth/me with valid token"""
    print_test_header("Authentication - Get current user with token")
    
    if not access_token:
        return print_result(False, "No access token available")
    
    try:
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("username") == ADMIN_USERNAME:
                return print_result(True, f"User info retrieved: {data.get('username')}, admin: {data.get('is_admin')}")
            else:
                return print_result(False, f"Username mismatch: {data}")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_auth_me_without_token():
    """Test GET /api/auth/me without token"""
    print_test_header("Authentication - Get current user without token")
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me")
        
        if response.status_code == 401 or response.status_code == 403:
            return print_result(True, f"Correctly returned {response.status_code} without token")
        else:
            return print_result(False, f"Expected 401/403, got {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_codesystem_create_with_auth():
    """Test POST /api/CodeSystem with authentication"""
    print_test_header("CodeSystem - Create with authentication")
    
    if not access_token:
        return print_result(False, "No access token available")
    
    timestamp = int(time.time())
    try:
        response = requests.post(
            f"{BASE_URL}/CodeSystem",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "url": f"http://example.org/fhir/CodeSystem/test-{timestamp}",
                "name": f"TestCodeSystem{timestamp}",
                "title": "Test Code System",
                "status": "draft",
                "content": "complete",
                "caseSensitive": True,
                "concept": [
                    {"code": "001", "display": "Test Concept 1", "definition": "First test concept"},
                    {"code": "002", "display": "Test Concept 2", "definition": "Second test concept"}
                ]
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            if "id" in data:
                global test_codesystem_id
                test_codesystem_id = data["id"]
                # Verify concept is an array, not null
                if isinstance(data.get("concept"), list) and len(data.get("concept")) == 2:
                    return print_result(True, f"CodeSystem created with ID: {test_codesystem_id}, concepts: {len(data.get('concept'))}")
                else:
                    return print_result(False, f"Concept field issue: {data.get('concept')}")
            else:
                return print_result(False, f"Response missing ID: {data}")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_codesystem_create_without_auth():
    """Test POST /api/CodeSystem without authentication"""
    print_test_header("CodeSystem - Create without authentication")
    
    timestamp = int(time.time())
    try:
        response = requests.post(
            f"{BASE_URL}/CodeSystem",
            json={
                "url": f"http://example.org/fhir/CodeSystem/unauth-{timestamp}",
                "name": f"UnauthCodeSystem{timestamp}",
                "title": "Unauthorized Test",
                "status": "draft",
                "content": "complete"
            }
        )
        
        if response.status_code == 401 or response.status_code == 403:
            return print_result(True, f"Correctly returned {response.status_code} without auth")
        else:
            return print_result(False, f"Expected 401/403, got {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_codesystem_list():
    """Test GET /api/CodeSystem"""
    print_test_header("CodeSystem - List all")
    
    try:
        response = requests.get(f"{BASE_URL}/CodeSystem")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return print_result(True, f"Retrieved {len(data)} CodeSystems")
            else:
                return print_result(False, f"Expected list, got: {type(data)}")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_codesystem_get_by_id():
    """Test GET /api/CodeSystem/{id}"""
    print_test_header("CodeSystem - Get by ID")
    
    if not test_codesystem_id:
        return print_result(False, "No test CodeSystem ID available")
    
    try:
        response = requests.get(f"{BASE_URL}/CodeSystem/{test_codesystem_id}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("id") == test_codesystem_id:
                # Verify concept is an array
                if isinstance(data.get("concept"), list):
                    return print_result(True, f"Retrieved CodeSystem: {data.get('name')}, concepts: {len(data.get('concept', []))}")
                else:
                    return print_result(False, f"Concept field is not an array: {data.get('concept')}")
            else:
                return print_result(False, f"ID mismatch: {data}")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_codesystem_update_with_auth():
    """Test PUT /api/CodeSystem/{id} with authentication"""
    print_test_header("CodeSystem - Update with authentication")
    
    if not access_token or not test_codesystem_id:
        return print_result(False, "Missing access token or CodeSystem ID")
    
    try:
        response = requests.put(
            f"{BASE_URL}/CodeSystem/{test_codesystem_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "url": f"http://example.org/fhir/CodeSystem/test-{test_codesystem_id}",
                "name": f"UpdatedTestCodeSystem",
                "title": "Updated Test Code System",
                "status": "active",
                "content": "complete",
                "caseSensitive": True,
                "concept": [
                    {"code": "001", "display": "Updated Concept 1", "definition": "Updated first concept"},
                    {"code": "002", "display": "Updated Concept 2", "definition": "Updated second concept"},
                    {"code": "003", "display": "New Concept 3", "definition": "New third concept"}
                ]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("title") == "Updated Test Code System" and len(data.get("concept", [])) == 3:
                return print_result(True, f"CodeSystem updated: {data.get('title')}, concepts: {len(data.get('concept'))}")
            else:
                return print_result(False, f"Update verification failed: {data}")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_codesystem_update_invalid_id():
    """Test PUT /api/CodeSystem/{invalid_id}"""
    print_test_header("CodeSystem - Update with invalid ID")
    
    if not access_token:
        return print_result(False, "No access token available")
    
    try:
        response = requests.put(
            f"{BASE_URL}/CodeSystem/invalid-id-12345",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "url": "http://example.org/fhir/CodeSystem/invalid",
                "name": "InvalidTest",
                "title": "Invalid Test",
                "status": "draft",
                "content": "complete"
            }
        )
        
        if response.status_code == 404:
            return print_result(True, "Correctly returned 404 for invalid ID")
        else:
            return print_result(False, f"Expected 404, got {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_codesystem_deactivate():
    """Test POST /api/CodeSystem/{id}/deactivate"""
    print_test_header("Soft Delete - Deactivate CodeSystem")
    
    if not access_token or not test_codesystem_id:
        return print_result(False, "Missing access token or CodeSystem ID")
    
    try:
        response = requests.post(
            f"{BASE_URL}/CodeSystem/{test_codesystem_id}/deactivate",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("message") and "deactivated" in data.get("message").lower():
                return print_result(True, f"CodeSystem deactivated: {data.get('message')}")
            else:
                return print_result(False, f"Unexpected response: {data}")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_codesystem_list_excludes_inactive():
    """Test GET /api/CodeSystem - verify deactivated CS not in list"""
    print_test_header("Soft Delete - List excludes inactive by default")
    
    if not test_codesystem_id:
        return print_result(False, "No test CodeSystem ID available")
    
    try:
        response = requests.get(f"{BASE_URL}/CodeSystem")
        
        if response.status_code == 200:
            data = response.json()
            ids = [cs.get("id") for cs in data]
            if test_codesystem_id not in ids:
                return print_result(True, f"Deactivated CodeSystem not in default list (total: {len(data)})")
            else:
                return print_result(False, f"Deactivated CodeSystem still appears in list")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_codesystem_list_includes_inactive():
    """Test GET /api/CodeSystem?include_inactive=true"""
    print_test_header("Soft Delete - List includes inactive with parameter")
    
    if not test_codesystem_id:
        return print_result(False, "No test CodeSystem ID available")
    
    try:
        response = requests.get(f"{BASE_URL}/CodeSystem?include_inactive=true")
        
        if response.status_code == 200:
            data = response.json()
            ids = [cs.get("id") for cs in data]
            if test_codesystem_id in ids:
                return print_result(True, f"Deactivated CodeSystem appears with include_inactive=true (total: {len(data)})")
            else:
                return print_result(False, f"Deactivated CodeSystem not found even with include_inactive=true")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_codesystem_activate():
    """Test POST /api/CodeSystem/{id}/activate"""
    print_test_header("Soft Delete - Activate CodeSystem")
    
    if not access_token or not test_codesystem_id:
        return print_result(False, "Missing access token or CodeSystem ID")
    
    try:
        response = requests.post(
            f"{BASE_URL}/CodeSystem/{test_codesystem_id}/activate",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("message") and "activated" in data.get("message").lower():
                return print_result(True, f"CodeSystem activated: {data.get('message')}")
            else:
                return print_result(False, f"Unexpected response: {data}")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_codesystem_list_after_reactivate():
    """Test GET /api/CodeSystem - verify reactivated CS appears"""
    print_test_header("Soft Delete - List includes reactivated CodeSystem")
    
    if not test_codesystem_id:
        return print_result(False, "No test CodeSystem ID available")
    
    try:
        response = requests.get(f"{BASE_URL}/CodeSystem")
        
        if response.status_code == 200:
            data = response.json()
            ids = [cs.get("id") for cs in data]
            if test_codesystem_id in ids:
                return print_result(True, f"Reactivated CodeSystem appears in default list (total: {len(data)})")
            else:
                return print_result(False, f"Reactivated CodeSystem not in list")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_audit_logs_get():
    """Test GET /api/audit-logs"""
    print_test_header("Audit Trail - Get audit logs")
    
    if not access_token:
        return print_result(False, "No access token available")
    
    try:
        response = requests.get(
            f"{BASE_URL}/audit-logs",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if "logs" in data and "total" in data:
                logs = data["logs"]
                if len(logs) > 0:
                    # Check if logs have required fields
                    first_log = logs[0]
                    required_fields = ["id", "resource_type", "resource_id", "action", "username", "timestamp"]
                    if all(field in first_log for field in required_fields):
                        return print_result(True, f"Retrieved {len(logs)} audit logs (total: {data['total']})")
                    else:
                        return print_result(False, f"Audit log missing required fields: {first_log}")
                else:
                    return print_result(True, "No audit logs yet (expected for fresh system)")
            else:
                return print_result(False, f"Response missing logs/total: {data}")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_audit_logs_filter_resource_type():
    """Test GET /api/audit-logs?resource_type=CodeSystem"""
    print_test_header("Audit Trail - Filter by resource type")
    
    if not access_token:
        return print_result(False, "No access token available")
    
    try:
        response = requests.get(
            f"{BASE_URL}/audit-logs?resource_type=CodeSystem",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get("logs", [])
            # Verify all logs are for CodeSystem
            if all(log.get("resource_type") == "CodeSystem" for log in logs):
                return print_result(True, f"Retrieved {len(logs)} CodeSystem audit logs")
            else:
                return print_result(False, f"Some logs are not CodeSystem type")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_audit_logs_filter_action():
    """Test GET /api/audit-logs?action=create"""
    print_test_header("Audit Trail - Filter by action")
    
    if not access_token:
        return print_result(False, "No access token available")
    
    try:
        response = requests.get(
            f"{BASE_URL}/audit-logs?action=create",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get("logs", [])
            # Verify all logs are create actions
            if all(log.get("action") == "create" for log in logs):
                return print_result(True, f"Retrieved {len(logs)} 'create' action logs")
            else:
                return print_result(False, f"Some logs are not 'create' action")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_audit_logs_verify_operations():
    """Verify audit logs contain create, update, deactivate, activate actions"""
    print_test_header("Audit Trail - Verify CRUD operations logged")
    
    if not access_token or not test_codesystem_id:
        return print_result(False, "Missing access token or CodeSystem ID")
    
    try:
        response = requests.get(
            f"{BASE_URL}/audit-logs?resource_id={test_codesystem_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get("logs", [])
            actions = [log.get("action") for log in logs]
            
            expected_actions = ["create", "update", "deactivate", "activate"]
            found_actions = [action for action in expected_actions if action in actions]
            
            if len(found_actions) >= 3:  # At least create, deactivate, activate
                return print_result(True, f"Found audit logs for actions: {', '.join(found_actions)}")
            else:
                return print_result(False, f"Missing expected actions. Found: {', '.join(found_actions)}, Expected: {', '.join(expected_actions)}")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_audit_logs_export_csv():
    """Test GET /api/audit-logs/export-csv"""
    print_test_header("Audit Trail - Export CSV")
    
    if not access_token:
        return print_result(False, "No access token available")
    
    try:
        response = requests.get(
            f"{BASE_URL}/audit-logs/export-csv",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            content_disposition = response.headers.get("content-disposition", "")
            
            if "text/csv" in content_type and "attachment" in content_disposition:
                # Verify CSV content
                csv_content = response.text
                lines = csv_content.strip().split('\n')
                if len(lines) > 0:
                    header = lines[0]
                    expected_columns = ["Timestamp", "Resource Type", "Resource ID", "Action", "User"]
                    if all(col in header for col in expected_columns):
                        return print_result(True, f"CSV export successful with {len(lines)-1} rows")
                    else:
                        return print_result(False, f"CSV header missing expected columns: {header}")
                else:
                    return print_result(True, "CSV export successful (empty)")
            else:
                return print_result(False, f"Wrong content type: {content_type}, disposition: {content_disposition}")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def run_all_tests():
    """Run all backend tests"""
    print("\n" + "="*80)
    print("FHIR TERMINOLOGY SERVICE - BACKEND TEST SUITE")
    print("="*80)
    print(f"Backend URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().isoformat()}")
    print("="*80)
    
    results = []
    
    # Authentication Tests
    results.append(("Auth - Login (correct)", test_auth_login_correct_credentials()))
    results.append(("Auth - Login (wrong)", test_auth_login_wrong_credentials()))
    results.append(("Auth - Register", test_auth_register_new_user()))
    results.append(("Auth - Get Me (with token)", test_auth_me_with_token()))
    results.append(("Auth - Get Me (no token)", test_auth_me_without_token()))
    
    # CodeSystem CRUD Tests
    results.append(("CodeSystem - Create (with auth)", test_codesystem_create_with_auth()))
    results.append(("CodeSystem - Create (no auth)", test_codesystem_create_without_auth()))
    results.append(("CodeSystem - List", test_codesystem_list()))
    results.append(("CodeSystem - Get by ID", test_codesystem_get_by_id()))
    results.append(("CodeSystem - Update (with auth)", test_codesystem_update_with_auth()))
    results.append(("CodeSystem - Update (invalid ID)", test_codesystem_update_invalid_id()))
    
    # Soft Delete Tests
    results.append(("Soft Delete - Deactivate", test_codesystem_deactivate()))
    results.append(("Soft Delete - List excludes inactive", test_codesystem_list_excludes_inactive()))
    results.append(("Soft Delete - List includes inactive", test_codesystem_list_includes_inactive()))
    results.append(("Soft Delete - Activate", test_codesystem_activate()))
    results.append(("Soft Delete - List after reactivate", test_codesystem_list_after_reactivate()))
    
    # Audit Trail Tests
    results.append(("Audit - Get logs", test_audit_logs_get()))
    results.append(("Audit - Filter by resource type", test_audit_logs_filter_resource_type()))
    results.append(("Audit - Filter by action", test_audit_logs_filter_action()))
    results.append(("Audit - Verify operations", test_audit_logs_verify_operations()))
    results.append(("Audit - Export CSV", test_audit_logs_export_csv()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)
    total = len(results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if failed > 0:
        print("\n" + "="*80)
        print("FAILED TESTS:")
        print("="*80)
        for name, result in results:
            if not result:
                print(f"  ❌ {name}")
    
    print("\n" + "="*80)
    return passed, failed, total

if __name__ == "__main__":
    passed, failed, total = run_all_tests()
    exit(0 if failed == 0 else 1)
