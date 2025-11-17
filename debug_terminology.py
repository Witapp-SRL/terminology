import requests
import json

BASE_URL = "https://fhirterm.preview.emergentagent.com/api"

def test_debug():
    print("=== DEBUGGING TERMINOLOGY SERVICE ===")
    
    # 1. Get CodeSystems
    print("\n1. Getting CodeSystems...")
    response = requests.get(f"{BASE_URL}/CodeSystem")
    if response.status_code == 200:
        codesystems = response.json()
        print(f"Found {len(codesystems)} CodeSystems")
        for cs in codesystems[:3]:
            print(f"  - {cs.get('name')}: {cs.get('url')}")
            
        # 2. Test lookup with first CodeSystem
        if codesystems:
            first_cs = codesystems[0]
            system_url = first_cs.get('url')
            print(f"\n2. Testing lookup with system: {system_url}")
            
            # Get a concept from this CodeSystem
            cs_detail = requests.get(f"{BASE_URL}/CodeSystem/{first_cs['id']}")
            if cs_detail.status_code == 200:
                cs_data = cs_detail.json()
                concepts = cs_data.get('concept', [])
                if concepts:
                    first_code = concepts[0].get('code')
                    print(f"   Testing with code: {first_code}")
                    
                    # Test lookup
                    lookup_url = f"{BASE_URL}/CodeSystem/$lookup?system={system_url}&code={first_code}"
                    print(f"   URL: {lookup_url}")
                    lookup_response = requests.get(lookup_url)
                    print(f"   Response: {lookup_response.status_code}")
                    print(f"   Content: {lookup_response.text}")
                    
                    # Test find-matches
                    print(f"\n3. Testing find-matches...")
                    find_matches_url = f"{BASE_URL}/CodeSystem/$find-matches?system={system_url}&value=test&exact=false"
                    print(f"   URL: {find_matches_url}")
                    find_response = requests.get(find_matches_url)
                    print(f"   Response: {find_response.status_code}")
                    print(f"   Content: {find_response.text}")
                    
                    # Test find-matches without system
                    print(f"\n4. Testing find-matches without system...")
                    find_matches_url2 = f"{BASE_URL}/CodeSystem/$find-matches?value=A00&exact=false"
                    print(f"   URL: {find_matches_url2}")
                    find_response2 = requests.get(find_matches_url2)
                    print(f"   Response: {find_response2.status_code}")
                    print(f"   Content: {find_response2.text}")
                else:
                    print("   No concepts found in CodeSystem")
            else:
                print(f"   Could not get CodeSystem details: {cs_detail.status_code}")
    else:
        print(f"Could not get CodeSystems: {response.status_code}")

if __name__ == "__main__":
    test_debug()