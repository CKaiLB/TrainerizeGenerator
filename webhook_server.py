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

# Additional Trainerize API endpoints
TRAINERIZE_CLIENT_LIST_URL = os.environ.get('TRAINERIZE_CLIENT_LIST_URL')
TRAINERIZE_MASS_MESSAGE_URL = os.environ.get('TRAINERIZE_MASS_MESSAGE_URL')

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

def extract_user_context_from_tally_data(tally_data):
    """Extract user context information from Tally survey data for fitness program generation"""
    try:
        fields = tally_data.get('data', {}).get('fields', [])
        
        # Initialize with fallback values only
        user_context = {
            'first_name': '',
            'last_name': '',
            'age': 25,
            'gender': 'male',
            'current_fitness_level': 'beginner',
            'fitness_goals': [],
            'workout_frequency': 3,
            'workout_duration': 60,
            'preferred_workout_types': [],
            'equipment_access': ['gym'],
            'limitations_injuries': [],
            'additional_info': ''
        }
        
        # Create a map of field keys to values for easier lookup
        field_map = {}
        for field in fields:
            key = field.get('key', '')
            value = field.get('value')
            label = field.get('label', '')
            field_map[key] = {'value': value, 'label': label, 'field': field}
        
        # Extract specific Tally form fields
        
        # Basic Info
        if 'question_zMWrpa' in field_map:
            user_context['first_name'] = str(field_map['question_zMWrpa']['value'] or '')
            
        if 'question_59EG66' in field_map:
            user_context['last_name'] = str(field_map['question_59EG66']['value'] or '')
            
        if 'question_Ap6oao' in field_map:
            try:
                age_value = field_map['question_Ap6oao']['value']
                user_context['age'] = int(age_value) if age_value else 25
            except (ValueError, TypeError):
                user_context['age'] = 25
                
        if 'question_lOVlDB' in field_map:
            gender_value = field_map['question_lOVlDB']['value']
            if gender_value and str(gender_value).lower() in ['male', 'female']:
                user_context['gender'] = str(gender_value).lower()
        
        # Fitness Goals
        fitness_goals = []
        if 'question_WReGQL' in field_map:
            goal_text = field_map['question_WReGQL']['value']
            if goal_text:
                fitness_goals.append(str(goal_text))
        
        # Goal Classification (question_Dp0v2q)
        if 'question_Dp0v2q' in field_map:
            goal_classification = field_map['question_Dp0v2q']['field']
            selected_values = goal_classification.get('value', [])
            options = goal_classification.get('options', [])
            
            # Map selected option IDs to text
            for option in options:
                if option.get('id') in selected_values:
                    option_text = option.get('text', '').lower()
                    if 'beginner' in option_text:
                        user_context['current_fitness_level'] = 'beginner'
                    elif 'intermediate' in option_text:
                        user_context['current_fitness_level'] = 'intermediate'
                    elif 'advanced' in option_text:
                        user_context['current_fitness_level'] = 'advanced'
                    elif 'weight loss' in option_text:
                        fitness_goals.append('weight loss')
                    elif 'mass gain' in option_text:
                        fitness_goals.append('muscle building')
                    elif 'nutrition' in option_text:
                        fitness_goals.append('nutrition improvement')
        
        # Activity Level (question_Ro8BKd)
        if 'question_Ro8BKd' in field_map:
            activity_field = field_map['question_Ro8BKd']['field']
            selected_values = activity_field.get('value', [])
            options = activity_field.get('options', [])
            
            for option in options:
                if option.get('id') in selected_values:
                    activity_text = option.get('text', '').lower()
                    if 'sedentary' in activity_text:
                        user_context['current_fitness_level'] = 'beginner'
                    elif 'lightly active' in activity_text:
                        user_context['current_fitness_level'] = 'beginner'
                    elif 'moderately active' in activity_text:
                        user_context['current_fitness_level'] = 'intermediate'
                    elif 'very active' in activity_text:
                        user_context['current_fitness_level'] = 'advanced'
        
        # Workout Frequency (question_NXNJbW)
        if 'question_NXNJbW' in field_map:
            try:
                frequency_value = field_map['question_NXNJbW']['value']
                user_context['workout_frequency'] = int(frequency_value) if frequency_value else 3
            except (ValueError, TypeError):
                user_context['workout_frequency'] = 3
        
        # Workout Duration (question_XoRVge)
        if 'question_XoRVge' in field_map:
            duration_field = field_map['question_XoRVge']['field']
            selected_values = duration_field.get('value', [])
            options = duration_field.get('options', [])
            
            for option in options:
                if option.get('id') in selected_values:
                    duration_text = option.get('text', '')
                    if '30 min' in duration_text:
                        user_context['workout_duration'] = 30
                    elif '45 min' in duration_text:
                        user_context['workout_duration'] = 45
                    elif '1 hour' in duration_text:
                        user_context['workout_duration'] = 60
        
        # Health Conditions/Limitations (question_BpLOg4)
        limitations = []
        if 'question_BpLOg4' in field_map:
            health_conditions = field_map['question_BpLOg4']['value']
            if health_conditions and str(health_conditions).strip():
                limitations.append(str(health_conditions))
                
        # Food Allergies (question_kG0Dpd)
        if 'question_kG0Dpd' in field_map:
            allergies = field_map['question_kG0Dpd']['value']
            if allergies and str(allergies).strip():
                limitations.append(f"Food allergies: {str(allergies)}")
        
        user_context['limitations_injuries'] = limitations
        
        # What's holding you back (question_a4jbkW)
        additional_info_parts = []
        if 'question_a4jbkW' in field_map:
            holding_back = field_map['question_a4jbkW']['value']
            if holding_back and str(holding_back).strip():
                additional_info_parts.append(f"What's holding back: {str(holding_back)}")
        
        # Habits to destroy (question_zMWB1q)
        if 'question_zMWB1q' in field_map:
            bad_habits = field_map['question_zMWB1q']['value']
            if bad_habits and str(bad_habits).strip():
                additional_info_parts.append(f"Habits to destroy: {str(bad_habits)}")
                
        # Habits to build (question_59E0pd)
        if 'question_59E0pd' in field_map:
            good_habits = field_map['question_59E0pd']['value']
            if good_habits and str(good_habits).strip():
                additional_info_parts.append(f"Habits to build: {str(good_habits)}")
        
        user_context['additional_info'] = '; '.join(additional_info_parts)
        
        # Set fitness goals if we extracted any
        if fitness_goals:
            user_context['fitness_goals'] = fitness_goals
        else:
            user_context['fitness_goals'] = ['general fitness']  # fallback
            
        # Set default workout types based on fitness level and goals
        workout_types = ['strength training']
        if 'weight loss' in user_context['fitness_goals']:
            workout_types.append('cardio')
        if user_context['current_fitness_level'] == 'beginner':
            workout_types.append('functional training')
            
        user_context['preferred_workout_types'] = workout_types
        
        logger.info(f"Extracted user context for {user_context['first_name']} {user_context['last_name']}: "
                   f"Age {user_context['age']}, {user_context['gender']}, "
                   f"{user_context['current_fitness_level']} level, "
                   f"{user_context['workout_frequency']}x/week, "
                   f"{user_context['workout_duration']}min workouts")
        return user_context
        
    except Exception as e:
        logger.error(f"Error extracting user context from Tally data: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

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

def get_active_clients():
    """Get list of active clients from Trainerize API"""
    try:
        payload = {
            "userID": 23372308,
            "view": "activeClient",
            "start": 0,
            "count": 100
        }
        
        logger.info("Fetching active clients from Trainerize API")
        logger.info(f"API Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            TRAINERIZE_CLIENT_LIST_URL,
            headers=TRAINERIZE_HEADERS,
            json=payload
        )
        
        logger.info(f"Trainerize client list API response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Successfully retrieved {len(result.get('users', []))} active clients")
            return result
        else:
            logger.error(f"Trainerize client list API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error calling Trainerize client list API: {str(e)}")
        return None

def send_weekly_checkin_messages(clients_data):
    """Send weekly check-in messages to all active clients"""
    try:
        if not clients_data or 'users' not in clients_data:
            logger.error("No clients data provided for mass messaging")
            return {"status": "error", "message": "No clients data provided"}
        
        users = clients_data.get('users', [])
        if not users:
            logger.warning("No active clients found for weekly check-in")
            return {"status": "success", "message": "No active clients to message", "clients_count": 0}
        
        # Extract user IDs and create recipient list
        recipients = []
        client_names = {}
        excluded_users = []
        
        for user in users:
            user_id = user.get('id')
            first_name = user.get('firstName', '')
            last_name = user.get('lastName', '')
            
            if user_id and user_id != 23372308:  # Exclude the trainer ID
                # Exclude specific user ID 23544758
                if user_id == 23544758:
                    excluded_users.append(f"{first_name} {last_name}".strip())
                    logger.info(f"Excluding user {user_id} ({first_name} {last_name}) from weekly check-in")
                    continue
                
                recipients.append(str(user_id))
                client_names[str(user_id)] = f"{first_name} {last_name}".strip()
        
        if not recipients:
            logger.warning("No valid recipients found for weekly check-in")
            return {"status": "success", "message": "No valid recipients found", "clients_count": 0}
        
        # Log excluded users for transparency
        if excluded_users:
            logger.info(f"Excluded users from weekly check-in: {excluded_users}")
        
        # Create personalized message body
        message_body = """Hey [Client Name]! Hope you had a great weekend. It's time for your quick weekly check-in so I can keep supporting you and making sure we're on track. Just reply directly to this message with your answers. short and honest is perfect!

How would you rate last week overall? (1–10)
How many workouts did you complete?
Did you stick to your nutrition plan 80% or more?
Any meals or situations where you felt off track?
How was your energy, mood, and sleep last week?
What was your biggest win?
What was your biggest challenge?
Anything you're feeling stuck or unsure about?
Anything you'd like to see more of in your plan?
Any questions, concerns, or feedback for me?"""
        
        # Create API payload for mass message
        payload = {
            "userID": 23372308,
            "recipients": recipients,
            "body": message_body,
            "type": "text",
            "threadType": "mainThread",
            "conversationType": "single"
        }
        
        logger.info(f"Sending weekly check-in messages to {len(recipients)} clients")
        logger.info(f"Recipients: {recipients}")
        logger.info(f"API Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            TRAINERIZE_MASS_MESSAGE_URL,
            headers=TRAINERIZE_HEADERS,
            json=payload
        )
        
        logger.info(f"Trainerize mass message API response status: {response.status_code}")
        logger.info(f"Trainerize mass message API response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Successfully sent weekly check-in messages to {len(recipients)} clients")
            return {
                "status": "success",
                "message": f"Successfully sent weekly check-in messages to {len(recipients)} clients",
                "clients_count": len(recipients),
                "recipients": recipients,
                "client_names": client_names,
                "excluded_users": excluded_users,
                "response": result
            }
        else:
            logger.error(f"Trainerize mass message API error: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "message": f"Trainerize mass message API error: {response.status_code}",
                "response_text": response.text
            }
            
    except Exception as e:
        logger.error(f"Error sending weekly check-in messages: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

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
            
            # Pass the raw Tally data directly to the orchestrator
            # The orchestrator will use parse_user_context() to properly create UserContext
            fitness_program = orchestrator.create_fitness_program(tally_data)
            
            logger.info(f"Generated fitness program with {len(fitness_program.focus_areas) if fitness_program else 0} focus areas")
                
        except Exception as e:
            logger.error(f"Error generating fitness program: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            fitness_program = None
        
        # Initialize results
        workout_results = []
        training_program_results = []
        
        # Only proceed with Trainerize operations if we have a user ID
        if user_id and fitness_program:
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
                if fitness_program and hasattr(fitness_program, 'exercise_matches'):
                    exercise_matches = fitness_program.exercise_matches
                
                if exercise_matches:
                    # Create a mapping of focus areas to training plan IDs
                    training_plan_ids = {}
                    for program_result in training_program_results:
                        if program_result.get('status') == 'success':
                            focus_area = program_result.get('focus_area', '')
                            training_plan_id = program_result.get('training_plan_id', '')
                            if focus_area and training_plan_id:
                                training_plan_ids[focus_area] = training_plan_id
                    
                    logger.info(f"Training plan ID mapping: {training_plan_ids}")
                    
                    # Create workouts with proper training plan ID mapping
                    workout_results = workout_creator.create_workouts_for_focus_areas(
                        user_id=user_id,
                        exercise_matches=exercise_matches,
                        user_context=fitness_program.user_context,
                        exercises_per_workout=5,
                        training_plan_ids=training_plan_ids
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

@app.route('/monday', methods=['POST'])
def monday_weekly_checkin():
    """Handle Monday weekly check-in for all active clients"""
    try:
        current_pid = os.getpid()
        logger.info(f"Starting Monday weekly check-in process in worker PID {current_pid}")
        
        # Check if this is a test mode request
        request_data = request.get_json() or {}
        test_mode = request_data.get('test_mode', False)
        target_user_id = request_data.get('target_user_id')
        target_user_name = request_data.get('target_user_name', 'Test User')
        
        if test_mode and target_user_id:
            logger.info(f"Test mode enabled - sending message only to {target_user_name} (ID: {target_user_id})")
            
            # Check if the target user is in the excluded list
            if target_user_id == "23544758":
                logger.warning(f"Test mode: Target user {target_user_name} (ID: {target_user_id}) is in excluded list")
                return jsonify({
                    "status": "warning",
                    "message": f"TEST MODE: Target user {target_user_name} (ID: {target_user_id}) is excluded from weekly check-ins",
                    "clients_count": 0,
                    "recipients": [],
                    "client_names": {},
                    "excluded_users": [target_user_name],
                    "test_mode": True,
                    "target_user": target_user_name,
                    "worker_pid": current_pid,
                    "timestamp": datetime.now().isoformat()
                }), 200
            
            # Create test client data structure
            test_clients_data = {
                "users": [
                    {
                        "id": int(target_user_id),
                        "firstName": target_user_name.split()[0] if ' ' in target_user_name else target_user_name,
                        "lastName": target_user_name.split()[1] if ' ' in target_user_name else "",
                        "email": "test@example.com",
                        "type": "client",
                        "status": "active"
                    }
                ],
                "total": 1
            }
            
            # Send test message
            message_result = send_weekly_checkin_messages(test_clients_data)
            
            # Prepare response
            response_data = {
                "status": message_result.get("status", "unknown"),
                "message": f"TEST MODE: {message_result.get('message', 'Unknown result')}",
                "clients_count": message_result.get("clients_count", 0),
                "recipients": message_result.get("recipients", []),
                "client_names": message_result.get("client_names", {}),
                "excluded_users": message_result.get("excluded_users", []),
                "test_mode": True,
                "target_user": target_user_name,
                "worker_pid": current_pid,
                "timestamp": datetime.now().isoformat()
            }
            
            if message_result.get("status") == "success":
                logger.info(f"TEST MODE: Successfully sent test message to {target_user_name} in worker PID {current_pid}")
                return jsonify(response_data), 200
            else:
                logger.error(f"TEST MODE: Failed to send test message to {target_user_name} in worker PID {current_pid}: {message_result.get('message')}")
                return jsonify(response_data), 500
        
        # Normal mode - get all active clients
        logger.info("Step 1: Fetching active clients...")
        clients_data = get_active_clients()
        
        if not clients_data:
            error_msg = "Failed to retrieve active clients from Trainerize"
            logger.error(error_msg)
            return jsonify({
                "status": "error",
                "message": error_msg,
                "worker_pid": current_pid,
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # Step 2: Send weekly check-in messages to all clients
        logger.info("Step 2: Sending weekly check-in messages...")
        message_result = send_weekly_checkin_messages(clients_data)
        
        # Prepare response
        response_data = {
            "status": message_result.get("status", "unknown"),
            "message": message_result.get("message", "Unknown result"),
            "clients_count": message_result.get("clients_count", 0),
            "recipients": message_result.get("recipients", []),
            "client_names": message_result.get("client_names", {}),
            "excluded_users": message_result.get("excluded_users", []),
            "worker_pid": current_pid,
            "timestamp": datetime.now().isoformat()
        }
        
        if message_result.get("status") == "success":
            logger.info(f"Successfully completed Monday weekly check-in for {message_result.get('clients_count', 0)} clients in worker PID {current_pid}")
            return jsonify(response_data), 200
        else:
            logger.error(f"Failed to complete Monday weekly check-in in worker PID {current_pid}: {message_result.get('message')}")
            return jsonify(response_data), 500
            
    except Exception as e:
        current_pid = os.getpid()
        logger.error(f"Error in Monday weekly check-in process in worker PID {current_pid}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "worker_pid": current_pid,
            "timestamp": datetime.now().isoformat()
        }), 500

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
            "monday_checkin": "/monday",
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