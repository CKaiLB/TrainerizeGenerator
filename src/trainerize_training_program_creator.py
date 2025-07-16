import os
import json
import logging
import requests
from typing import Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TrainingProgram:
    """Represents a training program in Trainerize"""
    name: str
    instruction: str
    start_date: str
    end_date: str
    duration: int
    duration_type: str
    training_plan_id: str

class TrainerizeTrainingProgramCreator:
    """Creates training programs in Trainerize for each fitness focus area"""
    
    def __init__(self):
        self.api_url = os.environ.get('TRAINERIZE_PROGRAM_ADD')
        self.auth = os.environ.get('TRAINERIZE_AUTH')
        self.headers = {
            'accept': 'application/json',
            'authorization': self.auth,
            'content-type': 'application/json'
        }
        logger.info("TrainerizeTrainingProgramCreator initialized")
    
    def calculate_program_dates(self, user_start_date: str, focus_area_index: int) -> Dict[str, str]:
        """Calculate start and end dates for a training program based on focus area index"""
        try:
            # Parse user start date
            start_date = datetime.strptime(user_start_date, "%Y-%m-%d")
            
            # Calculate program start date (2 weeks per focus area)
            weeks_offset = focus_area_index * 2
            program_start_date = start_date + timedelta(weeks=weeks_offset)
            
            # Calculate program end date (2 weeks duration)
            program_end_date = program_start_date + timedelta(weeks=2)
            
            return {
                "start_date": program_start_date.strftime("%Y-%m-%d"),
                "end_date": program_end_date.strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            logger.error(f"Error calculating program dates: {str(e)}")
            # Fallback to current date
            current_date = datetime.now()
            return {
                "start_date": current_date.strftime("%Y-%m-%d"),
                "end_date": (current_date + timedelta(weeks=2)).strftime("%Y-%m-%d")
            }
    
    def create_training_program(self, user_id: str, focus_area: str, focus_area_index: int, user_start_date: str) -> Dict[str, Any]:
        """Create a training program in Trainerize for a specific focus area"""
        try:
            if not user_id:
                logger.error("No user ID provided for training program creation")
                return {"error": "No user ID provided", "status": "failed"}
            
            if not focus_area:
                logger.error("No focus area provided for training program creation")
                return {"error": "No focus area provided", "status": "failed"}
            
            # Calculate program dates
            dates = self.calculate_program_dates(user_start_date, focus_area_index)
            
            # Create program name with week range
            week_start = (focus_area_index * 2) + 1
            week_end = week_start + 1
            program_name = f"Week ({week_start}-{week_end})"
            
            # Create instruction based on focus area
            instruction = f"Focus on {focus_area}. This 2-week program is designed to help you achieve your fitness goals through targeted training and progressive overload."
            
            # Create API payload
            api_payload = {
                "plan": {
                    "name": program_name,
                    "instruction": instruction,
                    "startDate": dates["start_date"],
                    "durationType": "week",
                    "duration": 2,
                    "endDate": dates["end_date"]
                },
                "userid": user_id
            }
            
            logger.info(f"Creating training program for user {user_id}, focus area: {focus_area}")
            logger.info(f"API Payload: {json.dumps(api_payload, indent=2)}")
            
            # Make API call to Trainerize
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=api_payload
            )
            
            logger.info(f"Trainerize training program API response status: {response.status_code}")
            logger.info(f"Trainerize training program API response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                training_plan_id = result.get('id')
                
                if training_plan_id:
                    logger.info(f"Successfully created training program for user {user_id}, plan ID: {training_plan_id}")
                    return {
                        "status": "success",
                        "user_id": user_id,
                        "training_plan_id": training_plan_id,
                        "focus_area": focus_area,
                        "program_name": program_name,
                        "start_date": dates["start_date"],
                        "end_date": dates["end_date"],
                        "response": result
                    }
                else:
                    logger.error("No training plan ID returned in response")
                    return {
                        "error": "No training plan ID in response",
                        "status": "failed",
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
            logger.error(f"Error creating training program: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def create_training_programs_for_focus_areas(self, user_id: str, focus_areas: List[str], user_start_date: str) -> List[Dict[str, Any]]:
        """Create training programs for all focus areas"""
        try:
            if not user_id:
                logger.error("No user ID provided")
                return []
            
            if not focus_areas:
                logger.error("No focus areas provided")
                return []
            
            if not user_start_date:
                logger.error("No user start date provided")
                return []
            
            created_programs = []
            
            for index, focus_area in enumerate(focus_areas):
                logger.info(f"Creating training program for focus area {index + 1}: {focus_area}")
                
                result = self.create_training_program(user_id, focus_area, index, user_start_date)
                
                if result.get("status") == "success":
                    created_programs.append(result)
                    logger.info(f"Created training program: {result.get('program_name')} (ID: {result.get('training_plan_id')})")
                else:
                    logger.error(f"Failed to create training program for {focus_area}: {result.get('error')}")
            
            logger.info(f"Created {len(created_programs)} training programs for user {user_id}")
            return created_programs
            
        except Exception as e:
            logger.error(f"Error creating training programs for focus areas: {str(e)}")
            return []
    
    def export_training_program_results_to_json(self, training_program_results: List[Dict[str, Any]]) -> str:
        """Export training program creation results to JSON format"""
        try:
            return json.dumps(training_program_results, indent=2)
        except Exception as e:
            logger.error(f"Error exporting training program results to JSON: {str(e)}")
            return "[]" 