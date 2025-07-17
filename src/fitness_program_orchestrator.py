import json
import logging
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import os

# Use absolute imports instead of relative imports
from user_context_parser import parse_user_context, UserContext, format_user_context_for_prompt
from fitness_focus_generator import FitnessFocusGenerator, FitnessFocusArea
from focus_area_exercise_matcher import FocusAreaExerciseMatcher, FocusAreaExerciseMatch

logger = logging.getLogger(__name__)

@dataclass
class FitnessProgram:
    """Complete 16-week fitness program structure"""
    client_name: str
    program_name: str
    start_date: str
    total_weeks: int
    focus_areas: List[Dict[str, Any]]
    exercise_matches: List[Dict[str, Any]]
    weekly_plan: Dict[str, Any]
    created_at: str
    user_context: Dict[str, Any]

class FitnessProgramOrchestrator:
    """Main orchestrator for creating 16-week fitness programs"""
    
    def __init__(self):
        self.focus_generator = FitnessFocusGenerator()
        self.exercise_matcher = FocusAreaExerciseMatcher()
        logger.info("FitnessProgramOrchestrator initialized")
    
    def create_fitness_program(self, json_input: Dict[str, Any]) -> FitnessProgram:
        """Create a complete 16-week fitness program from JSON input"""
        try:
            logger.info("Starting fitness program creation")
            
            # Step 1: Parse user context from JSON input
            user_context = parse_user_context(json_input)
            logger.info(f"Parsed user context for {user_context.first_name} {user_context.last_name}")
            
            # Step 2: Generate 8 custom fitness focus areas using OpenAI
            focus_areas = self.focus_generator.generate_fitness_focus_areas(user_context)
            logger.info(f"Generated {len(focus_areas)} fitness focus areas")
            
            # Step 3: Match exercises to each focus area using vector search
            # Calculate exercises needed per focus area: exercise_days_per_week * 5 exercises per workout
            exercises_needed_per_area = user_context.exercise_days_per_week * 5
            exercise_matches = self.exercise_matcher.match_exercises_to_focus_areas(
                focus_areas,
                exercises_per_area=5,
                exercise_days_per_week=user_context.exercise_days_per_week
            )
            logger.info(f"Matched {len(exercise_matches)} exercises to focus areas (need {exercises_needed_per_area} per area for {user_context.exercise_days_per_week} workout days)")
            
            # Step 4: Create weekly exercise plan
            weekly_plan = self.exercise_matcher.create_weekly_exercise_plan(
                exercise_matches, 
                user_context.exercise_days_per_week
            )
            logger.info("Created weekly exercise plan")
            
            # Step 5: Create the complete fitness program
            fitness_program = self._create_program_structure(
                user_context, 
                focus_areas, 
                exercise_matches, 
                weekly_plan
            )
            
            logger.info("Fitness program creation completed successfully")
            return fitness_program
            
        except Exception as e:
            logger.error(f"Error creating fitness program: {str(e)}")
            raise
    
    def _create_program_structure(
        self, 
        user_context: UserContext, 
        focus_areas: List[FitnessFocusArea], 
        exercise_matches: List[FocusAreaExerciseMatch], 
        weekly_plan: Dict[str, Any]
    ) -> FitnessProgram:
        """Create the complete fitness program structure"""
        
        # Convert focus areas to dictionary format
        focus_areas_data = []
        for area in focus_areas:
            area_dict = {
                "area_name": area.area_name,
                "description": area.description,
                "priority_level": area.priority_level,
                "target_muscle_groups": area.target_muscle_groups,
                "training_frequency": area.training_frequency,
                "intensity_level": area.intensity_level,
                "special_considerations": area.special_considerations,
                "expected_outcomes": area.expected_outcomes
            }
            focus_areas_data.append(area_dict)
        
        # Convert exercise matches to dictionary format
        exercise_matches_data = []
        for match in exercise_matches:
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
            exercise_matches_data.append(match_dict)
        
        # Convert user context to dictionary
        user_context_dict = asdict(user_context)
        
        # Create fitness program
        fitness_program = FitnessProgram(
            client_name=f"{user_context.first_name} {user_context.last_name}",
            program_name=f"16-Week Transformation Program for {user_context.first_name}",
            start_date=user_context.start_date,
            total_weeks=16,
            focus_areas=focus_areas_data,
            exercise_matches=exercise_matches_data,
            weekly_plan=weekly_plan,
            created_at=datetime.now().isoformat(),
            user_context=user_context_dict
        )
        
        return fitness_program
    
    def export_program_to_json(self, fitness_program: FitnessProgram) -> str:
        """Export fitness program to JSON format"""
        try:
            program_dict = {
                "client_name": fitness_program.client_name,
                "program_name": fitness_program.program_name,
                "start_date": fitness_program.start_date,
                "total_weeks": fitness_program.total_weeks,
                "focus_areas": fitness_program.focus_areas,
                "exercise_matches": fitness_program.exercise_matches,
                "weekly_plan": fitness_program.weekly_plan,
                "created_at": fitness_program.created_at,
                "user_context": fitness_program.user_context
            }
            
            return json.dumps(program_dict, indent=2)
            
        except Exception as e:
            logger.error(f"Error exporting program to JSON: {str(e)}")
            return "{}"
    
    def print_program_summary(self, fitness_program: FitnessProgram):
        """Print a summary of the fitness program"""
        try:
            print("\n" + "="*60)
            print("🏋️ FITNESS PROGRAM SUMMARY")
            print("="*60)
            
            print(f"👤 Client: {fitness_program.client_name}")
            print(f"📅 Start Date: {fitness_program.start_date}")
            print(f"⏱️ Duration: {fitness_program.total_weeks} weeks")
            print(f"📊 Created: {fitness_program.created_at}")
        
            print(f"\n🎯 FOCUS AREAS ({len(fitness_program.focus_areas)}):")
            for i, area in enumerate(fitness_program.focus_areas, 1):
                print(f"  {i}. {area['area_name']} (Priority: {area['priority_level']})")
                print(f"     Description: {area['description']}")
                print(f"     Intensity: {area['intensity_level']}")
                print(f"     Frequency: {area['training_frequency']}")
                print()
            
            print(f"💪 EXERCISE MATCHES ({len(fitness_program.exercise_matches)}):")
            # Group by focus area
            grouped_matches = {}
            for match in fitness_program.exercise_matches:
                area_name = match['focus_area_name']
                if area_name not in grouped_matches:
                    grouped_matches[area_name] = []
                grouped_matches[area_name].append(match)
            
            for area_name, matches in grouped_matches.items():
                print(f"  📍 {area_name}:")
                for match in matches[:3]:  # Show top 3 exercises per area
                    print(f"    • {match['exercise_name']} (Score: {match['match_score']:.3f})")
                print()
            
            print("="*60)
            
        except Exception as e:
            logger.error(f"Error printing program summary: {str(e)}")

def create_fitness_program_from_json(json_input: Dict[str, Any]) -> FitnessProgram:
    """Create fitness program from JSON input using the orchestrator"""
    orchestrator = FitnessProgramOrchestrator()
    return orchestrator.create_fitness_program(json_input)

def main():
    """Main function for testing the orchestrator"""
    try:
        # Test with sample data
        sample_data = {
        "data": {
            "fields": [
                    {"key": "question_zMWrpa", "value": "Test"},
                    {"key": "question_59EG66", "value": "User"},
                    {"key": "question_WReGQL", "value": "Weight Loss"},
                    {"key": "question_gqQypM", "value": "3"},
                    {"key": "question_y40KG6", "value": ["Monday", "Wednesday", "Friday"]}
            ]
        }
    }
    
        orchestrator = FitnessProgramOrchestrator()
        program = orchestrator.create_fitness_program(sample_data)
        
        # Print summary
        orchestrator.print_program_summary(program)
        
        # Export to JSON
        json_output = orchestrator.export_program_to_json(program)
        print(f"\nJSON Output Length: {len(json_output)} characters")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main() 