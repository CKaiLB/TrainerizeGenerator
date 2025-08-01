#!/usr/bin/env python3
"""
Test script to verify user 23544758 is excluded from Monday route
"""

import requests
import json

def test_excluded_user():
    """Test that user 23544758 is excluded from Monday route"""
    try:
        print("🧪 Testing User Exclusion - User 23544758")
        print("=" * 50)
        
        # Test payload for excluded user
        test_payload = {
            "test_mode": True,
            "target_user_id": "23544758",  # Excluded user ID
            "target_user_name": "Monica Ewing"  # Based on the logs, this is Monica Ewing
        }
        
        print(f"Test payload: {json.dumps(test_payload, indent=2)}")
        
        # Make the request
        response = requests.post(
            "http://localhost:6000/monday",
            json=test_payload,
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Test successful!")
            print(f"Status: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            print(f"Test mode: {result.get('test_mode')}")
            print(f"Target user: {result.get('target_user')}")
            print(f"Recipients: {result.get('recipients', [])}")
            print(f"Client names: {result.get('client_names', {})}")
            print(f"Excluded users: {result.get('excluded_users', [])}")
            
            # Verify the user was excluded
            if result.get('status') == 'warning' and 'excluded' in result.get('message', '').lower():
                print("✅ User 23544758 successfully excluded!")
                return True
            else:
                print("❌ User 23544758 was not properly excluded")
                return False
        else:
            print(f"❌ Test failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

def test_normal_mode_exclusion():
    """Test that user 23544758 is excluded in normal mode"""
    try:
        print("\n🧪 Testing Normal Mode Exclusion")
        print("=" * 40)
        
        # Test normal mode (no test payload)
        response = requests.post(
            "http://localhost:6000/monday",
            headers={'Content-Type': 'application/json'},
            json={},  # Empty JSON payload for normal mode
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Normal mode test successful!")
            print(f"Status: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            print(f"Clients count: {result.get('clients_count')}")
            print(f"Recipients: {result.get('recipients', [])}")
            print(f"Excluded users: {result.get('excluded_users', [])}")
            
            # Check if 23544758 is in excluded users
            excluded_users = result.get('excluded_users', [])
            if any('Monica' in user or '23544758' in str(user) for user in excluded_users):
                print("✅ User 23544758 properly excluded in normal mode!")
                return True
            else:
                print("❌ User 23544758 not found in excluded users list")
                return False
        else:
            print(f"❌ Normal mode test failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Normal mode test error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing User Exclusion Functionality")
    print("=" * 60)
    
    # Test excluded user in test mode
    test_mode_success = test_excluded_user()
    
    # Test normal mode exclusion
    normal_mode_success = test_normal_mode_exclusion()
    
    print("\n📋 Test Summary:")
    print(f"Test mode exclusion: {'✅ PASS' if test_mode_success else '❌ FAIL'}")
    print(f"Normal mode exclusion: {'✅ PASS' if normal_mode_success else '❌ FAIL'}")
    
    if test_mode_success and normal_mode_success:
        print("\n🎉 All exclusion tests passed! User 23544758 is properly excluded.")
    else:
        print("\n❌ Some exclusion tests failed.")

if __name__ == "__main__":
    main() 