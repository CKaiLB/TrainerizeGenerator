#!/usr/bin/env python3
"""
Webhook server for processing Tally survey responses and generating fitness programs
"""

import os
import sys
import json
import time
import requests
import logging
import threading
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import using absolute imports to avoid relative import issues
from src.fitness_program_orchestrator import FitnessProgramOrchestrator
from src.trainerize_workout_creator import TrainerizeWorkoutCreator
from src.trainerize_training_program_creator import TrainerizeTrainingProgramCreator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# Global model loading status to prevent timeouts
_model_loading_status = {
    "loaded": False,
    "loading": False,
    "error": None,
    "start_time": None
}

# Trainerize API configuration
TRAINERIZE_API_URL = os.environ.get('TRAINERIZE_FIND')
TRAINERIZE_AUTH = os.environ.get('TRAINERIZE_AUTH')
TRAINERIZE_HEADERS = {
    'accept': 'application/json',
    'authorization': TRAINERIZE_AUTH,
    'content-type': 'application/json'
}

def preload_vector_search_model():
    """Preload the vector search model in the background to avoid timeouts"""
    global _model_loading_status
    try:
        _model_loading_status["loading"] = True
        _model_loading_status["start_time"] = time.time()
        logger.info("Preloading vector search model...")
        
        from src.vector_search import VectorSearch
        vector_search = VectorSearch()
        # Trigger model loading by accessing the property
        _ = vector_search.embedding_model
        
        _model_loading_status["loaded"] = True
        _model_loading_status["loading"] = False
        _model_loading_status["error"] = None
        
        load_time = time.time() - _model_loading_status["start_time"]
        logger.info(f"Vector search model preloaded successfully in {load_time:.2f} seconds")
    except Exception as e:
        _model_loading_status["loading"] = False
        _model_loading_status["error"] = str(e)
        logger.error(f"Failed to preload vector search model: {str(e)}")

# Start model preloading in background thread on server startup
preload_thread = threading.Thread(target=preload_vector_search_model, daemon=True)
preload_thread.start()

@app.route('/model-status', methods=['GET'])
def model_status():
    """Check the status of model loading"""
    global _model_loading_status
    
    # If model is not loaded and no error, try to load it
    if not _model_loading_status["loaded"] and not _model_loading_status["error"]:
        try:
            logger.info("Attempting to load model on demand...")
            from src.vector_search import VectorSearch
            vector_search = VectorSearch()
            _ = vector_search.embedding_model
            _model_loading_status["loaded"] = True
            _model_loading_status["error"] = None
            logger.info("Model loaded successfully on demand")
        except Exception as e:
            logger.error(f"Failed to load model on demand: {str(e)}")
            _model_loading_status["error"] = str(e)
    
    status = {
        "model_loaded": _model_loading_status["loaded"],
        "model_loading": _model_loading_status["loading"],
        "model_error": _model_loading_status["error"],
        "timestamp": datetime.now().isoformat()
    }
    
    if _model_loading_status["start_time"]:
        status["load_time"] = time.time() - _model_loading_status["start_time"]
    
    return jsonify(status), 200

def extract_full_name_from_tally_data(tally_data):
    """Extract the full name from Tally survey data"""
    try:
        fields = tally_data.get('data', {}).get('fields', [])
        
        first_name = None
        last_name = None
        
        for field in fields:
            if field.get('key') == 'question_zMWrpa' and field.get('label') == 'First Name':
                first_name = field.get('value', '')
            elif field.get('key') == 'question_59EG66' and field.get('label') == 'Last Name':
                last_name = field.get('value', '')
        
        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error extracting name from Tally data: {str(e)}")
        return None

def find_user_in_trainerize(full_name):
    """Find user in Trainerize API"""
    try:
        payload = {
            "searchTerm": full_name,
            "view": "activeClient",
            "includeBasicMember": False,
            "start": 0,
            "count": 1,
            "verbose": True
        }
        
        logger.info(f"Searching for user: {full_name}")
        logger.info(f"Trainerize API payload: {payload}")
        
        response = requests.post(
            TRAINERIZE_API_URL,
            headers=TRAINERIZE_HEADERS,
            json=payload
        )
        
        logger.info(f"Trainerize API response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Trainerize API response: {result}")
            return result
        else:
            logger.error(f"Trainerize API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error calling Trainerize API: {str(e)}")
        return None

