import json
import logging
from typing import Dict, Any, List
from dataclasses import dataclass
import os

from fitness_focus_generator import FitnessFocusArea
from vector_search import VectorSearch

logger = logging.getLogger(__name__)

@dataclass
class FocusAreaExerciseMatch:
    """Represents a matched exercise for a focus area"""
    focus_area_name: str
    focus_area_description: str
    exercise_id: str
    exercise_name: str
    exercise_description: str
    exercise_category: str
    exercise_equipment: List[str]
    exercise_muscle_groups: List[str]
    exercise_difficulty: str
    match_score: float
    priority_level: int

class FocusAreaExerciseMatcher:
    """Matches exercises to fitness focus areas using vector search"""
    
    def __init__(self):
        self.vector_search = VectorSearch()
        logger.info("FocusAreaExerciseMatcher initialized")
    
    def match_exercises_to_focus_areas(self, focus_areas: List[FitnessFocusArea], exercises_per_area: int = 5) -> List[FocusAreaExerciseMatch]:
        """Match exercises to each focus area using vector search"""
        try:
            logger.info(f"Matching exercises to {len(focus_areas)} focus areas")
            
            all_matches = []
            
            for focus_area in focus_areas:
                logger.info(f"Searching exercises for focus area: {focus_area.area_name}")
                
                # Create search query for this focus area
                search_query = self._create_search_query_for_focus_area(focus_area)
                
                # Search for exercises
                search_results = self.vector_search.search_exercises(search_query, limit=exercises_per_area)
                
                # Convert results to FocusAreaExerciseMatch objects
                for result in search_results:
                    match = self._create_exercise_match(focus_area, result)
                    all_matches.append(match)
                
                logger.info(f"Found {len(search_results)} exercises for {focus_area.area_name}")
            
            logger.info(f"Total matches found: {len(all_matches)}")
            return all_matches
            
        except Exception as e:
            logger.error(f"Error matching exercises to focus areas: {str(e)}")
            return []
    
    def _create_search_query_for_focus_area(self, focus_area: FitnessFocusArea) -> str:
        """Create a search query based on the focus area characteristics"""
        
        # Build search terms from focus area
        search_terms = []
        
        # Add area name and description
        search_terms.append(focus_area.area_name)
        search_terms.append(focus_area.description)
        
        # Add target muscle groups
        search_terms.extend(focus_area.target_muscle_groups)
        
        # Add intensity level
        search_terms.append(focus_area.intensity_level)
        
        # Add special considerations
        if focus_area.special_considerations:
            search_terms.append(focus_area.special_considerations)
        
        # Add expected outcomes
        search_terms.extend(focus_area.expected_outcomes)
        
        # Add training frequency context
        search_terms.append(focus_area.training_frequency)
        
        # Create the final search query
        search_query = " ".join(search_terms)
        
        logger.debug(f"Search query for {focus_area.area_name}: {search_query}")
        return search_query
    
    def _create_exercise_match(self, focus_area: FitnessFocusArea, search_result: Dict[str, Any]) -> FocusAreaExerciseMatch:
        """Create a FocusAreaExerciseMatch from search result"""
        
        payload = search_result.get('payload', {})
        
        # Extract the correct exercise_id from the payload (not the Qdrant point ID)
        exercise_id = payload.get('exercise_id', '')
        if exercise_id:
            exercise_id = str(exercise_id)  # Convert to string for consistency
        else:
            logger.warning(f"No exercise_id found in payload for exercise: {payload.get('name', 'Unknown')}")
            exercise_id = ''
        
        return FocusAreaExerciseMatch(
            focus_area_name=focus_area.area_name,
            focus_area_description=focus_area.description,
            exercise_id=exercise_id,
            exercise_name=payload.get('name', ''),
            exercise_description=payload.get('description', ''),
            exercise_category=payload.get('category', ''),
            exercise_equipment=payload.get('equipment', []),
            exercise_muscle_groups=payload.get('muscle_groups', []),
            exercise_difficulty=payload.get('difficulty', ''),
            match_score=search_result.get('score', 0.0),
            priority_level=focus_area.priority_level
        )
    
    def group_matches_by_focus_area(self, matches: List[FocusAreaExerciseMatch]) -> Dict[str, List[FocusAreaExerciseMatch]]:
        """Group exercise matches by focus area"""
        grouped = {}
        
        for match in matches:
            area_name = match.focus_area_name
            if area_name not in grouped:
                grouped[area_name] = []
            grouped[area_name].append(match)
        
        # Sort exercises within each group by match score (highest first)
        for area_name in grouped:
            grouped[area_name].sort(key=lambda x: x.match_score, reverse=True)
        
        return grouped
    
    def export_matches_to_json(self, matches: List[FocusAreaExerciseMatch]) -> str:
        """Export exercise matches to JSON format"""
        try:
            matches_data = []
            
            for match in matches:
                match_dict = {
                    "focus_area_name": match.focus_area_name,
                    "focus_area_description": match.focus_area_description,
                    "exercise_id": match.exercise_id,
                    "exercise_name": match.exercise_name,
                    "exercise_description": match.exercise_description,
                    "exercise_category": match.exercise_category,
                    "exercise_equipment": match.exercise_equipment,
                    "exercise_muscle_groups": match.exercise_muscle_groups,
                    "exercise_difficulty": match.exercise_difficulty,
                    "match_score": match.match_score,
                    "priority_level": match.priority_level
                }
                matches_data.append(match_dict)
            
            return json.dumps(matches_data, indent=2)
            
        except Exception as e:
            logger.error(f"Error exporting matches to JSON: {str(e)}")
            return "[]"
    
    def create_weekly_exercise_plan(self, matches: List[FocusAreaExerciseMatch], exercise_days_per_week: int) -> Dict[str, Any]:
        """Create a weekly exercise plan based on matches and available days"""
        try:
            logger.info(f"Creating weekly exercise plan for {exercise_days_per_week} days")
            
            # Group matches by focus area
            grouped_matches = self.group_matches_by_focus_area(matches)
            
            # Create weekly plan structure
            weekly_plan = {
                "total_weeks": 16,
                "exercise_days_per_week": exercise_days_per_week,
                "focus_areas": [],
                "weekly_schedule": {}
            }
            
            # Add focus areas with their exercises
            for area_name, area_matches in grouped_matches.items():
                focus_area_data = {
                    "area_name": area_name,
                    "priority_level": area_matches[0].priority_level if area_matches else 1,
                    "description": area_matches[0].focus_area_description if area_matches else "",
                    "exercises": []
                }
                
                # Add exercises for this focus area
                for match in area_matches:
                    exercise_data = {
                        "exercise_id": match.exercise_id,
                        "exercise_name": match.exercise_name,
                        "exercise_description": match.exercise_description,
                        "exercise_category": match.exercise_category,
                        "exercise_equipment": match.exercise_equipment,
                        "exercise_muscle_groups": match.exercise_muscle_groups,
                        "exercise_difficulty": match.exercise_difficulty,
                        "match_score": match.match_score
                    }
                    focus_area_data["exercises"].append(exercise_data)
                
                weekly_plan["focus_areas"].append(focus_area_data)
            
            # Sort focus areas by priority
            weekly_plan["focus_areas"].sort(key=lambda x: x["priority_level"])
            
            # Create weekly schedule template
            for week in range(1, 17):  # 16 weeks
                weekly_plan["weekly_schedule"][f"week_{week}"] = {
                    "week_number": week,
                    "focus_areas": [],
                    "daily_exercises": {}
                }
                
                # Distribute focus areas across the week
                for day in range(1, exercise_days_per_week + 1):
                    weekly_plan["weekly_schedule"][f"week_{week}"]["daily_exercises"][f"day_{day}"] = []
            
            logger.info("Weekly exercise plan created successfully")
            return weekly_plan
            
        except Exception as e:
            logger.error(f"Error creating weekly exercise plan: {str(e)}")
            return {}
    
    def export_weekly_plan_to_json(self, weekly_plan: Dict[str, Any]) -> str:
        """Export weekly exercise plan to JSON format"""
        try:
            return json.dumps(weekly_plan, indent=2)
        except Exception as e:
            logger.error(f"Error exporting weekly plan to JSON: {str(e)}")
            return "{}" 