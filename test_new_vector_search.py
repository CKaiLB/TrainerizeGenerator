#!/usr/bin/env python3
"""
Test script for the new vector search implementation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from vector_search import VectorSearch
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_vector_search():
    """Test the new vector search implementation"""
    
    print("🧪 Testing New Vector Search Implementation")
    print("=" * 50)
    
    try:
        # Initialize vector search
        vector_search = VectorSearch()
        print("✅ VectorSearch initialized successfully")
        
        # Test embedding creation
        print("\n🔍 Testing embedding creation...")
        test_text = "bench press strength training"
        embedding = vector_search.create_embedding(test_text)
        
        if embedding:
            print(f"✅ Embedding created successfully")
            print(f"📊 Embedding length: {len(embedding)}")
            print(f"📊 First 5 values: {embedding[:5]}")
            print(f"📊 Data type: {type(embedding[0]) if embedding else 'N/A'}")
        else:
            print("❌ Failed to create embedding")
            return
        
        # Test exercise search
        print("\n🔍 Testing exercise search...")
        search_results = vector_search.search_exercises("bench press", limit=3)
        
        if search_results:
            print(f"✅ Search successful: {len(search_results)} results found")
            for i, result in enumerate(search_results):
                print(f"\n  Result {i+1}:")
                print(f"    ID: {result.get('id', 'N/A')}")
                print(f"    Score: {result.get('score', 'N/A')}")
                payload = result.get('payload', {})
                print(f"    Name: {payload.get('name', 'N/A')}")
                print(f"    Type: {payload.get('type', 'N/A')}")
                print(f"    Equipment: {payload.get('equipment', 'N/A')}")
                # Debug: print full payload structure
                print(f"    Full payload keys: {list(payload.keys())}")
                if payload:
                    print(f"    Sample payload values:")
                    for key, value in list(payload.items())[:3]:  # Show first 3 items
                        print(f"      {key}: {value}")
        else:
            print("❌ No search results found")
        
        # Test with different query
        print("\n🔍 Testing with different query...")
        search_results2 = vector_search.search_exercises("squat leg strength", limit=2)
        
        if search_results2:
            print(f"✅ Second search successful: {len(search_results2)} results found")
            for i, result in enumerate(search_results2):
                print(f"\n  Result {i+1}:")
                print(f"    ID: {result.get('id', 'N/A')}")
                print(f"    Score: {result.get('score', 'N/A')}")
                payload = result.get('payload', {})
                print(f"    Name: {payload.get('name', 'N/A')}")
        else:
            print("❌ No results for second search")
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_vector_search() 