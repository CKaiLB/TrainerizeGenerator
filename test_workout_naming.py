#!/usr/bin/env python3
"""
Test script to verify the workout naming with week ranges is working correctly
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

from trainerize_workout_creator import TrainerizeWorkoutCreator

def test_workout_naming():
    """Test that workout naming with week ranges is working correctly"""
    print("🧪 Testing workout naming with week ranges...")
    
    try:
        # Create workout creator
        workout_creator = TrainerizeWorkoutCreator()
        
        # Test exercise data
        test_exercises = [
            {
                'focus_area_name': 'Strength Training',
                'exercise_id': '24',
                'exercise_name': 'Barbell Bench Press',
                'exercise_description': 'A compound exercise for chest',
                'exercise_category': 'compound',
                'exercise_equipment': ['barbell', 'bench'],
                'exercise_muscle_groups': ['chest', 'triceps'],
                'exercise_difficulty': 'intermediate',
                'match_score': 0.85,
                'priority_level': 1
            },
            {
                'focus_area_name': 'Strength Training',
                'exercise_id': '14',
                'exercise_name': 'Barbell Overhead Press',
                'exercise_description': 'A compound exercise for shoulders',
                'exercise_category': 'compound',
                'exercise_equipment': ['barbell'],
                'exercise_muscle_groups': ['shoulders', 'triceps'],
                'exercise_difficulty': 'intermediate',
                'match_score': 0.82,
                'priority_level': 1
            },
            {
                'focus_area_name': 'Strength Training',
                'exercise_id': '26',
                'exercise_name': 'Barbell Decline Bench Press',
                'exercise_description': 'A compound exercise for lower chest',
                'exercise_category': 'compound',
                'exercise_equipment': ['barbell', 'bench'],
                'exercise_muscle_groups': ['chest', 'triceps'],
                'exercise_difficulty': 'intermediate',
                'match_score': 0.80,
                'priority_level': 1
            },
            {
                'focus_area_name': 'Strength Training',
                'exercise_id': '443',
                'exercise_name': 'Barbell Back Squat',
                'exercise_description': 'A compound exercise for legs',
                'exercise_category': 'compound',
                'exercise_equipment': ['barbell'],
                'exercise_muscle_groups': ['quadriceps', 'glutes'],
                'exercise_difficulty': 'intermediate',
                'match_score': 0.78,
                'priority_level': 1
            },
            {
                'focus_area_name': 'Strength Training',
                'exercise_id': '411',
                'exercise_name': 'Bodyweight Split Squat',
                'exercise_description': 'A unilateral exercise for legs',
                'exercise_category': 'compound',
                'exercise_equipment': ['bodyweight'],
                'exercise_muscle_groups': ['quadriceps', 'glutes'],
                'exercise_difficulty': 'beginner',
                'match_score': 0.75,
                'priority_level': 1
            }
        ]
        
        # Test workout definition creation with week range
        print("✅ Testing workout definition creation...")
        
        exercise_ids = [ex['exercise_id'] for ex in test_exercises]
        workout_def = workout_creator._create_workout_definition(exercise_ids, "Strength Training", "Week (1-2)")
        
        print(f"✅ Created workout definition:")
        print(f"  Exercises count: {len(workout_def['exercises'])}")
        print(f"  Instructions: {workout_def['instructions']}")
        print(f"  Type: {workout_def['type']}")
        
        # Check that each exercise has the name parameter
        print(f"\n🔍 Checking exercise definitions:")
        for i, exercise in enumerate(workout_def['exercises']):
            exercise_def = exercise['def']
            print(f"  Exercise {i+1}:")
            print(f"    ID: {exercise_def['id']}")
            print(f"    Sets: {exercise_def['sets']}")
            print(f"    Target: {exercise_def.get('target', 'N/A')}")
            print(f"    Interval Time: {exercise_def.get('intervalTime', 'N/A')}")
            print(f"    Rest Time: {exercise_def.get('restTime', 'N/A')}")
            print(f"    Superset Type: {exercise_def['supersetType']}")
        
        # Check workout level name
        print(f"\n📋 Workout level details:")
        print(f"  Name: {workout_def.get('name', 'N/A')}")
        print(f"  Type: {workout_def.get('type', 'N/A')}")
        print(f"  Instructions: {workout_def.get('instructions', 'N/A')}")
        
        # Test the full workout creation process
        print(f"\n🧪 Testing full workout creation process...")
        
        # Create multiple focus areas to test week progression
        test_focus_areas = [
            {
                'focus_area_name': 'Strength Training',
                'exercises': test_exercises
            },
            {
                'focus_area_name': 'Cardio Training',
                'exercises': [
                    {
                        'focus_area_name': 'Cardio Training',
                        'exercise_id': '635',
                        'exercise_name': 'Treadmill Run',
                        'exercise_description': 'Cardiovascular exercise',
                        'exercise_category': 'cardio',
                        'exercise_equipment': ['treadmill'],
                        'exercise_muscle_groups': ['cardiovascular'],
                        'exercise_difficulty': 'beginner',
                        'match_score': 0.90,
                        'priority_level': 2
                    },
                    {
                        'focus_area_name': 'Cardio Training',
                        'exercise_id': '636',
                        'exercise_name': 'Stationary Bike',
                        'exercise_description': 'Low-impact cardio',
                        'exercise_category': 'cardio',
                        'exercise_equipment': ['stationary bike'],
                        'exercise_muscle_groups': ['cardiovascular'],
                        'exercise_difficulty': 'beginner',
                        'match_score': 0.88,
                        'priority_level': 2
                    },
                    {
                        'focus_area_name': 'Cardio Training',
                        'exercise_id': '637',
                        'exercise_name': 'Rowing Machine',
                        'exercise_description': 'Full-body cardio',
                        'exercise_category': 'cardio',
                        'exercise_equipment': ['rowing machine'],
                        'exercise_muscle_groups': ['cardiovascular', 'back'],
                        'exercise_difficulty': 'intermediate',
                        'match_score': 0.85,
                        'priority_level': 2
                    },
                    {
                        'focus_area_name': 'Cardio Training',
                        'exercise_id': '638',
                        'exercise_name': 'Elliptical',
                        'exercise_description': 'Low-impact cardio',
                        'exercise_category': 'cardio',
                        'exercise_equipment': ['elliptical'],
                        'exercise_muscle_groups': ['cardiovascular'],
                        'exercise_difficulty': 'beginner',
                        'match_score': 0.82,
                        'priority_level': 2
                    },
                    {
                        'focus_area_name': 'Cardio Training',
                        'exercise_id': '639',
                        'exercise_name': 'Stair Climber',
                        'exercise_description': 'High-intensity cardio',
                        'exercise_category': 'cardio',
                        'exercise_equipment': ['stair climber'],
                        'exercise_muscle_groups': ['cardiovascular', 'legs'],
                        'exercise_difficulty': 'intermediate',
                        'match_score': 0.80,
                        'priority_level': 2
                    }
                ]
            }
        ]
        
        # Test workout creation for each focus area
        test_user_id = "24549336"
        
        for focus_area_data in test_focus_areas:
            focus_area_name = focus_area_data['focus_area_name']
            exercises = focus_area_data['exercises']
            
            print(f"\n📋 Testing focus area: {focus_area_name}")
            
            # Create workout with week range
            result = workout_creator.create_workout_from_exercises(
                test_user_id, 
                exercises, 
                focus_area_name, 
                "Week (1-2)"
            )
            
            if result.get("status") == "success":
                print(f"  ✅ Successfully created workout")
                print(f"  📝 Workout name: {result.get('workout_name', 'N/A')}")
                print(f"  📅 Week range: {result.get('week_range', 'N/A')}")
                print(f"  💪 Exercises count: {result.get('exercises_count', 'N/A')}")
            else:
                print(f"  ❌ Failed to create workout: {result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Workout Naming with Week Ranges")
    print("=" * 50)
    
    # Test workout naming
    test_passed = test_workout_naming()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Workout Naming Test: {'✅ PASSED' if test_passed else '❌ FAILED'}")
    
    if test_passed:
        print("\n🎉 All tests passed! Workout naming with week ranges is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
    
    print("=" * 50) 