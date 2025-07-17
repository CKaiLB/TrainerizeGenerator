import os
import json
import logging
import requests
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class WorkoutDefinition:
    """Represents a workout definition for Trainerize"""
    workout_name: str
    exercises: List[str]  # List of exercise IDs
    instructions: str
    focus_area: str

class TrainerizeWorkoutCreator:
    """Creates workouts in Trainerize using exercise IDs from Qdrant search"""
    
    def __init__(self):
        self.api_url = os.environ.get('TRAINERIZE_WORKOUT_ADD')
        self.auth = os.environ.get('TRAINERIZE_AUTH')
        self.headers = {
            'accept': 'application/json',
            'authorization': self.auth,
            'content-type': 'application/json'
        }
        logger.info("TrainerizeWorkoutCreator initialized")
    
    def create_workout_from_exercises(self, user_id: str, exercises: List[Dict[str, Any]], focus_area: str, workout_name: str, training_plan_id: str = None) -> Dict[str, Any]:
        """Create a workout in Trainerize from a list of exercises with a unique name. Ensures training plan ID is present if expected. (See LLM.txt)"""
        try:
            if not user_id:
                logger.error("No user ID provided for workout creation")
                return {"error": "No user ID provided", "status": "failed"}
            
            if not exercises or len(exercises) == 0:
                logger.error("No exercises provided for workout creation")
                return {"error": "No exercises provided", "status": "failed"}
            
            # Extract exercise IDs from the exercises (use exercise_id or id directly)
            exercise_ids = []
            for exercise in exercises:
                exercise_id = exercise.get('exercise_id') or exercise.get('id')
                if exercise_id:
                    exercise_ids.append(exercise_id)
                    logger.info(f"Added exercise ID: {exercise_id}")
                else:
                    logger.warning(f"Exercise {exercise.get('exercise_name', 'unknown')} has no exercise_id")
            
            if not exercise_ids:
                logger.error("No valid exercise IDs found in exercises")
                return {"error": "No valid exercise IDs found", "status": "failed"}
            
            # Create workout definition with unique name
            workout_def = self._create_workout_definition(exercise_ids, focus_area, workout_name)
            
            # Create the API payload (ensure userID is correct)
            api_payload = {
                "workoutDef": workout_def,
                "type": "mine",
                "userID": user_id
            }
            
            # Add training plan ID if provided
            if training_plan_id:
                api_payload["trainingPlanID"] = training_plan_id
                logger.info(f"Adding training plan ID: {training_plan_id} to workout payload")
            else:
                # LLM_NOTE: Flag if a workout is created without a training plan ID
                logger.error(f"Workout for user {user_id} and focus area '{focus_area}' is being created WITHOUT a training plan ID! This should be investigated.")
            
            logger.info(f"Creating workout for user {user_id} with {len(exercise_ids)} exercises")
            logger.info(f"API Payload: {json.dumps(api_payload, indent=2)}")
            
            # Make API call to Trainerize
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=api_payload
            )
            
            logger.info(f"Trainerize workout API response status: {response.status_code}")
            logger.info(f"Trainerize workout API response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully created workout for user {user_id}")
                # LLM_NOTE: Log confirmation that training plan ID was used
                if not training_plan_id:
                    logger.error(f"Workout created WITHOUT training plan ID! This is a critical issue.")
                else:
                    logger.info(f"Workout created and linked to training plan ID: {training_plan_id}")
                return {
                    "status": "success",
                    "user_id": user_id,
                    "workout_id": result.get('id'),
                    "exercises_count": len(exercise_ids),
                    "focus_area": focus_area,
                    "workout_name": workout_name,
                    "training_plan_id": training_plan_id,
                    "response": result
                }
            else:
                logger.error(f"Trainerize API error: {response.status_code} - {response.text}")
                return {
                    "error": f"Trainerize API error: {response.status_code}",
                    "status": "failed",
                    "response_text": response.text
                }
                
        except Exception as e:
            logger.error(f"Error creating workout: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def _create_workout_definition(self, exercise_ids: List[str], focus_area: str, workout_name: str) -> Dict[str, Any]:
        """Create the workout definition structure for Trainerize API with a unique name"""
        # LLM_NOTE: Changed to accept unique workout_name for Trainerize API uniqueness
        exercises = []
        for exercise_id in exercise_ids:
            exercise_def = {
                "def": {
                    "supersetType": "none",
                    "id": exercise_id,
                    "sets": 3,
                    "target": "10 reps",
                    "intervalTime": 30,
                    "restTime": 60
                }
            }
            exercises.append(exercise_def)
        workout_def = {
            "exercises": exercises,
            "instructions": f"Focus on {focus_area}. Complete all exercises with proper form and controlled movements.",
            "type": "workoutRegular",
            "name": workout_name
        }
        return workout_def

    def create_workouts_for_focus_areas(self, user_id: str, exercise_matches: List[Dict[str, Any]], user_context: Any, exercises_per_workout: int = 5, training_plan_ids: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """Create workouts for all focus areas, using unique user-specific workout names for each day (see LLM.txt)"""
        try:
            if not user_id:
                logger.error("No user ID provided")
                return []
            if not exercise_matches:
                logger.error("No exercise matches provided")
                return []
            exercise_days_per_week = getattr(user_context, 'exercise_days_per_week', 3)
            exercise_days = getattr(user_context, 'exercise_days', ['Monday', 'Wednesday', 'Friday'])
            first_name = getattr(user_context, 'first_name', 'User')
            last_name = getattr(user_context, 'last_name', '')
            logger.info(f"User can workout {exercise_days_per_week} days per week: {exercise_days}")
            # Convert exercise matches to dictionaries if they're objects
            exercise_matches_dict = []
            for match in exercise_matches:
                if hasattr(match, '__dict__'):
                    match_dict = {
                        'focus_area_name': getattr(match, 'focus_area_name', 'Unknown'),
                        'exercise_id': getattr(match, 'exercise_id', ''),
                        'exercise_name': getattr(match, 'exercise_name', ''),
                        'exercise_description': getattr(match, 'exercise_description', ''),
                        'exercise_category': getattr(match, 'exercise_category', ''),
                        'exercise_equipment': getattr(match, 'exercise_equipment', []),
                        'exercise_muscle_groups': getattr(match, 'exercise_muscle_groups', []),
                        'exercise_difficulty': getattr(match, 'exercise_difficulty', ''),
                        'match_score': getattr(match, 'match_score', 0.0),
                        'priority_level': getattr(match, 'priority_level', 1)
                    }
                    exercise_matches_dict.append(match_dict)
                else:
                    exercise_matches_dict.append(match)
            # Group exercises by focus area
            grouped_exercises = {}
            for match in exercise_matches_dict:
                focus_area = match.get('focus_area_name', 'Unknown')
                if focus_area not in grouped_exercises:
                    grouped_exercises[focus_area] = []
                grouped_exercises[focus_area].append(match)
            created_workouts = []
            total_weeks = 16
            total_days = exercise_days_per_week * total_weeks
            global_day_number = 1  # LLM_NOTE: Ensures unique workout names across all focus areas
            for focus_area, exercises in grouped_exercises.items():
                logger.info(f"Creating workouts for focus area: {focus_area}")
                # Get training plan ID for this focus area
                training_plan_id = None
                if training_plan_ids and focus_area in training_plan_ids:
                    training_plan_id = training_plan_ids[focus_area]
                    logger.info(f"Using training plan ID {training_plan_id} for focus area {focus_area}")
                for week in range(total_weeks):
                    for day_index in range(exercise_days_per_week):
                        # Calculate starting index for this day's exercises
                        start_index = (week * exercise_days_per_week + day_index) * exercises_per_workout
                        end_index = start_index + exercises_per_workout
                        day_exercises = exercises[start_index:end_index]
                        if len(day_exercises) < exercises_per_workout:
                            logger.warning(f"Not enough exercises for {focus_area} week {week+1} day {day_index+1}. Need {exercises_per_workout}, have {len(day_exercises)}")
                            continue
                        # Unique workout name: '[user full name] day X'
                        workout_name = f"{first_name} {last_name} day {global_day_number}"
                        result = self.create_workout_from_exercises(
                            user_id,
                            day_exercises,
                            focus_area,
                            workout_name,
                            training_plan_id
                        )
                        if result.get("status") == "success":
                            result["workout_name"] = workout_name
                            result["focus_area"] = focus_area
                            result["week_number"] = week + 1
                            result["day_of_week"] = exercise_days[day_index % len(exercise_days)]
                            result["global_day_number"] = global_day_number
                            created_workouts.append(result)
                            logger.info(f"Created workout: {workout_name}")
                        else:
                            logger.error(f"Failed to create workout for {workout_name}: {result.get('error')}")
                        global_day_number += 1
            logger.info(f"Created {len(created_workouts)} workouts for user {user_id}")
            return created_workouts
        except Exception as e:
            logger.error(f"Error creating workouts for focus areas: {str(e)}")
            return []
    
    def export_workout_results_to_json(self, workout_results: List[Dict[str, Any]]) -> str:
        """Export workout creation results to JSON format"""
        try:
            return json.dumps(workout_results, indent=2)
        except Exception as e:
            logger.error(f"Error exporting workout results to JSON: {str(e)}")
            return "[]" 