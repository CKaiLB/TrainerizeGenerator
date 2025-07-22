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

# Global model loading status for this worker process
_model_loading_status = {
    "loaded": False,
    "loading": False,
    "error": None,
    "start_time": None,
    "worker_pid": os.getpid()
}

# Global model instance for this worker process
_global_vector_search = None

# Trainerize API configuration
TRAINERIZE_API_URL = os.environ.get('TRAINERIZE_FIND')
TRAINERIZE_AUTH = os.environ.get('TRAINERIZE_AUTH')
TRAINERIZE_HEADERS = {
    'accept': 'application/json',
    'authorization': TRAINERIZE_AUTH,
    'content-type': 'application/json'
}

def load_vector_search_model():
    """Load the vector search model in this worker process"""
    global _model_loading_status, _global_vector_search
    
    worker_pid = os.getpid()
    
    # Check if already loaded in this worker
    if _global_vector_search is not None:
        logger.info(f"Model already loaded in worker PID {worker_pid}")
        return True
    
    # Check if already loading
    if _model_loading_status["loading"]:
        logger.info(f"Model already loading in worker PID {worker_pid}, waiting...")
        wait_start = time.time()
        while _model_loading_status["loading"] and (time.time() - wait_start) < 120:  # 2 minute timeout
            time.sleep(1)
        return _model_loading_status["loaded"]
    
    try:
        _model_loading_status["loading"] = True
        _model_loading_status["start_time"] = time.time()
        _model_loading_status["worker_pid"] = worker_pid
        _model_loading_status["error"] = None
        
        logger.info(f"Loading vector search model in worker PID {worker_pid}...")
        
        from src.vector_search import VectorSearch
        _global_vector_search = VectorSearch()
        
        # Trigger model loading by accessing the property
        _ = _global_vector_search.embedding_model
        
        _model_loading_status["loaded"] = True
        _model_loading_status["loading"] = False
        
        load_time = time.time() - _model_loading_status["start_time"]
        logger.info(f"Vector search model loaded successfully in worker PID {worker_pid} ({load_time:.2f} seconds)")
        
        return True
        
    except Exception as e:
        _model_loading_status["loading"] = False
        _model_loading_status["error"] = str(e)
        logger.error(f"Failed to load vector search model in worker PID {worker_pid}: {str(e)}")
        return False

def get_vector_search_instance():
    """Get the vector search instance, loading if necessary"""
    global _global_vector_search, _model_loading_status
    
    worker_pid = os.getpid()
    
    if _global_vector_search is not None:
        return _global_vector_search
    
    logger.warning(f"Model not loaded in worker PID {worker_pid}, loading on demand...")
    
    # Try to load on demand
    if load_vector_search_model():
        return _global_vector_search
    else:
        raise RuntimeError(f"Failed to load model in worker PID {worker_pid}: {_model_loading_status.get('error', 'Unknown error')}")

