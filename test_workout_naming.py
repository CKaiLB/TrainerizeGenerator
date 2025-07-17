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

class DummyUserContext:
    def __init__(self, first_name, last_name, exercise_days_per_week=2, exercise_days=None):
        self.first_name = first_name
        self.last_name = last_name
        self.exercise_days_per_week = exercise_days_per_week
        self.exercise_days = exercise_days or ['Monday', 'Wednesday']


def test_workout_naming():
    """Test that workout naming uses '[user full name] day X' and is unique"""
    print("🧪 Testing workout naming with unique user day format...")
    try:
        workout_creator = TrainerizeWorkoutCreator()
        # Simulate user context
        user_context = DummyUserContext("Jane", "Doe", exercise_days_per_week=2, exercise_days=["Monday", "Wednesday"])
        # Create enough exercises for 2 focus areas, 2 days/week, 2 weeks, 5 exercises per workout
        exercises_per_workout = 5
        total_weeks = 2
        total_days = user_context.exercise_days_per_week * total_weeks
        # 2 focus areas
        focus_areas = ["Strength Training", "Cardio Training"]
        test_exercises = []
        for area in focus_areas:
            for i in range(total_days * exercises_per_workout):
                test_exercises.append({
                    'focus_area_name': area,
                    'exercise_id': f'{area[:2]}_{i}',
                    'exercise_name': f'{area} Exercise {i}',
                    'exercise_description': f'Description {i}',
                    'exercise_category': 'compound',
                    'exercise_equipment': ['dumbbell'],
                    'exercise_muscle_groups': ['muscle'],
                    'exercise_difficulty': 'beginner',
                    'match_score': 0.8,
                    'priority_level': 1
                })
        # Mix exercises for both focus areas
        all_exercises = test_exercises
        # Assign focus area to each exercise
        exercise_matches = all_exercises
        # Group by focus area for the test
        # Call the new logic
        results = workout_creator.create_workouts_for_focus_areas(
            user_id="12345",
            exercise_matches=exercise_matches,
            user_context=user_context,
            exercises_per_workout=exercises_per_workout,
            training_plan_ids=None
        )
        print(f"\nCreated {len(results)} workouts.")
        # Check for unique names and correct format
        names = set()
        for r in results:
            name = r.get('workout_name')
            print(f"  - {name}")
            assert name not in names, f"Duplicate workout name found: {name}"
            assert name.startswith("Jane Doe day "), f"Workout name does not start with user name: {name}"
            names.add(name)
        assert len(names) == len(results), "Workout names are not unique!"
        print("\n✅ All workout names are unique and follow the '[user full name] day X' format.")
        return True
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Workout Naming with Unique User Day Format")
    print("=" * 50)
    test_passed = test_workout_naming()
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Workout Naming Test: {'✅ PASSED' if test_passed else '❌ FAILED'}")
    if test_passed:
        print("\n🎉 All tests passed! Unique workout naming is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
    print("=" * 50) 