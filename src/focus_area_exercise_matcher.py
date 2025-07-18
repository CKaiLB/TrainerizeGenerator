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
    
    def match_exercises_to_focus_areas(self, focus_areas: List[FitnessFocusArea], exercises_per_area: int = 5, exercise_days_per_week: int = 3, level: str = None, main_muscle: str = None, equipment: str = None, force: str = None) -> List[FocusAreaExerciseMatch]:
        """Match exercises to each focus area using vector search and optional tag-based filtering"""
        try:
            logger.info(f"Matching exercises to {len(focus_areas)} focus areas")
            
            all_matches = []
            exercises_needed_per_area = exercise_days_per_week * exercises_per_area
            logger.info(f"Each focus area needs {exercises_needed_per_area} exercises (days/week={exercise_days_per_week}, exercises/workout={exercises_per_area})")
            
            for focus_area in focus_areas:
                logger.info(f"Searching exercises for focus area: {focus_area.area_name}")
                
                # Search without filters first to get semantic matches
                search_query = self._create_search_query_for_focus_area(focus_area)
                search_results = self.vector_search.search_exercises(
                    search_query,
                    limit=exercises_needed_per_area * 2  # Get more results to filter from
                )
                logger.info(f"Found {len(search_results)} initial exercises for {focus_area.area_name}")
                
                # Filter results in Python if filters are provided
                filtered_results = self._filter_results_by_tags(search_results, level, main_muscle, equipment, force)
                logger.info(f"After filtering: {len(filtered_results)} exercises for {focus_area.area_name}")
                
                # Take the required number of exercises
                final_results = filtered_results[:exercises_needed_per_area]
                
                for result in final_results:
                    match = self._create_exercise_match(focus_area, result)
                    all_matches.append(match)
                    
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
    
    def _filter_results_by_tags(self, search_results: List[Dict[str, Any]], level: str = None, main_muscle: str = None, equipment: str = None, force: str = None) -> List[Dict[str, Any]]:
        """Filter search results by tags in Python (since Qdrant doesn't have indexes on tag fields)"""
        if not any([level, main_muscle, equipment, force]):
            return search_results  # No filters to apply
        
        filtered_results = []
        
        for result in search_results:
            payload = result.get('payload', {})
            tags = payload.get('tags', {})
            
            # Check if exercise matches all provided filters
            matches_all_filters = True
            
            if level and 'level' in tags:
                if level not in tags['level']:
                    matches_all_filters = False
            
            if main_muscle and 'mainMuscle' in tags:
                if main_muscle not in tags['mainMuscle']:
                    matches_all_filters = False
            
            if equipment and 'equipment' in tags:
                if equipment not in tags['equipment']:
                    matches_all_filters = False
            
            if force and 'force' in tags:
                if force not in tags['force']:
                    matches_all_filters = False
            
            if matches_all_filters:
                filtered_results.append(result)
        
        logger.info(f"Filtered {len(search_results)} results to {len(filtered_results)} using Python filtering")
        return filtered_results
    
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
        
        # Handle the actual data structure from Qdrant
        # Tags are stored as a dictionary with arrays, e.g., {'mainMuscle': ['chest'], 'force': ['push']}
        tags = payload.get('tags', {})
        
        # Extract muscle groups from tags or main_muscle field
        muscle_groups = []
        if 'mainMuscle' in tags and tags['mainMuscle']:
            muscle_groups = tags['mainMuscle']
        elif payload.get('main_muscle'):
            muscle_groups = payload.get('main_muscle', [])
        
        # Extract equipment from tags or equipment field
        equipment = []
        if 'equipment' in tags and tags['equipment']:
            equipment = tags['equipment']
        elif payload.get('equipment'):
            equipment = payload.get('equipment', [])
        
        # Extract difficulty/level from tags or level field
        difficulty = ''
        if 'level' in tags and tags['level']:
            difficulty = tags['level'][0] if tags['level'] else ''
        elif payload.get('level'):
            difficulty = payload.get('level', [''])[0] if payload.get('level') else ''
        
        # Extract category from record_type
        category = payload.get('record_type', '')
        
        return FocusAreaExerciseMatch(
            focus_area_name=focus_area.area_name,
            focus_area_description=focus_area.description,
            exercise_id=exercise_id,
            exercise_name=payload.get('name', ''),
            exercise_description=payload.get('description', ''),
            exercise_category=category,
            exercise_equipment=equipment,
            exercise_muscle_groups=muscle_groups,
            exercise_difficulty=difficulty,
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

if __name__ == "__main__":
    # Practice/test: search for beginner, chest, dumbbell, push
    matcher = FocusAreaExerciseMatcher()
    class DummyFocusArea:
        area_name = "Push Strength"
        description = "Build upper body push strength"
        priority_level = 1
        target_muscle_groups = ["Chest"]
        training_frequency = "3x/week"
        intensity_level = "Beginner"
        special_considerations = "None"
        expected_outcomes = ["Strength"]
    focus_areas = [DummyFocusArea()]
    matches = matcher.match_exercises_to_focus_areas(
        focus_areas,
        exercises_per_area=5,
        exercise_days_per_week=3,
        level="beginner",
        main_muscle="chestInner",
        equipment="dumbbell",
        force="push"
    )
    print(f"Found {len(matches)} matches for practice focus area:")
    for m in matches:
        print(f"- {m.exercise_name} (ID: {m.exercise_id})") 