def extract_user_id_from_trainerize_response(trainerize_result):
    """Extract user ID from Trainerize API response, excluding 23372308"""
    try:
        logger.info(f"Extracting user ID from Trainerize response: {trainerize_result}")
        
        if not trainerize_result:
            logger.warning("Trainerize result is None or empty")
            return None
        
        # Check for the actual Trainerize API response structure
        if 'users' in trainerize_result and isinstance(trainerize_result['users'], list):
            logger.info(f"Found users array with {len(trainerize_result['users'])} users")
            for i, user in enumerate(trainerize_result['users']):
                logger.info(f"Checking user {i}: {user}")
                if 'id' in user and str(user['id']) != '23372308':
                    user_id = user['id']
                    logger.info(f"Found valid user ID: {user_id}")
                    return user_id
                elif 'id' in user:
                    logger.info(f"User ID {user['id']} matches excluded ID 23372308")
        
        # Check if there's a direct user ID in the response
        if 'userId' in trainerize_result:
            potential_id = trainerize_result['userId']
            logger.info(f"Found userId in response: {potential_id}")
            if str(potential_id) != '23372308':
                user_id = potential_id
                logger.info(f"Using userId: {user_id}")
                return user_id
            else:
                logger.info(f"userId {potential_id} matches excluded ID 23372308")
        
        # Check in data array if present
        elif 'data' in trainerize_result and isinstance(trainerize_result['data'], list):
            logger.info(f"Checking data array with {len(trainerize_result['data'])} items")
            for i, item in enumerate(trainerize_result['data']):
                logger.info(f"Checking item {i}: {item}")
                if 'id' in item and str(item['id']) != '23372308':
                    user_id = item['id']
                    logger.info(f"Found user ID in data array: {user_id}")
                    return user_id
        
        # Check in nested structures
        elif 'data' in trainerize_result and isinstance(trainerize_result['data'], dict):
            data = trainerize_result['data']
            logger.info(f"Checking nested data structure: {data}")
            if 'id' in data and str(data['id']) != '23372308':
                user_id = data['id']
                logger.info(f"Found user ID in nested data: {user_id}")
                return user_id
            elif 'userId' in data and str(data['userId']) != '23372308':
                user_id = data['userId']
                logger.info(f"Found user ID in nested data userId: {user_id}")
                return user_id
        
        logger.warning("No valid user ID found in Trainerize response")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting user ID from Trainerize response: {str(e)}")
        return None

def process_tally_webhook(tally_data):
    """Process the Tally webhook data and generate fitness program"""
    try:
        logger.info("Processing Tally webhook data")
        
        # Check if model is loaded before processing
        if not _model_loading_status["loaded"]:
            if _model_loading_status["loading"]:
                # Wait for model to load (max 60 seconds)
                wait_start = time.time()
                while _model_loading_status["loading"] and (time.time() - wait_start) < 60:
                    time.sleep(1)
                
                if not _model_loading_status["loaded"]:
                    logger.error("Model loading timed out")
                    return {
                        "status": "error",
                        "message": "Model loading timed out. Please try again.",
                        "model_status": _model_loading_status
                    }
            else:
                logger.error("Model not loaded and not loading")
                return {
                    "status": "error", 
                    "message": "Model not available. Please check /model-status endpoint.",
                    "model_status": _model_loading_status
                }
        
        # Extract full name from Tally data
        full_name = extract_full_name_from_tally_data(tally_data)
        if not full_name:
            logger.error("Could not extract full name from Tally data")
            return {"status": "error", "message": "Could not extract user name from form data"}
        
        logger.info(f"Extracted full name: {full_name}")
        
        # Wait 30 seconds as requested
        logger.info("Waiting 30 seconds before calling Trainerize API...")
        time.sleep(30)
        
        # Find user in Trainerize
        trainerize_result = find_user_in_trainerize(full_name)
        
        # Extract user ID from Trainerize response
        user_id = extract_user_id_from_trainerize_response(trainerize_result)
        logger.info(f"Final extracted user ID: {user_id}")
        
        # Generate fitness program using the orchestrator
        logger.info("Starting fitness program generation...")
        orchestrator = FitnessProgramOrchestrator()
        fitness_program = orchestrator.create_fitness_program(tally_data)
        
        # Convert to JSON for response
        program_json = orchestrator.export_program_to_json(fitness_program)
        program_data = json.loads(program_json)
        
        # Create workouts in Trainerize if user ID is available
        workout_results = []
        training_program_results = []
        
        if user_id:
            logger.info(f"Creating training programs and workouts in Trainerize for user {user_id}")
            
            # Step 1: Create training programs for each focus area
            logger.info("Step 1: Creating training programs...")
            training_program_creator = TrainerizeTrainingProgramCreator()
            
            # Extract focus area names from the program data
            focus_areas = program_data.get("focus_areas", [])
            focus_area_names = [area.get("area_name", "") for area in focus_areas if area.get("area_name")]
            
            if focus_area_names:
                # Get user start date from the program data
                user_start_date = program_data.get("user_context", {}).get("start_date", "")
                if not user_start_date:
                    # Fallback to current date if no start date provided
                    user_start_date = datetime.now().strftime("%Y-%m-%d")
                    logger.warning(f"No start date found, using current date: {user_start_date}")
                
                logger.info(f"Creating training programs for {len(focus_area_names)} focus areas with start date: {user_start_date}")
                
                training_program_results = training_program_creator.create_training_programs_for_focus_areas(
                    user_id, 
                    focus_area_names, 
                    user_start_date
                )
                
                logger.info(f"Created {len(training_program_results)} training programs")
            else:
                logger.warning("No focus areas found for training program creation")
            
            # Step 2: Create workouts with training plan IDs
            logger.info("Step 2: Creating workouts...")
            workout_creator = TrainerizeWorkoutCreator()
            
            # Get exercise matches from the program data
            exercise_matches = program_data.get("exercise_matches", [])
            
            if exercise_matches:
                logger.info(f"Found {len(exercise_matches)} exercise matches for workout creation")
                
                # Create workouts for each training plan
                for result in training_program_results:
                    if result.get("success") and result.get("training_plan_id"):
                        training_plan_id = result["training_plan_id"]
                        focus_area_name = result["focus_area_name"]
                        
                        # Filter exercise matches for this focus area
                        focus_area_exercises = [
                            match for match in exercise_matches 
                            if match.get("focus_area_name") == focus_area_name
                        ]
                        
                        if focus_area_exercises:
                            logger.info(f"Creating workouts for focus area '{focus_area_name}' with training plan ID {training_plan_id}")
                            
                            # Create workouts for this training plan
                            area_workout_results = workout_creator.create_workouts_for_training_plan(
                                user_id,
                                training_plan_id,
                                focus_area_exercises,
                                focus_area_name
                            )
                            
                            workout_results.extend(area_workout_results)
                            logger.info(f"Created {len(area_workout_results)} workouts for focus area '{focus_area_name}'")
                        else:
                            logger.warning(f"No exercises found for focus area '{focus_area_name}'")
                    else:
                        logger.warning(f"Failed to create training program: {result}")
                
            else:
                logger.warning("No exercise matches found for workout creation")
        
        else:
            logger.warning("No user ID found, skipping Trainerize workout creation")
        
        # Prepare response
        response_data = {
            "status": "success",
            "full_name": full_name,
            "user_id": user_id,
            "trainerize_result": trainerize_result,
            "fitness_program": program_data,
            "training_programs": training_program_results,
            "workouts": workout_results,
            "created_at": datetime.now().isoformat(),
            "model_status": _model_loading_status
        }
        
        logger.info(f"Successfully processed webhook for {full_name}")
        return response_data
        
    except Exception as e:
        logger.error(f"Error processing Tally webhook: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "message": str(e),
            "model_status": _model_loading_status,
            "created_at": datetime.now().isoformat()
        }

