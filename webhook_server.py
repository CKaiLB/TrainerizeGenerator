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
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import using absolute imports to avoid relative import issues
from fitness_program_orchestrator import FitnessProgramOrchestrator
from trainerize_workout_creator import TrainerizeWorkoutCreator
from trainerize_training_program_creator import TrainerizeTrainingProgramCreator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# Trainerize API configuration
TRAINERIZE_API_URL = os.environ.get('TRAINERIZE_FIND')
TRAINERIZE_AUTH = os.environ.get('TRAINERIZE_AUTH')
TRAINERIZE_HEADERS = {
    'accept': 'application/json',
    'authorization': TRAINERIZE_AUTH,
    'content-type': 'application/json'
}

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
    """Process Tally webhook data and generate fitness program"""
    try:
        logger.info("Processing Tally webhook data")
        
        # Extract full name from Tally data
        full_name = extract_full_name_from_tally_data(tally_data)
        if not full_name:
            return {
                "error": "Could not extract full name from Tally data",
                "status": "failed"
            }
        
        logger.info(f"Extracted full name: {full_name}")
        
        # Wait 30 seconds as requested
        logger.info("Waiting 30 seconds before calling Trainerize API...")
        time.sleep(30)
        
        # Call Trainerize API to find user
        trainerize_result = find_user_in_trainerize(full_name)
        
        # Extract user ID from Trainerize response
        user_id = extract_user_id_from_trainerize_response(trainerize_result)
        logger.info(f"Final extracted user ID: {user_id}")
        
        # Generate fitness program using the orchestrator
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
            logger.info(f"Found {len(exercise_matches)} exercise matches for workout creation")
            
            if exercise_matches:
                # Get user context from the fitness program and create UserContext object
                user_context_dict = program_data.get("user_context", {})
                logger.info(f"User context dict: {user_context_dict}")
                
                # Create UserContext object from the dictionary
                from user_context_parser import UserContext
                user_context = UserContext(
                    first_name=user_context_dict.get('first_name', ''),
                    last_name=user_context_dict.get('last_name', ''),
                    email=user_context_dict.get('email', ''),
                    phone=user_context_dict.get('phone', ''),
                    social_handle=user_context_dict.get('social_handle', ''),
                    address=user_context_dict.get('address', ''),
                    country=user_context_dict.get('country', ''),
                    date_of_birth=user_context_dict.get('date_of_birth', ''),
                    sex_at_birth=user_context_dict.get('sex_at_birth', ''),
                    height=user_context_dict.get('height', ''),
                    weight=user_context_dict.get('weight', ''),
                    age=user_context_dict.get('age', 0),
                    top_fitness_goal=user_context_dict.get('top_fitness_goal', ''),
                    goal_classification=user_context_dict.get('goal_classification', []),
                    holding_back=user_context_dict.get('holding_back', ''),
                    activity_level=user_context_dict.get('activity_level', ''),
                    health_conditions=user_context_dict.get('health_conditions', ''),
                    food_allergies=user_context_dict.get('food_allergies', ''),
                    daily_eating_pattern=user_context_dict.get('daily_eating_pattern', ''),
                    favorite_foods=user_context_dict.get('favorite_foods', ''),
                    disliked_foods=user_context_dict.get('disliked_foods', ''),
                    meals_per_day=user_context_dict.get('meals_per_day', ''),
                    metabolism_rating=user_context_dict.get('metabolism_rating', 5),
                    nutrition_history=user_context_dict.get('nutrition_history', ''),
                    macro_familiarity=user_context_dict.get('macro_familiarity', 1),
                    exercise_days_per_week=user_context_dict.get('exercise_days_per_week', 3),
                    exercise_days=user_context_dict.get('exercise_days', ['Monday', 'Wednesday', 'Friday']),
                    preferred_workout_length=user_context_dict.get('preferred_workout_length', ''),
                    start_date=user_context_dict.get('start_date', ''),
                    habits_to_destroy=user_context_dict.get('habits_to_destroy', []),
                    habits_to_build=user_context_dict.get('habits_to_build', [])
                )
                
                # Create mapping of focus area names to training plan IDs
                training_plan_ids = {}
                for program_result in training_program_results:
                    if program_result.get("status") == "success":
                        focus_area = program_result.get("focus_area", "")
                        training_plan_id = program_result.get("training_plan_id", "")
                        if focus_area and training_plan_id:
                            training_plan_ids[focus_area] = training_plan_id
                            logger.info(f"Mapped focus area '{focus_area}' to training plan ID: {training_plan_id}")
                
                # Create workouts (5 exercises per workout) with user context and training plan IDs
                workout_results = workout_creator.create_workouts_for_focus_areas(
                    user_id, 
                    exercise_matches, 
                    user_context,  # Pass user context for exercise days
                    exercises_per_workout=5,
                    training_plan_ids=training_plan_ids  # Pass training plan IDs
                )
                logger.info(f"Created {len(workout_results)} workouts in Trainerize")
            else:
                logger.warning("No exercise matches found for workout creation")
        else:
            logger.warning("No user ID available for training program and workout creation")
        
        # Create enhanced response with focus areas, exercise matches, and workout results
        response_data = {
            "status": "success",
            "full_name": full_name,
            "user_id": user_id,
            "trainerize_result": trainerize_result,
            "fitness_program": program_data,
            "focus_areas": program_data.get("focus_areas", []),
            "exercise_matches": program_data.get("exercise_matches", []),
            "weekly_plan": program_data.get("weekly_plan", {}),
            "training_program_results": training_program_results,
            "workout_results": workout_results,
            "created_at": datetime.now().isoformat()
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {
            "error": str(e),
            "status": "failed"
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

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
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
    app.run(host='0.0.0.0', port=port, debug=True) 