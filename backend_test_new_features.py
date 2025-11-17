import requests
import json
import time
from datetime import datetime

# Backend URL from environment
BASE_URL = "https://fhirterm.preview.emergentagent.com/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Global variables to store test data
access_token = None
codesystem_urls = []

def print_test_header(test_name):
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")

def print_result(success, message):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    return success

def test_login_fix():
    """CRITICAL PRIORITY - Test POST /api/auth/login with admin credentials"""
    print_test_header("CRITICAL - Login Fix Test")
    
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
                
                # Verify token is valid JWT format (basic check)
                token_parts = access_token.split('.')
                if len(token_parts) == 3:
                    return print_result(True, f"Login successful, valid JWT token received: {data['token_type']}")
                else:
                    return print_result(False, f"Token format invalid: {len(token_parts)} parts instead of 3")
            else:
                return print_result(False, f"Response missing required fields: {data}")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_audit_logs_with_token():
    """CRITICAL PRIORITY - Test GET /api/audit-logs with token (should work without 403)"""
    print_test_header("CRITICAL - Audit Logs Access Test")
    
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
                return print_result(True, f"Audit logs accessible - no 403 error. Found {data['total']} logs")
            else:
                return print_result(False, f"Response format incorrect: {data}")
        elif response.status_code == 403:
            return print_result(False, "Still getting 403 Forbidden - login fix not working")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def get_existing_codesystems():
    """Helper function to get existing CodeSystem URLs for compose operation"""
    try:
        response = requests.get(f"{BASE_URL}/CodeSystem")
        if response.status_code == 200:
            data = response.json()
            global codesystem_urls
            codesystem_urls = [cs.get("url") for cs in data if cs.get("url")]
            print(f"Found {len(codesystem_urls)} existing CodeSystems")
            return True
        return False
    except Exception as e:
        print(f"Error getting CodeSystems: {e}")
        return False