@app.route('/webhook/tally', methods=['POST'])
def tally_webhook():
    """Handle Tally webhook POST requests"""
    try:
        # Get JSON data from request
        tally_data = request.get_json()
        
        if not tally_data:
            return jsonify({"error": "No JSON data received"}), 400
        
        logger.info(f"Received Tally webhook: {tally_data.get('eventId', 'unknown')}")
        
        # Process the webhook data
        result = process_tally_webhook(tally_data)
        
        if result.get("status") == "success":
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/memory-status', methods=['GET'])
def memory_status():
    """Check memory usage and model status"""
    try:
        from src.vector_search import VectorSearch
        
        # Get memory info from the VectorSearch instance if available
        try:
            vector_search = VectorSearch()
            memory_info = vector_search.get_memory_usage()
        except Exception as e:
            memory_info = {"error": f"Could not get VectorSearch memory info: {str(e)}"}
        
        # Get system memory info
        try:
            import psutil
            system_memory = psutil.virtual_memory()
            system_info = {
                "total_mb": system_memory.total / 1024 / 1024,
                "available_mb": system_memory.available / 1024 / 1024,
                "used_mb": system_memory.used / 1024 / 1024,
                "percent_used": system_memory.percent
            }
        except Exception as e:
            system_info = {"error": f"Could not get system memory info: {str(e)}"}
        
        return jsonify({
            "timestamp": datetime.now().isoformat(),
            "model_status": _model_loading_status,
            "vector_search_memory": memory_info,
            "system_memory": system_info
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with model status"""
    return jsonify({
        "status": "healthy",
        "model_loaded": _model_loading_status["loaded"],
        "model_loading": _model_loading_status["loading"], 
        "model_error": _model_loading_status["error"],
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with basic info"""
    return jsonify({
        "service": "Fitness Program Generator Webhook",
        "endpoints": {
            "webhook": "/webhook/tally (POST)",
            "health": "/health (GET)"
        },
        "timestamp": datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    # Run the Flask app
    port = int(os.environ.get('PORT', 6000))
    
    # Wait for model to load before starting server (max 60 seconds)
    logger.info("Waiting for model to load before starting server...")
    wait_start = time.time()
    while _model_loading_status["loading"] and (time.time() - wait_start) < 60:
        time.sleep(1)
    
    if _model_loading_status["loaded"]:
        logger.info("Model loaded successfully, starting server...")
    elif _model_loading_status["error"]:
        logger.warning(f"Model failed to load ({_model_loading_status['error']}), starting server anyway...")
    else:
        logger.warning("Model loading timed out, starting server anyway...")
    
    app.run(host='0.0.0.0', port=port, debug=True) 