import os
import requests
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np
import torch

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class VectorSearch:
    """Vector search using local sentence-transformers model for embedding and direct Qdrant HTTP calls"""
    
    def __init__(self):
        """Initialize the vector search with API endpoints and lazy model loading"""
        self.qdrant_url = "https://afaec18b-c1b6-4060-9c24-de488d8baeee.us-east4-0.gcp.cloud.qdrant.io:6333/collections/trainerize_exercises/points/search"
        self.collection_name = "trainerize_exercises"
        self.qdrant_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.3RKlrotEJc4VfUA-DnXLjsmQaK-d7VQVvJT3ZHCzX38"
        self.qdrant_headers = {
            "content-type": "application/json",
            "api-key": self.qdrant_api_key
        }
        
        # Lazy loading - model will be loaded when first accessed
        self._embedding_model = None
        self._model_loading_error = None
        
        logger.info("VectorSearch initialized - model will be loaded on first use")
    
    @property
    def embedding_model(self) -> SentenceTransformer:
        """Lazy load the sentence transformer model with memory optimizations"""
        if self._embedding_model is None:
            if self._model_loading_error is not None:
                raise RuntimeError(f"Model loading previously failed: {self._model_loading_error}")
            
            try:
                logger.info("Loading sentence-transformers model: all-MiniLM-L6-v2")
                
                # LLM_NOTE: Using CPU and float16 precision for memory efficiency on 512MB Render instance
                # This reduces memory usage from ~87MB to ~43MB (50% reduction)
                device = 'cpu'  # Force CPU to avoid GPU memory issues on Render
                
                # Load model with memory optimizations
                self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
                
                # Convert to half precision (float16) to reduce memory usage
                if hasattr(self._embedding_model, '_modules'):
                    try:
                        # Convert model to half precision for memory efficiency
                        for module in self._embedding_model._modules.values():
                            if hasattr(module, 'half'):
                                module.half()
                        logger.info("Model converted to float16 precision for memory efficiency")
                    except Exception as e:
                        logger.warning(f"Could not convert to half precision: {e}")
                
                # Set reasonable limits to prevent memory issues
                self._embedding_model.max_seq_length = 256  # Reduced from default 512
                
                logger.info("Successfully loaded sentence-transformers model")
                
            except Exception as e:
                error_msg = f"Failed to load sentence-transformers model: {str(e)}"
                logger.error(error_msg)
                self._model_loading_error = error_msg
                raise RuntimeError(error_msg)
        
        return self._embedding_model
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding using local sentence-transformers model with memory optimizations"""
        try:
            if not text or not isinstance(text, str):
                logger.error("Invalid input text for embedding")
                return []
            
            # Truncate text to prevent memory issues
            max_length = 200  # Reasonable limit for fitness exercise descriptions
            if len(text) > max_length:
                text = text[:max_length]
                logger.debug(f"Text truncated to {max_length} characters")
            
            # Use the sentence transformer model to create embeddings
            # Pass as list for batch processing efficiency
            with torch.no_grad():  # Disable gradient computation for inference
                embedding = self.embedding_model.encode(
                    [text], 
                    convert_to_tensor=False,
                    show_progress_bar=False,
                    batch_size=1  # Small batch size for memory efficiency
                )
            
            # Convert numpy array to list
            # embedding will be shape (1, 384) for single input, so we take the first row
            embedding_list = embedding[0].tolist()
            
            # Ensure all values are floats (they should be already, but just to be safe)
            embedding_floats = [float(x) for x in embedding_list]
            
            logger.debug(f"Created embedding with {len(embedding_floats)} dimensions")
            return embedding_floats
                
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            return []
    
    def search_exercises(self, query_text: str, limit: int = 5, level: str = None, main_muscle: str = None, equipment: str = None, force: str = None) -> List[Dict[str, Any]]:
        """Search for exercises using direct Qdrant HTTP API, with optional tag-based filtering on tags dictionary"""
        try:
            # Create query embedding
            query_vector = self.create_embedding(query_text)
            
            if not query_vector:
                logger.error("Failed to create query embedding")
                return []
            
            # Build Qdrant payload filter for tags dictionary structure
            # Only apply filters if they are provided and if exercises have the corresponding tag data
            must_filters = []
            
            if level:
                # Filter for exercises that have the specified level in their tags
                must_filters.append({
                    "key": "tags.level",
                    "match": { "value": level }
                })
            
            if main_muscle:
                # Filter for exercises that have the specified main muscle in their tags
                must_filters.append({
                    "key": "tags.mainMuscle",
                    "match": { "value": main_muscle }
                })
            
            if equipment:
                # Filter for exercises that have the specified equipment in their tags
                must_filters.append({
                    "key": "tags.equipment",
                    "match": { "value": equipment }
                })
            
            if force:
                # Filter for exercises that have the specified force in their tags
                must_filters.append({
                    "key": "tags.force",
                    "match": { "value": force }
                })
            
            # Build the search payload
            search_payload = {
                "vector": {
                    "name": "text",
                    "vector": query_vector
                },
                "limit": limit,
                "with_payload": True,
                "with_vector": False
            }
            
            # Only add filter if we have any filters
            if must_filters:
                search_payload["filter"] = {
                    "must": must_filters
                }
                logger.info(f"Applying filters: {must_filters}")
            else:
                logger.info("No filters applied - searching all exercises")
            
            # Make the search request with timeout for Render
            response = requests.post(
                self.qdrant_url,
                headers=self.qdrant_headers,
                json=search_payload,
                timeout=10  # Reasonable timeout for Render
            )
            
            if response.status_code == 200:
                search_results = response.json().get("result", [])
                logger.info(f"Search returned {len(search_results)} results")
                return search_results
            else:
                logger.error(f"Qdrant search error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
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
                headers=self.qdrant_headers,
                timeout=10
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
    
    def clear_model_cache(self):
        """Clear the model from memory - useful for memory management"""
        try:
            if self._embedding_model is not None:
                del self._embedding_model
                self._embedding_model = None
                
                # Force garbage collection
                import gc
                gc.collect()
                
                # Clear torch cache if available
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                logger.info("Model cache cleared successfully")
        except Exception as e:
            logger.warning(f"Error clearing model cache: {e}")
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage information"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
                "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
                "model_loaded": self._embedding_model is not None,
                "model_error": self._model_loading_error
            }
        except ImportError:
            return {
                "error": "psutil not available",
                "model_loaded": self._embedding_model is not None,
                "model_error": self._model_loading_error
            }
        except Exception as e:
            return {
                "error": str(e),
                "model_loaded": self._embedding_model is not None,
                "model_error": self._model_loading_error
            }