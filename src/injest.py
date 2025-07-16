import requests
from sentence_transformers import SentenceTransformer
import torch
import gc
import numpy as np
from dotenv import load_dotenv
import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
import time
import json
import uuid
from typing import Dict, List, Optional, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "trainerize_exercises"

# Trainerize API configuration
TRAINERIZE_API_URL = "https://api.trainerize.com/v03/exercise/get"
TRAINERIZE_AUTH = os.getenv("TRAINERIZE_AUTH")

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    prefer_grpc=True
)

model = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
model.max_seq_length = 512  # Increased for full exercise objects

model_dimension = model.get_sentence_embedding_dimension()

def fetch_exercise_from_trainerize(exercise_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single exercise from Trainerize API"""
    try:
        payload = {"id": exercise_id}
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": TRAINERIZE_AUTH
        }
        
        response = requests.post(TRAINERIZE_API_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data
        elif response.status_code == 404:
            logger.warning(f"Exercise {exercise_id} not found")
            return None
        else:
            logger.error(f"Failed to fetch exercise {exercise_id}: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for exercise {exercise_id}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error for exercise {exercise_id}: {str(e)}")
        return None

def prepare_exercise_text(exercise_data: Dict[str, Any]) -> str:
    """Convert exercise data to searchable text"""
    text_parts = []
    
    # Handle the actual Trainerize API response structure
    if isinstance(exercise_data, dict):
        # Extract the actual exercise data if it's nested
        if 'data' in exercise_data:
            exercise_data = exercise_data['data']
        elif 'exercise' in exercise_data:
            exercise_data = exercise_data['exercise']
        elif 'result' in exercise_data:
            exercise_data = exercise_data['result']
    
    # Basic exercise information
    if exercise_data.get('name'):
        text_parts.append(f"Exercise: {exercise_data['name']}")
    
    if exercise_data.get('alternateName'):
        text_parts.append(f"Alternate Name: {exercise_data['alternateName']}")
    
    if exercise_data.get('description'):
        text_parts.append(f"Description: {exercise_data['description']}")
    
    if exercise_data.get('type'):
        text_parts.append(f"Type: {exercise_data['type']}")
    
    if exercise_data.get('recordType'):
        text_parts.append(f"Record Type: {exercise_data['recordType']}")
    
    # Handle tags - Trainerize API returns array of objects with type and name
    tags = exercise_data.get('tags', [])
    if tags and isinstance(tags, list):
        # Group tags by type for better organization
        tag_groups = {}
        for tag in tags:
            if isinstance(tag, dict) and 'type' in tag and 'name' in tag:
                tag_type = tag['type']
                tag_name = tag['name']
                if tag_type not in tag_groups:
                    tag_groups[tag_type] = []
                tag_groups[tag_type].append(tag_name)
        
        # Add grouped tags to text
        for tag_type, tag_names in tag_groups.items():
            text_parts.append(f"{tag_type.title()}: {', '.join(tag_names)}")
    
    # Handle media information if available
    if exercise_data.get('media'):
        media = exercise_data['media']
        if media.get('type'):
            text_parts.append(f"Media Type: {media['type']}")
        if media.get('status'):
            text_parts.append(f"Media Status: {media['status']}")
    
    # Handle video information
    if exercise_data.get('videoType'):
        text_parts.append(f"Video Type: {exercise_data['videoType']}")
    
    if exercise_data.get('videoStatus'):
        text_parts.append(f"Video Status: {exercise_data['videoStatus']}")
    
    # Add version information
    if exercise_data.get('version'):
        text_parts.append(f"Version: {exercise_data['version']}")
    
    # Add any other fields that might be useful
    for key, value in exercise_data.items():
        if key not in ['name', 'alternateName', 'description', 'type', 'recordType', 
                      'tags', 'media', 'videoType', 'videoStatus', 'version', 
                      'id', 'exerciseId', 'videoUrl', 'videoMobileUrl', 'numPhotos', 
                      'lastPerformed']:
            if value and str(value).strip():
                text_parts.append(f"{key.title()}: {value}")
    
    result = " | ".join(text_parts)
    return result

def create_exercise_embedding(exercise_text: str) -> np.ndarray:
    """Create embedding for exercise text"""
    try:
        # Encode the text
        embedding = model.encode(exercise_text, convert_to_tensor=False, show_progress_bar=False)
        # Ensure it's float32 and convert to list of floats
        return embedding.astype(np.float32)
    except Exception as e:
        logger.error(f"Error creating embedding: {str(e)}")
        raise

def ensure_collection_exists(collection_name: str) -> None:
    """Ensure the Qdrant collection exists with correct configuration"""
    try:
        collections = client.get_collections()
        collection_exists = any(col.name == collection_name for col in collections.collections)
        
        if collection_exists:
            # Check if the collection has the correct vector configuration
            try:
                collection_info = client.get_collection(collection_name)
                vectors_config = collection_info.config.params.vectors
                
                # Check if the 'text' vector exists and has correct configuration
                if hasattr(vectors_config, 'vectors') and 'text' in vectors_config.vectors:
                    logger.info(f"Collection '{collection_name}' already exists with correct configuration.")
                    return
                else:
                    logger.warning(f"Collection '{collection_name}' exists but has incorrect vector configuration. Recreating...")
                    client.delete_collection(collection_name)
                    collection_exists = False
            except Exception as e:
                logger.warning(f"Error checking collection configuration: {str(e)}. Recreating...")
                try:
                    client.delete_collection(collection_name)
                except:
                    pass
                collection_exists = False
        
        if not collection_exists:
            logger.info(f"Creating new collection '{collection_name}'...")
            client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "text": VectorParams(
                        size=model.get_sentence_embedding_dimension(),
                        distance=Distance.COSINE,
                        on_disk=True
                    )
                },
            )
            logger.info(f"Collection '{collection_name}' created successfully.")
            
    except Exception as e:
        logger.error(f"Error handling collection: {str(e)}")
        raise e

def upload_exercise_to_qdrant(exercise_data: Dict[str, Any], exercise_id: int) -> bool:
    """Upload a single exercise to Qdrant"""
    try:
        # Prepare exercise text
        exercise_text = prepare_exercise_text(exercise_data)
        
        if not exercise_text.strip():
            logger.warning(f"Empty exercise text for ID {exercise_id}")
            return False
        
        # Create embedding
        embedding = create_exercise_embedding(exercise_text)
        
        # Ensure embedding is converted to list of floats, not strings
        embedding_list = [float(x) for x in embedding.tolist()]
        
        # Extract tags for payload
        tags = exercise_data.get('tags', [])
        tag_groups = {}
        if tags and isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, dict) and 'type' in tag and 'name' in tag:
                    tag_type = tag['type']
                    tag_name = tag['name']
                    if tag_type not in tag_groups:
                        tag_groups[tag_type] = []
                    tag_groups[tag_type].append(tag_name)
        
        # Create point with proper UUID
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector={"text": embedding_list},  # Use the float list
            payload={
                "exercise_id": exercise_id,
                "name": exercise_data.get('name', ''),
                "alternate_name": exercise_data.get('alternateName', ''),
                "type": exercise_data.get('type', ''),
                "record_type": exercise_data.get('recordType', ''),
                "description": exercise_data.get('description', ''),
                "tags": tag_groups,
                "main_muscle": tag_groups.get('mainMuscle', []),
                "equipment": tag_groups.get('equipment', []),
                "level": tag_groups.get('level', []),
                "mechanics": tag_groups.get('mechanics', []),
                "force": tag_groups.get('force', []),
                "movement": tag_groups.get('movement', []),
                "text": exercise_text,
                "source": "trainerize_api",
                "uploaded_at": time.time(),
                "version": exercise_data.get('version', ''),
                "media_type": exercise_data.get('media', {}).get('type', ''),
                "video_status": exercise_data.get('videoStatus', '')
            }
        )
        
        # Upload to Qdrant
        client.upsert(collection_name=COLLECTION_NAME, points=[point])
        
        logger.info(f"Successfully uploaded exercise {exercise_id}: {exercise_data.get('name', 'Unknown')}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to upload exercise {exercise_id}: {str(e)}")
        return False

def batch_upload_exercises(exercises_data: List[Dict[str, Any]], batch_size: int = 10) -> int:
    """Upload exercises in batches"""
    successful_uploads = 0
    total_batches = (len(exercises_data) + batch_size - 1) // batch_size
    
    for i in range(0, len(exercises_data), batch_size):
        batch = exercises_data[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} exercises)")
        
        batch_success = 0
        for exercise_data in batch:
            exercise_id = exercise_data.get('id', exercise_data.get('exerciseId', 0))
            if upload_exercise_to_qdrant(exercise_data, exercise_id):
                batch_success += 1
        
        successful_uploads += batch_success
        logger.info(f"Batch {batch_num} completed: {batch_success}/{len(batch)} successful")
        
        # Small delay between batches to avoid overwhelming the API
        time.sleep(0.5)
    
    return successful_uploads

def fetch_and_vectorize_exercises(start_id: int = 1, end_id: int = 730) -> None:
    """Main function to fetch exercises from Trainerize and vectorize them"""
    logger.info(f"Starting exercise vectorization from ID {start_id} to {end_id}")
    
    # Ensure collection exists
    ensure_collection_exists(COLLECTION_NAME)
    
    # Fetch exercises
    exercises_data = []
    successful_fetches = 0
    
    for exercise_id in range(start_id, end_id + 1):
        logger.info(f"Fetching exercise {exercise_id}/{end_id}")
        
        exercise_data = fetch_exercise_from_trainerize(exercise_id)
        
        if exercise_data:
            # Add the exercise ID to the data for reference
            exercise_data['id'] = exercise_id
            exercises_data.append(exercise_data)
            successful_fetches += 1
        else:
            logger.warning(f"Failed to fetch exercise {exercise_id}")
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    logger.info(f"Fetched {successful_fetches} exercises out of {end_id - start_id + 1} attempts")
    
    if not exercises_data:
        logger.error("No exercises were successfully fetched")
        return
    
    # Upload to Qdrant
    logger.info("Starting upload to Qdrant...")
    successful_uploads = batch_upload_exercises(exercises_data, batch_size=5)
    
    logger.info(f"Vectorization complete! Successfully uploaded {successful_uploads}/{len(exercises_data)} exercises")
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"EXERCISE VECTORIZATION SUMMARY")
    print(f"{'='*50}")
    print(f"Total exercises attempted: {end_id - start_id + 1}")
    print(f"Successfully fetched: {successful_fetches}")
    print(f"Successfully uploaded to Qdrant: {successful_uploads}")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Model: all-MiniLM-L6-v2")
    print(f"{'='*50}")

def search_exercises(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for exercises in Qdrant"""
    try:
        # Create query vector
        query_vector = create_exercise_embedding(query)
        
        # Ensure query vector is converted to list of floats, not strings
        query_vector_list = [float(x) for x in query_vector.tolist()]
        
        # Search in Qdrant - use the correct named vector format
        search_results = client.search(
            collection_name=COLLECTION_NAME,
            vector={"text": query_vector_list},  # Use the float list
            limit=limit
        )
        
        logger.info(f"Search returned {len(search_results)} results")
        
        results = []
        for i, result in enumerate(search_results):
            try:
                logger.debug(f"Processing result {i}: score type={type(result.score)}, value={result.score}")
                # Safely convert score to float
                score = float(result.score) if result.score is not None else 0.0
                results.append({
                    "score": score,
                    "payload": result.payload,
                    "id": result.id
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Error processing search result {i} score: {e}, score={result.score}")
                # Skip this result if score conversion fails
                continue
        
        logger.info(f"Successfully processed {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []

# Main execution
if __name__ == "__main__":
    print("🚀 Starting Trainerize Exercise Vectorization")
    print("=" * 50)
    
    # Check environment variables
    if not QDRANT_URL or not QDRANT_API_KEY:
        print("❌ Error: QDRANT_URL and QDRANT_API_KEY must be set in environment variables")
        exit(1)
    
    try:
        # Fetch and vectorize exercises 1-730
        fetch_and_vectorize_exercises(1, 730)
        
        # Optional: Test search functionality
        print("\n🔍 Testing search functionality...")
        test_results = search_exercises("bench press chest", limit=5)
        if test_results:
            print("✅ Search test successful!")
            print(f"Found {len(test_results)} results for 'bench press chest'")
            for i, result in enumerate(test_results[:3]):
                print(f"  {i+1}. {result['payload'].get('name', 'Unknown')} (Score: {result['score']:.3f})")
        else:
            print("⚠️  Search test returned no results")
            
    except KeyboardInterrupt:
        print("\n⏹️  Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during execution: {str(e)}")
        logger.error(f"Execution error: {str(e)}")
    
    print("\n✅ Exercise vectorization script completed!")