def test_codesystem_find_matches():
    """HIGH PRIORITY - Test GET /api/CodeSystem/$find-matches"""
    print_test_header("HIGH PRIORITY - CodeSystem $find-matches Operation")
    
    try:
        response = requests.get(
            f"{BASE_URL}/CodeSystem/$find-matches?value=test&exact=false"
        )
        
        if response.status_code == 200:
            data = response.json()
            # Should return Parameters resource with matching codes
            if data.get("resourceType") == "Parameters":
                parameters = data.get("parameter", [])
                return print_result(True, f"$find-matches working - returned Parameters with {len(parameters)} parameters")
            else:
                return print_result(False, f"Expected Parameters resource, got: {data.get('resourceType')}")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_valueset_compose():
    """HIGH PRIORITY - Test POST /api/ValueSet/$compose"""
    print_test_header("HIGH PRIORITY - ValueSet $compose Operation")
    
    # First get existing CodeSystems
    if not get_existing_codesystems():
        return print_result(False, "Could not retrieve existing CodeSystems")
    
    if len(codesystem_urls) < 2:
        return print_result(False, f"Need at least 2 CodeSystems for compose test, found {len(codesystem_urls)}")
    
    try:
        # Use first two CodeSystem URLs
        url1 = codesystem_urls[0]
        url2 = codesystem_urls[1]
        
        response = requests.post(
            f"{BASE_URL}/ValueSet/$compose?include={url1}&include={url2}"
        )
        
        if response.status_code == 200:
            data = response.json()
            # Should return composed ValueSet with concepts from both systems
            if data.get("resourceType") == "ValueSet":
                compose = data.get("compose", {})
                include = compose.get("include", [])
                return print_result(True, f"$compose working - returned ValueSet with {len(include)} included systems")
            else:
                return print_result(False, f"Expected ValueSet resource, got: {data.get('resourceType')}")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_valueset_find_matches():
    """HIGH PRIORITY - Test GET /api/ValueSet/$find-matches"""
    print_test_header("HIGH PRIORITY - ValueSet $find-matches Operation")
    
    try:
        response = requests.get(
            f"{BASE_URL}/ValueSet/$find-matches?value=test&property=display"
        )
        
        if response.status_code == 200:
            data = response.json()
            # Should return Parameters resource with matching codes
            if data.get("resourceType") == "Parameters":
                parameters = data.get("parameter", [])
                return print_result(True, f"ValueSet $find-matches working - returned Parameters with {len(parameters)} parameters")
            else:
                return print_result(False, f"Expected Parameters resource, got: {data.get('resourceType')}")
        else:
            return print_result(False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_file_upload_size():
    """MEDIUM PRIORITY - Test file upload size handling (if possible)"""
    print_test_header("MEDIUM PRIORITY - File Upload Size Test")
    
    if not access_token:
        return print_result(False, "No access token available")
    
    try:
        # Create a small CSV content to test upload
        csv_content = "code,display,definition\n"
        csv_content += "TEST001,Test Code 1,Test definition 1\n"
        csv_content += "TEST002,Test Code 2,Test definition 2\n"
        
        # Test with small file first
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        
        response = requests.post(
            f"{BASE_URL}/CodeSystem/import-csv",
            files=files,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            return print_result(True, "Small CSV upload successful - no 413 error")
        elif response.status_code == 413:
            return print_result(False, "Still getting 413 error on small file upload")
        else:
            return print_result(True, f"Upload processed (status {response.status_code}) - no 413 error")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_additional_fhir_operations():
    """Test other FHIR operations to ensure they still work"""
    print_test_header("Additional FHIR Operations Verification")
    
    results = []
    
    # Test CodeSystem $lookup
    try:
        if codesystem_urls:
            response = requests.get(
                f"{BASE_URL}/CodeSystem/$lookup?system={codesystem_urls[0]}&code=001"
            )
            if response.status_code == 200:
                results.append("$lookup: ✅")
            else:
                results.append(f"$lookup: ❌ ({response.status_code})")
        else:
            results.append("$lookup: ⚠️ (no CodeSystems)")
    except Exception as e:
        results.append(f"$lookup: ❌ ({str(e)})")
    
    # Test CodeSystem $validate-code
    try:
        if codesystem_urls:
            response = requests.get(
                f"{BASE_URL}/CodeSystem/$validate-code?system={codesystem_urls[0]}&code=001"
            )
            if response.status_code == 200:
                results.append("$validate-code: ✅")
            else:
                results.append(f"$validate-code: ❌ ({response.status_code})")
        else:
            results.append("$validate-code: ⚠️ (no CodeSystems)")
    except Exception as e:
        results.append(f"$validate-code: ❌ ({str(e)})")
    
    # Test ValueSet $expand
    try:
        response = requests.get(f"{BASE_URL}/ValueSet")
        if response.status_code == 200:
            valuesets = response.json()
            if valuesets:
                vs_url = valuesets[0].get("url")
                if vs_url:
                    expand_response = requests.get(f"{BASE_URL}/ValueSet/$expand?url={vs_url}")
                    if expand_response.status_code == 200:
                        results.append("$expand: ✅")
                    else:
                        results.append(f"$expand: ❌ ({expand_response.status_code})")
                else:
                    results.append("$expand: ⚠️ (no ValueSet URL)")
            else:
                results.append("$expand: ⚠️ (no ValueSets)")
        else:
            results.append(f"$expand: ❌ (can't get ValueSets)")
    except Exception as e:
        results.append(f"$expand: ❌ ({str(e)})")
    
    success = all("✅" in result for result in results)
    return print_result(success, f"Additional operations: {', '.join(results)}")

def run_new_features_tests():
    """Run tests for new features and login fix"""
    print("\n" + "="*80)
    print("FHIR TERMINOLOGY SERVICE - NEW FEATURES TEST SUITE")
    print("="*80)
    print(f"Backend URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().isoformat()}")
    print("="*80)
    
    results = []
    
    # CRITICAL PRIORITY TESTS
    print("\n" + "="*50)
    print("CRITICAL PRIORITY - LOGIN FIX TESTS")
    print("="*50)
    results.append(("Login Fix", test_login_fix()))
    results.append(("Audit Logs Access", test_audit_logs_with_token()))
    
    # HIGH PRIORITY TESTS
    print("\n" + "="*50)
    print("HIGH PRIORITY - NEW FHIR OPERATIONS")
    print("="*50)
    results.append(("CodeSystem $find-matches", test_codesystem_find_matches()))
    results.append(("ValueSet $compose", test_valueset_compose()))
    results.append(("ValueSet $find-matches", test_valueset_find_matches()))
    
    # MEDIUM PRIORITY TESTS
    print("\n" + "="*50)
    print("MEDIUM PRIORITY - FILE UPLOAD")
    print("="*50)
    results.append(("File Upload Size", test_file_upload_size()))
    
    # ADDITIONAL VERIFICATION
    print("\n" + "="*50)
    print("ADDITIONAL VERIFICATION")
    print("="*50)
    results.append(("Other FHIR Operations", test_additional_fhir_operations()))
    
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
    
    # Detailed results
    print("\n" + "="*80)
    print("DETAILED RESULTS:")
    print("="*80)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    if failed > 0:
        print("\n" + "="*80)
        print("FAILED TESTS NEED ATTENTION:")
        print("="*80)
        for name, result in results:
            if not result:
                print(f"  ❌ {name}")
    
    print("\n" + "="*80)
    return passed, failed, total

if __name__ == "__main__":
    passed, failed, total = run_new_features_tests()
    exit(0 if failed == 0 else 1)