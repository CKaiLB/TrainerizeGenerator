#!/usr/bin/env python3
"""
Simple test script to demonstrate Kai LB only testing
"""

import requests
import json

def test_kai_lb_only():
    """Test the Monday route with Kai LB only"""
    try:
        print("🧪 Testing Monday Route - Kai LB Only")
        print("=" * 50)
        
        # Test payload for Kai LB only
        test_payload = {
            "test_mode": True,
            "target_user_id": "24645450",  # Kai LB's user ID
            "target_user_name": "Kai LB"
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
        else:
            print(f"❌ Test failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")

if __name__ == "__main__":
    test_kai_lb_only() 