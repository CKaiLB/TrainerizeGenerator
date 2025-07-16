#!/usr/bin/env python3
"""
Test script for the webhook server
"""

import requests
import json
import time

def test_webhook():
    """Test the webhook with sample Tally data"""
    
    # Sample Tally webhook data
    sample_tally_data = {
        "eventId": "214f0ed8-9f45-47fe-b820-a33bd0032b70",
        "eventType": "FORM_RESPONSE",
        "createdAt": "2025-07-03T17:47:46.443Z",
        "data": {
            "responseId": "pbAxYky",
            "submissionId": "pbAxYky",
            "respondentId": "QZLVk1",
            "formId": "31Y66W",
            "formName": "Boon Fay's 16-Week Transformation Program",
            "createdAt": "2025-07-03T17:47:46.000Z",
            "fields": [
                {
                    "key": "question_zMWrpa",
                    "label": "First Name",
                    "type": "INPUT_TEXT",
                    "value": "Timmy"
                },
                {
                    "key": "question_59EG66",
                    "label": "Last Name",
                    "type": "INPUT_TEXT",
                    "value": "Explorer"
                },
                {
                    "key": "question_WReGQL",
                    "label": "What is your top fitness goal?",
                    "type": "INPUT_TEXT",
                    "value": "To lose weight"
                },
                {
                    "key": "question_Dp0v2q",
                    "label": "How would you classify this goal: ",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["b0ec82cd-4ce0-42e2-a1d2-b303478ff4cd"],
                    "options": [
                        {"id": "b0ec82cd-4ce0-42e2-a1d2-b303478ff4cd", "text": "Weight Loss"}
                    ]
                },
                {
                    "key": "question_gqQypM",
                    "label": "How many days per week can you commit to exercise?",
                    "type": "INPUT_TEXT",
                    "value": "3"
                },
                {
                    "key": "question_y40KG6",
                    "label": "Which days?",
                    "type": "CHECKBOXES",
                    "value": ["0e8844f7-96ac-4f46-a665-c0f2688bf004", "fa97315b-71f4-41f4-a078-0ea61b2ff5ac"],
                    "options": [
                        {"id": "0e8844f7-96ac-4f46-a665-c0f2688bf004", "text": "Saturday"},
                        {"id": "fa97315b-71f4-41f4-a078-0ea61b2ff5ac", "text": "Sunday"}
                    ]
                }
            ]
        }
    }
    
    # Webhook URL (assuming running locally)
    webhook_url = "http://localhost:6000/webhook/tally"
    
    print("🧪 Testing Webhook Server")
    print("=" * 50)
    
    try:
        print("📤 Sending POST request to webhook...")
        print(f"📝 Sample data: {json.dumps(sample_tally_data, indent=2)[:200]}...")
        
        # Send POST request to webhook
        response = requests.post(
            webhook_url,
            json=sample_tally_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook test successful!")
            print(f"📊 Full name extracted: {result.get('full_name', 'N/A')}")
            print(f"📊 Trainerize result: {result.get('trainerize_result', 'N/A')}")
            print(f"📊 Fitness program sections: {len(result.get('fitness_program', {}).get('sections', []))}")
        else:
            print(f"❌ Webhook test failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to webhook server. Make sure it's running on localhost:5000")
    except Exception as e:
        print(f"❌ Error testing webhook: {str(e)}")

def test_health_check():
    """Test the health check endpoint"""
    
    health_url = "http://localhost:5000/health"
    
    try:
        print("\n🏥 Testing health check...")
        response = requests.get(health_url)
        
        if response.status_code == 200:
            print("✅ Health check successful!")
            print(f"📊 Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to health check endpoint")
    except Exception as e:
        print(f"❌ Error testing health check: {str(e)}")

if __name__ == "__main__":
    test_health_check()
    test_webhook() 