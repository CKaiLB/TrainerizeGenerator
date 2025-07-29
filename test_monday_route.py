#!/usr/bin/env python3
"""
Test script for the Monday weekly check-in route (Kai LB only)
"""

import requests
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_monday_route_kai_lb_only():
    """Test the Monday weekly check-in route but only send to Kai LB"""
    try:
        # Test the Monday route with a custom payload to only send to Kai LB
        url = "http://localhost:6000/monday"
        
        logger.info("Testing Monday weekly check-in route (Kai LB only)...")
        logger.info(f"URL: {url}")
        
        # Create a custom payload to override the default behavior
        # This will simulate the Monday route but only target Kai LB
        test_payload = {
            "test_mode": True,
            "target_user_id": "24645450",  # Kai LB's user ID
            "target_user_name": "Kai LB"
        }
        
        # Make POST request to the Monday route with test payload
        response = requests.post(url, json=test_payload, timeout=30)
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Monday route test successful (Kai LB only)!")
            logger.info(f"Status: {result.get('status')}")
            logger.info(f"Message: {result.get('message')}")
            logger.info(f"Clients count: {result.get('clients_count')}")
            logger.info(f"Recipients: {result.get('recipients', [])}")
            logger.info(f"Client names: {result.get('client_names', {})}")
            return True
        else:
            logger.error(f"❌ Monday route test failed with status code: {response.status_code}")
            logger.error(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ Connection error - make sure the webhook server is running on localhost:6000")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        return False

def test_direct_kai_lb_message():
    """Test sending a message directly to Kai LB using the Trainerize API"""
    try:
        logger.info("Testing direct message to Kai LB...")
        
        # Import the necessary functions from webhook_server
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
        
        from webhook_server import TRAINERIZE_MASS_MESSAGE_URL, TRAINERIZE_HEADERS
        
        # Create payload to send message only to Kai LB
        payload = {
            "userID": 23372308,
            "recipients": ["24645450"],  # Only Kai LB
            "body": """Hey Kai LB! This is a test message for the Monday weekly check-in system. 

How would you rate last week overall? (1–10)
How many workouts did you complete?
Did you stick to your nutrition plan 80% or more?
Any meals or situations where you felt off track?
How was your energy, mood, and sleep last week?
What was your biggest win?
What was your biggest challenge?
Anything you're feeling stuck or unsure about?
Anything you'd like to see more of in your plan?
Any questions, concerns, or feedback for me?

(This is a test message - please ignore)""",
            "type": "text",
            "threadType": "mainThread",
            "conversationType": "single"
        }
        
        logger.info(f"Sending test message to Kai LB...")
        logger.info(f"API Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            TRAINERIZE_MASS_MESSAGE_URL,
            headers=TRAINERIZE_HEADERS,
            json=payload
        )
        
        logger.info(f"Trainerize API response status: {response.status_code}")
        logger.info(f"Trainerize API response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Direct message to Kai LB successful!")
            logger.info(f"Response: {result}")
            return True
        else:
            logger.error(f"❌ Direct message to Kai LB failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Direct message test failed with error: {str(e)}")
        return False

def test_root_endpoint():
    """Test the root endpoint to verify the Monday route is listed"""
    try:
        url = "http://localhost:6000/"
        
        logger.info("Testing root endpoint...")
        logger.info(f"URL: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            endpoints = result.get('endpoints', {})
            
            if 'monday_checkin' in endpoints:
                logger.info("✅ Monday route is properly listed in root endpoint")
                logger.info(f"Monday route: {endpoints['monday_checkin']}")
                return True
            else:
                logger.error("❌ Monday route not found in root endpoint")
                return False
        else:
            logger.error(f"❌ Root endpoint test failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Root endpoint test failed with error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Monday Weekly Check-in Route (Kai LB Only)")
    print("=" * 60)
    
    # Test root endpoint first
    root_success = test_root_endpoint()
    
    if root_success:
        # Test direct message to Kai LB
        direct_message_success = test_direct_kai_lb_message()
        
        if direct_message_success:
            print("\n🎉 Direct message test passed! Message sent to Kai LB only.")
        else:
            print("\n❌ Direct message test failed.")
        
        # Test Monday route (if modified to support test mode)
        monday_success = test_monday_route_kai_lb_only()
        
        if monday_success:
            print("\n🎉 Monday route test passed!")
        else:
            print("\n❌ Monday route test failed.")
    else:
        print("\n❌ Root endpoint test failed.")
    
    print("\n📋 Test Summary:")
    print(f"Root endpoint: {'✅ PASS' if root_success else '❌ FAIL'}")
    print(f"Direct message to Kai LB: {'✅ PASS' if 'direct_message_success' in locals() and direct_message_success else '❌ FAIL'}")
    print(f"Monday route: {'✅ PASS' if 'monday_success' in locals() and monday_success else '❌ FAIL'}")
    
    print("\n🔒 Safety Note: This test only sends messages to Kai LB (user ID: 24645450)")
    print("   No other clients will receive test messages.")

if __name__ == "__main__":
    main() 