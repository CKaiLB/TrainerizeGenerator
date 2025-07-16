import os
import requests
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class VectorSearch:
    """Vector search using SageMaker API for embedding and direct Qdrant HTTP calls"""
    
    def __init__(self):
        """Initialize the vector search with API endpoints"""
        self.sagemaker_url = "https://xksr5iv13c.execute-api.us-east-1.amazonaws.com/prod/predict"
        self.qdrant_url = "https://afaec18b-c1b6-4060-9c24-de488d8baeee.us-east4-0.gcp.cloud.qdrant.io:6333/collections/trainerize_exercises/points/search"
        self.qdrant_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.3RKlrotEJc4VfUA-DnXLjsmQaK-d7VQVvJT3ZHCzX38"
        self.qdrant_headers = {
            "content-type": "application/json",
            "api-key": self.qdrant_api_key
        }
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding using SageMaker API"""
        try:
            # Prepare the request body with required 'mode' field
            payload = {
                "text_inputs": text,
                "mode": "embedding"  # Add the required mode field
            }
            
            # Make POST request to SageMaker API
            response = requests.post(
                self.sagemaker_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                # Parse the response to get the embedding
                result = response.json()
                # Assuming the API returns the embedding in a specific format
                # You may need to adjust this based on the actual response structure
                embedding = result.get("embedding", result.get("vector", result))
                
                # Ensure it's a list of floats
                if isinstance(embedding, list):
                    return [float(x) for x in embedding]
                else:
                    logger.error(f"Unexpected embedding format: {type(embedding)}")
                    return []
            else:
                logger.error(f"SageMaker API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            return []
    
    def search_exercises(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for exercises using direct Qdrant HTTP API"""
        try:
            # Create query embedding
            query_vector = self.create_embedding(query_text)
            
            if not query_vector:
                logger.error("Failed to create query embedding")
                return []
            
            # Prepare the search request body
            search_payload = {
                "vector": {
                    "name": "text",
                    "vector": query_vector
                },
                "limit": limit,
                "with_payload": True
            }
            
            # Make POST request to Qdrant
            response = requests.post(
                self.qdrant_url,
                json=search_payload,
                headers=self.qdrant_headers
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Search returned {len(result.get('result', []))} results")
                
                # Process and return results
                results = []
                for item in result.get('result', []):
                    exercise_data = {
                        'id': item.get('id'),
                        'score': item.get('score'),
                        'payload': item.get('payload', {})
                    }
                    results.append(exercise_data)
                
                return results
            else:
                logger.error(f"Qdrant search error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching exercises: {str(e)}")
            return []
    
    def get_exercise_by_id(self, exercise_id: str) -> Dict[str, Any]:
        """Get a specific exercise by ID"""
        try:
            # Prepare the request to get a specific point
            get_payload = {
                "ids": [exercise_id],
                "with_payload": True,
                "with_vector": True
            }
            
            # Make POST request to Qdrant (adjust URL for getting specific points)
            get_url = self.qdrant_url.replace("/search", "")
            response = requests.post(
                get_url,
                json=get_payload,
                headers=self.qdrant_headers
            )
            
            if response.status_code == 200:
                result = response.json()
                points = result.get('result', {}).get('points', [])
                if points:
                    point = points[0]
                    return {
                        'id': point.get('id'),
                        'payload': point.get('payload', {}),
                        'vector': point.get('vector', {})
                    }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting exercise by ID: {str(e)}")
            return {} 