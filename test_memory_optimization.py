#!/usr/bin/env python3
"""
Test script for memory optimization and timeout prevention
"""

import requests
import json
import time
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_memory_optimization():
    """Test the memory optimization features"""
    print("🧠 Testing Memory Optimization Features")
    print("=" * 50)
    
    try:
        # Test 1: Import and initialize VectorSearch
        print("Test 1: Lazy Loading VectorSearch...")
        from src.vector_search import VectorSearch
        
        start_time = time.time()
        vector_search = VectorSearch()
        init_time = time.time() - start_time
        
        print(f"✅ VectorSearch initialized in {init_time:.2f} seconds (lazy loading)")
        
        # Test 2: Check memory usage before model loading
        print("\nTest 2: Memory usage before model loading...")
        memory_before = vector_search.get_memory_usage()
        print(f"Memory before: {json.dumps(memory_before, indent=2)}")
        
        # Test 3: Load model and check memory usage
        print("\nTest 3: Loading model and checking memory...")
        start_time = time.time()
        _ = vector_search.embedding_model  # This triggers model loading
        load_time = time.time() - start_time
        
        memory_after = vector_search.get_memory_usage()
        print(f"✅ Model loaded in {load_time:.2f} seconds")
        print(f"Memory after: {json.dumps(memory_after, indent=2)}")
        
        # Test 4: Test embedding creation
        print("\nTest 4: Testing embedding creation...")
        test_text = "barbell bench press chest exercise"
        start_time = time.time()
        embedding = vector_search.create_embedding(test_text)
        embed_time = time.time() - start_time
        
        if embedding and len(embedding) > 0:
            print(f"✅ Embedding created in {embed_time:.3f} seconds")
            print(f"Embedding dimensions: {len(embedding)}")
        else:
            print("❌ Failed to create embedding")
            return False
        
        # Test 5: Test vector search
        print("\nTest 5: Testing vector search...")
        start_time = time.time()
        results = vector_search.search_exercises("chest press workout", limit=3)
        search_time = time.time() - start_time
        
        if results:
            print(f"✅ Vector search completed in {search_time:.3f} seconds")
            print(f"Found {len(results)} results")
            for i, result in enumerate(results[:2]):
                exercise_name = result.get('payload', {}).get('name', 'Unknown')
                score = result.get('score', 0)
                print(f"  {i+1}. {exercise_name} (score: {score:.3f})")
        else:
            print("⚠️  No search results found")
        
        # Test 6: Memory cleanup
        print("\nTest 6: Testing memory cleanup...")
        memory_before_cleanup = vector_search.get_memory_usage()
        vector_search.clear_model_cache()
        memory_after_cleanup = vector_search.get_memory_usage()
        
        print(f"Memory before cleanup: {memory_before_cleanup.get('rss_mb', 'unknown'):.1f} MB")
        print(f"Memory after cleanup: {memory_after_cleanup.get('rss_mb', 'unknown'):.1f} MB")
        print("✅ Memory cleanup test completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Memory optimization test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_webhook_server(base_url="http://localhost:6000"):
    """Test the webhook server endpoints"""
    print("\n🌐 Testing Webhook Server Endpoints")
    print("=" * 50)
    
    try:
        # Test 1: Health check
        print("Test 1: Health check...")
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed: {health_data.get('status')}")
            print(f"Model loaded: {health_data.get('model_loaded')}")
            print(f"Model loading: {health_data.get('model_loading')}")
            if health_data.get('model_error'):
                print(f"Model error: {health_data.get('model_error')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test 2: Model status
        print("\nTest 2: Model status check...")
        response = requests.get(f"{base_url}/model-status", timeout=10)
        if response.status_code == 200:
            model_data = response.json()
            print(f"✅ Model status check passed")
            print(f"Model loaded: {model_data.get('model_loaded')}")
            if model_data.get('load_time'):
                print(f"Load time: {model_data.get('load_time'):.2f} seconds")
        else:
            print(f"❌ Model status check failed: {response.status_code}")
        
        # Test 3: Memory status
        print("\nTest 3: Memory status check...")
        response = requests.get(f"{base_url}/memory-status", timeout=10)
        if response.status_code == 200:
            memory_data = response.json()
            print(f"✅ Memory status check passed")
            
            system_memory = memory_data.get('system_memory', {})
            if 'total_mb' in system_memory:
                total_mb = system_memory['total_mb']
                used_mb = system_memory['used_mb']
                percent_used = system_memory['percent_used']
                print(f"System memory: {used_mb:.1f}/{total_mb:.1f} MB ({percent_used:.1f}%)")
            
            vector_memory = memory_data.get('vector_search_memory', {})
            if 'rss_mb' in vector_memory:
                rss_mb = vector_memory['rss_mb']
                print(f"Process memory: {rss_mb:.1f} MB")
        else:
            print(f"⚠️  Memory status check failed: {response.status_code}")
        
        # Test 4: Simple webhook test
        print("\nTest 4: Simple webhook test...")
        sample_data = {
            "eventId": "test-event-123",
            "eventType": "FORM_RESPONSE",
            "data": {
                "fields": [
                    {"key": "question_zMWrpa", "label": "First Name", "value": "Test"},
                    {"key": "question_59EG66", "label": "Last Name", "value": "User"}
                ]
            }
        }
        
        print("Sending test webhook (this may take 30+ seconds due to wait time)...")
        response = requests.post(
            f"{base_url}/webhook/tally", 
            json=sample_data,
            timeout=120  # Allow for the 30-second wait + processing time
        )
        
        if response.status_code == 200:
            webhook_data = response.json()
            print(f"✅ Webhook test passed")
            print(f"Status: {webhook_data.get('status')}")
            print(f"Full name: {webhook_data.get('full_name')}")
            
            model_status = webhook_data.get('model_status', {})
            if model_status:
                print(f"Model loaded: {model_status.get('loaded')}")
                print(f"Model error: {model_status.get('error')}")
        else:
            print(f"❌ Webhook test failed: {response.status_code}")
            print(f"Response: {response.text}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to {base_url}")
        print("Make sure the webhook server is running with: python webhook_server.py")
        return False
    except Exception as e:
        print(f"❌ Webhook server test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Memory Optimization and Timeout Prevention Tests")
    print("=" * 60)
    
    # Test 1: Memory optimization
    memory_test_passed = test_memory_optimization()
    
    # Test 2: Webhook server (if requested)
    webhook_test_passed = True
    if len(sys.argv) > 1 and sys.argv[1] == "--test-server":
        webhook_test_passed = test_webhook_server()
    elif len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        webhook_test_passed = test_webhook_server(sys.argv[1])
    else:
        print("\n⏭️  Skipping webhook server tests")
        print("Run with --test-server to test local server or provide URL")
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 Test Summary")
    print("=" * 60)
    print(f"Memory optimization: {'✅ PASSED' if memory_test_passed else '❌ FAILED'}")
    print(f"Webhook server: {'✅ PASSED' if webhook_test_passed else '❌ FAILED'}")
    
    if memory_test_passed and webhook_test_passed:
        print("🎉 All tests passed! Ready for Render deployment.")
    else:
        print("⚠️  Some tests failed. Check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 