@app.route('/model-status', methods=['GET'])
def model_status():
    """Check the status of model loading"""
    global _model_loading_status
    
    current_pid = os.getpid()
    
    # If model is not loaded, try to get it
    if not _model_loading_status["loaded"] and not _model_loading_status["error"]:
        try:
            logger.info(f"Attempting to load model on demand in worker PID {current_pid}...")
            get_vector_search_instance()
        except Exception as e:
            logger.error(f"Failed to load model on demand in worker PID {current_pid}: {str(e)}")
            _model_loading_status["error"] = str(e)
    
    status = {
        "model_loaded": _model_loading_status["loaded"],
        "model_loading": _model_loading_status["loading"],
        "model_error": _model_loading_status["error"],
        "worker_pid": current_pid,
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
        current_pid = os.getpid()
        logger.info(f"Processing Tally webhook data in worker PID {current_pid}")
        
        # Check if model is loaded before processing
        if not _model_loading_status["loaded"]:
            if _model_loading_status["loading"]:
                # Wait for model to load (max 60 seconds)
                logger.info(f"Model still loading in worker PID {current_pid}, waiting...")
                wait_start = time.time()
                while _model_loading_status["loading"] and (time.time() - wait_start) < 60:
                    time.sleep(1)
                
                if not _model_loading_status["loaded"]:
                    error_msg = f"Model loading timed out in worker PID {current_pid}"
                    logger.error(error_msg)
                    return {
                        "status": "error",
                        "message": error_msg,
                        "model_status": _model_loading_status,
                        "worker_pid": current_pid
                    }
            else:
                # Try to load model on demand
                try:
                    logger.info(f"Model not loaded in worker PID {current_pid}, attempting to load...")
                    get_vector_search_instance()
                except Exception as e:
                    error_msg = f"Model not available in worker PID {current_pid}: {str(e)}"
                    logger.error(error_msg)
                    return {
                        "status": "error", 
                        "message": error_msg,
                        "model_status": _model_loading_status,
                        "worker_pid": current_pid
                    }
        
        # Verify we have a working vector search instance
        try:
            vector_search = get_vector_search_instance()
            logger.info(f"Using vector search instance in worker PID {current_pid}")
        except Exception as e:
            error_msg = f"Failed to get vector search instance in worker PID {current_pid}: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "worker_pid": current_pid
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
        
        if user_id:
            logger.info(f"Found user ID: {user_id}")
        else:
            logger.warning("No valid user ID found in Trainerize")
        
        # Generate fitness program regardless of user ID
        logger.info("Starting fitness program generation...")
        
        try:
            # Create the orchestrator and generate the program
            orchestrator = FitnessProgramOrchestrator()
            
            # Extract user context from Tally data for fitness program generation
            user_context_data = extract_user_context_from_tally_data(tally_data)
            if user_context_data:
                # Create UserContext object from the dictionary
                from src.user_context_parser import UserContext
                user_context = UserContext(
                    first_name=user_context_data.get('first_name', ''),
                    last_name=user_context_data.get('last_name', ''),
                    age=user_context_data.get('age', 25),
                    gender=user_context_data.get('gender', 'male'),
                    current_fitness_level=user_context_data.get('current_fitness_level', 'beginner'),
                    fitness_goals=user_context_data.get('fitness_goals', []),
                    workout_frequency=user_context_data.get('workout_frequency', 3),
                    workout_duration=user_context_data.get('workout_duration', 60),
                    preferred_workout_types=user_context_data.get('preferred_workout_types', []),
                    equipment_access=user_context_data.get('equipment_access', []),
                    limitations_injuries=user_context_data.get('limitations_injuries', []),
                    additional_info=user_context_data.get('additional_info', '')
                )
                
                # Generate the fitness program
                fitness_program = orchestrator.create_fitness_program(user_context)
                program_data = fitness_program.to_dict() if fitness_program else None
                
                logger.info(f"Generated fitness program with {len(program_data.get('weeks', [])) if program_data else 0} weeks")
            else:
                logger.error("Failed to extract user context from Tally data")
                program_data = None
                
        except Exception as e:
            logger.error(f"Error generating fitness program: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            program_data = None
        
        # Initialize results
        workout_results = []
        training_program_results = []
        
        # Only proceed with Trainerize operations if we have a user ID
        if user_id and program_data:
            try:
                # Create training programs in Trainerize
                logger.info("Creating training programs in Trainerize...")
                program_creator = TrainerizeTrainingProgramCreator()
                training_program_results = program_creator.create_training_programs_from_fitness_program(
                    fitness_program, user_id
                )
                logger.info(f"Created {len(training_program_results)} training programs")
                
                # Create workouts in Trainerize
                logger.info("Creating workouts in Trainerize...")
                workout_creator = TrainerizeWorkoutCreator()
                
                # Get exercise matches from the fitness program
                exercise_matches = []
                if fitness_program and hasattr(fitness_program, 'weeks'):
                    for week in fitness_program.weeks:
                        for workout in week.workouts:
                            if hasattr(workout, 'exercise_matches'):
                                exercise_matches.extend(workout.exercise_matches)
                
                if exercise_matches:
                    workout_results = workout_creator.create_workouts_from_exercise_matches(
                        exercise_matches, user_id
                    )
                    logger.info(f"Created {len(workout_results)} workouts")
                else:
                    logger.warning("No exercise matches found for workout creation")
                    
            except Exception as e:
                logger.error(f"Error creating Trainerize content: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                
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
            "model_status": _model_loading_status,
            "worker_pid": current_pid
        }
        
        logger.info(f"Successfully processed webhook for {full_name} in worker PID {current_pid}")
        return response_data
        
    except Exception as e:
        current_pid = os.getpid()
        logger.error(f"Error processing Tally webhook in worker PID {current_pid}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "message": str(e),
            "model_status": _model_loading_status,
            "worker_pid": current_pid,
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
        current_pid = os.getpid()
        
        # Get memory info from the VectorSearch instance if available
        try:
            vector_search = get_vector_search_instance()
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
            "worker_pid": current_pid,
            "model_status": _model_loading_status,
            "vector_search_memory": memory_info,
            "system_memory": system_info
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "worker_pid": os.getpid(),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with model status"""
    current_pid = os.getpid()
    return jsonify({
        "status": "healthy",
        "model_loaded": _model_loading_status["loaded"],
        "model_loading": _model_loading_status["loading"], 
        "model_error": _model_loading_status["error"],
        "worker_pid": current_pid,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with service information"""
    return jsonify({
        "service": "Trainerize Fitness Program Generator",
        "status": "running",
        "version": "1.0.0",
        "worker_pid": os.getpid(),
        "model_loaded": _model_loading_status["loaded"],
        "endpoints": {
            "webhook": "/webhook/tally",
            "health": "/health",
            "model_status": "/model-status",
            "memory_status": "/memory-status"
        }
    }), 200

if __name__ == '__main__':
    # Run the Flask app in development mode
    port = int(os.environ.get('PORT', 6000))
    current_pid = os.getpid()
    
    logger.info(f"Starting development server in PID {current_pid}")
    logger.info("Note: In production, model loading happens on first request per worker")
    
    app.run(host='0.0.0.0', port=port, debug=True) 