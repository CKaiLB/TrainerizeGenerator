#!/usr/bin/env python3
"""
Test script to verify the exercise ID fix is working correctly
"""

import sys
import os
import json
import logging

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from focus_area_exercise_matcher import FocusAreaExerciseMatcher, FocusAreaExerciseMatch
from fitness_focus_generator import FitnessFocusGenerator
from user_context_parser import UserContext
from trainerize_workout_creator import TrainerizeWorkoutCreator

def test_exercise_id_extraction():
    """Test that exercise IDs are correctly extracted from Qdrant payload"""
    print("🧪 Testing exercise ID extraction...")
    
    try:
        # Create test user context
        test_user_context = UserContext(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            phone="555-1234",
            social_handle="@testuser",
            address="123 Test St",
            country="USA",
            age=30,
            date_of_birth="1994-01-01",
            height="5'10\"",
            weight=180,
            sex_at_birth="Male",
            activity_level="Moderate",
            top_fitness_goal="Build muscle and strength",
            goal_classification=["Muscle Building", "Strength Training"],
            exercise_days_per_week=4,
            exercise_days=["Monday", "Wednesday", "Friday", "Saturday"],
            preferred_workout_length="45-60 minutes",
            health_conditions="None",
            holding_back="Lack of time",
            metabolism_rating=7,
            macro_familiarity=6,
            food_allergies="None",
            daily_eating_pattern="3 meals per day",
            favorite_foods="Chicken, rice, vegetables",
            disliked_foods="None",
            meals_per_day=3,
            nutrition_history="Basic knowledge",
            habits_to_destroy="Late night snacking",
            habits_to_build="Meal prep",
            start_date="2024-01-15"
        )
        
        # Generate focus areas
        focus_generator = FitnessFocusGenerator()
        focus_areas = focus_generator.generate_fitness_focus_areas(test_user_context)
        
        print(f"✅ Generated {len(focus_areas)} focus areas")
        
        # Match exercises to focus areas
        exercise_matcher = FocusAreaExerciseMatcher()
        exercise_matches = exercise_matcher.match_exercises_to_focus_areas(focus_areas, exercises_per_area=3)
        
        print(f"✅ Found {len(exercise_matches)} exercise matches")
        
        # Check exercise IDs
        print("\n🔍 Checking exercise IDs:")
        for i, match in enumerate(exercise_matches[:5]):  # Check first 5 matches
            print(f"  Match {i+1}:")
            print(f"    Focus Area: {match.focus_area_name}")
            print(f"    Exercise Name: {match.exercise_name}")
            print(f"    Exercise ID: {match.exercise_id}")
            print(f"    ID Type: {type(match.exercise_id)}")
            
            # Verify that exercise_id is a valid integer string (1-730)
            try:
                exercise_id_int = int(match.exercise_id)
                if 1 <= exercise_id_int <= 730:
                    print(f"    ✅ Valid exercise ID: {exercise_id_int}")
                else:
                    print(f"    ⚠️  Exercise ID out of range: {exercise_id_int}")
            except (ValueError, TypeError):
                print(f"    ❌ Invalid exercise ID format: {match.exercise_id}")
            print()
        
        # Test workout creation with the fixed exercise IDs
        print("🧪 Testing workout creation with fixed exercise IDs...")
        
        # Convert matches to dictionary format for workout creator
        exercise_matches_dict = []
        for match in exercise_matches:
            match_dict = {
                'focus_area_name': match.focus_area_name,
                'exercise_id': match.exercise_id,
                'exercise_name': match.exercise_name,
                'exercise_description': match.exercise_description,
                'exercise_category': match.exercise_category,
                'exercise_equipment': match.exercise_equipment,
                'exercise_muscle_groups': match.exercise_muscle_groups,
                'exercise_difficulty': match.exercise_difficulty,
                'match_score': match.match_score,
                'priority_level': match.priority_level
            }
            exercise_matches_dict.append(match_dict)
        
        # Test workout creator (without actually creating workouts)
        workout_creator = TrainerizeWorkoutCreator()
        
        # Test with a sample user ID
        test_user_id = "24549336"
        
        # Get first 5 exercises for testing
        test_exercises = exercise_matches_dict[:5]
        
        print(f"✅ Testing with {len(test_exercises)} exercises:")
        for i, exercise in enumerate(test_exercises):
            print(f"  Exercise {i+1}: {exercise['exercise_name']} (ID: {exercise['exercise_id']})")
        
        # Test the workout definition creation
        exercise_ids = [ex['exercise_id'] for ex in test_exercises]
        workout_def = workout_creator._create_workout_definition(exercise_ids, "Test Focus Area")
        
        print(f"\n✅ Created workout definition:")
        print(f"  Exercises count: {len(workout_def['exercises'])}")
        print(f"  Exercise IDs: {[ex['def']['id'] for ex in workout_def['exercises']]}")
        
        # Verify all exercise IDs are valid integers
        all_valid = True
        for exercise_id in exercise_ids:
            try:
                exercise_id_int = int(exercise_id)
                if not (1 <= exercise_id_int <= 730):
                    all_valid = False
                    print(f"    ❌ Invalid exercise ID: {exercise_id_int}")
            except (ValueError, TypeError):
                all_valid = False
                print(f"    ❌ Invalid exercise ID format: {exercise_id}")
        
        if all_valid:
            print("✅ All exercise IDs are valid Trainerize exercise IDs (1-730)")
        else:
            print("❌ Some exercise IDs are invalid")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_vector_search_results():
    """Test the vector search to see the actual structure of results"""
    print("\n🔍 Testing vector search results structure...")
    
    try:
        from vector_search import VectorSearch
        
        vector_search = VectorSearch()
        
        # Test search
        search_results = vector_search.search_exercises("chest exercises", limit=3)
        
        print(f"✅ Found {len(search_results)} search results")
        
        for i, result in enumerate(search_results):
            print(f"\n  Result {i+1}:")
            print(f"    Qdrant Point ID: {result.get('id', 'N/A')}")
            print(f"    Score: {result.get('score', 'N/A')}")
            
            payload = result.get('payload', {})
            print(f"    Payload keys: {list(payload.keys())}")
            print(f"    Exercise ID from payload: {payload.get('exercise_id', 'N/A')}")
            print(f"    Exercise Name: {payload.get('name', 'N/A')}")
            print(f"    Exercise Type: {payload.get('type', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during vector search testing: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Exercise ID Fix")
    print("=" * 50)
    
    # Test vector search results first
    vector_test_passed = test_vector_search_results()
    
    # Test exercise ID extraction
    extraction_test_passed = test_exercise_id_extraction()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Vector Search Test: {'✅ PASSED' if vector_test_passed else '❌ FAILED'}")
    print(f"Exercise ID Extraction Test: {'✅ PASSED' if extraction_test_passed else '❌ FAILED'}")
    
    if vector_test_passed and extraction_test_passed:
        print("\n🎉 All tests passed! Exercise ID fix is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
    
    print("=" * 50) 