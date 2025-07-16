#!/usr/bin/env python3
"""
Test script for the new fitness focus area generation and exercise matching system
"""

import sys
import os
import json
import requests
import time

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Set mock OpenAI API key for testing
OPENAI_API_KEY= os.environ["OPENAI_API_KEY"]

from fitness_focus_generator import FitnessFocusGenerator
from focus_area_exercise_matcher import FocusAreaExerciseMatcher
from trainerize_workout_creator import TrainerizeWorkoutCreator
from user_context_parser import parse_user_context

def test_focus_area_generation():
    """Test the fitness focus area generation"""
    print("🧪 Testing Fitness Focus Area Generation")
    print("=" * 50)
    
    # Sample Tally data
    sample_tally_data = {
        "data": {
            "fields": [
                {
                    "key": "question_zMWrpa",
                    "label": "First Name",
                    "type": "INPUT_TEXT",
                    "value": "Timmy"
                },
                {
                    "key": "question_59EG66",
                    "label": "Last Name",
                    "type": "INPUT_TEXT",
                    "value": "Explorer"
                },
                {
                    "key": "question_WReGQL",
                    "label": "What is your top fitness goal?",
                    "type": "INPUT_TEXT",
                    "value": "To lose weight and build muscle"
                },
                {
                    "key": "question_Dp0v2q",
                    "label": "How would you classify this goal: ",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["b0ec82cd-4ce0-42e2-a1d2-b303478ff4cd"],
                    "options": [
                        {"id": "b0ec82cd-4ce0-42e2-a1d2-b303478ff4cd", "text": "Weight Loss"}
                    ]
                },
                {
                    "key": "question_gqQypM",
                    "label": "How many days per week can you commit to exercise?",
                    "type": "INPUT_TEXT",
                    "value": "3"
                },
                {
                    "key": "question_y40KG6",
                    "label": "Which days?",
                    "type": "CHECKBOXES",
                    "value": ["0e8844f7-96ac-4f46-a665-c0f2688bf004", "fa97315b-71f4-41f4-a078-0ea61b2ff5ac"],
                    "options": [
                        {"id": "0e8844f7-96ac-4f46-a665-c0f2688bf004", "text": "Saturday"},
                        {"id": "fa97315b-71f4-41f4-a078-0ea61b2ff5ac", "text": "Sunday"}
                    ]
                },
                {
                    "key": "question_Ap6oao",
                    "label": "Age",
                    "type": "INPUT_TEXT",
                    "value": "25"
                },
                {
                    "key": "question_7KJBj6",
                    "label": "Height",
                    "type": "INPUT_TEXT",
                    "value": "5'10\""
                },
                {
                    "key": "question_be2Bg0",
                    "label": "Weight",
                    "type": "INPUT_TEXT",
                    "value": "180"
                },
                {
                    "key": "question_lOVlDB",
                    "label": "Sex at Birth",
                    "type": "INPUT_TEXT",
                    "value": "Male"
                },
                {
                    "key": "question_Ro8BKd",
                    "label": "Activity Level",
                    "type": "INPUT_TEXT",
                    "value": "Moderate"
                },
                {
                    "key": "question_BpLOg4",
                    "label": "Health Conditions",
                    "type": "INPUT_TEXT",
                    "value": "None"
                },
                {
                    "key": "question_a4jbkW",
                    "label": "What's holding you back?",
                    "type": "INPUT_TEXT",
                    "value": "Lack of time and motivation"
                },
                {
                    "key": "question_XoRVge",
                    "label": "Preferred workout length",
                    "type": "INPUT_TEXT",
                    "value": "30-45 minutes"
                },
                {
                    "key": "question_oRlV6e",
                    "label": "Start date",
                    "type": "INPUT_TEXT",
                    "value": "2025-01-15"
                }
            ]
        }
    }
    
    try:
        # Parse user context
        user_context = parse_user_context(sample_tally_data)
        print(f"✅ Parsed user context for {user_context.first_name} {user_context.last_name}")
        
        # Generate focus areas
        focus_generator = FitnessFocusGenerator()
        focus_areas = focus_generator.generate_fitness_focus_areas(user_context)
        
        print(f"✅ Generated {len(focus_areas)} focus areas")
        
        # Print focus areas
        for i, area in enumerate(focus_areas, 1):
            print(f"\n{i}. {area.area_name} (Priority: {area.priority_level})")
            print(f"   Description: {area.description}")
            print(f"   Intensity: {area.intensity_level}")
            print(f"   Frequency: {area.training_frequency}")
            print(f"   Target Muscles: {', '.join(area.target_muscle_groups)}")
        
        # Export to JSON
        focus_areas_json = focus_generator.export_focus_areas_to_json(focus_areas)
        print(f"\n📊 Focus Areas JSON Length: {len(focus_areas_json)} characters")
        
        return focus_areas
        
    except Exception as e:
        print(f"❌ Error testing focus area generation: {str(e)}")
        return []

def test_exercise_matching(focus_areas):
    """Test the exercise matching system"""
    print("\n🧪 Testing Exercise Matching")
    print("=" * 50)
    
    if not focus_areas:
        print("❌ No focus areas to test with")
        return []
    
    try:
        # Create exercise matcher
        exercise_matcher = FocusAreaExerciseMatcher()
        
        # Match exercises to focus areas
        exercise_matches = exercise_matcher.match_exercises_to_focus_areas(focus_areas, exercises_per_area=5)
        
        print(f"✅ Matched {len(exercise_matches)} exercises to focus areas")
        
        # Group matches by focus area
        grouped_matches = exercise_matcher.group_matches_by_focus_area(exercise_matches)
        
        # Print matches
        for area_name, matches in grouped_matches.items():
            print(f"\n📍 {area_name}:")
            for i, match in enumerate(matches[:3], 1):  # Show top 3
                print(f"  {i}. {match.exercise_name} (Score: {match.match_score:.3f})")
                print(f"     Category: {match.exercise_category}")
                print(f"     Difficulty: {match.exercise_difficulty}")
        
        # Export to JSON
        matches_json = exercise_matcher.export_matches_to_json(exercise_matches)
        print(f"\n📊 Exercise Matches JSON Length: {len(matches_json)} characters")
        
        return exercise_matches
        
    except Exception as e:
        print(f"❌ Error testing exercise matching: {str(e)}")
        return []

def test_weekly_plan_creation(exercise_matches):
    """Test the weekly plan creation"""
    print("\n🧪 Testing Weekly Plan Creation")
    print("=" * 50)
    
    if not exercise_matches:
        print("❌ No exercise matches to test with")
        return {}
    
    try:
        # Create exercise matcher
        exercise_matcher = FocusAreaExerciseMatcher()
        
        # Create weekly plan (assuming 3 days per week)
        weekly_plan = exercise_matcher.create_weekly_exercise_plan(exercise_matches, exercise_days_per_week=3)
        
        print(f"✅ Created weekly plan with {len(weekly_plan.get('focus_areas', []))} focus areas")
        print(f"📅 Plan covers {weekly_plan.get('total_weeks', 0)} weeks")
        print(f"🏃 Exercise days per week: {weekly_plan.get('exercise_days_per_week', 0)}")
        
        # Export to JSON
        plan_json = exercise_matcher.export_weekly_plan_to_json(weekly_plan)
        print(f"\n📊 Weekly Plan JSON Length: {len(plan_json)} characters")
        
        return weekly_plan
        
    except Exception as e:
        print(f"❌ Error testing weekly plan creation: {str(e)}")
        return {}

def test_workout_creation(exercise_matches):
    """Test the Trainerize workout creation"""
    print("\n🧪 Testing Trainerize Workout Creation")
    print("=" * 50)
    
    if not exercise_matches:
        print("❌ No exercise matches to test with")
        return []
    
    try:
        # Create workout creator
        workout_creator = TrainerizeWorkoutCreator()
        
        # Mock user ID for testing
        mock_user_id = "24549336"
        
        # Create workouts (5 exercises per workout)
        workout_results = workout_creator.create_workouts_for_focus_areas(
            mock_user_id, 
            exercise_matches, 
            exercises_per_workout=5
        )
        
        print(f"✅ Created {len(workout_results)} workouts")
        
        # Print workout results
        for i, workout in enumerate(workout_results, 1):
            print(f"\n{i}. {workout.get('workout_name', 'Unknown Workout')}")
            print(f"   Status: {workout.get('status', 'Unknown')}")
            print(f"   Focus Area: {workout.get('focus_area', 'Unknown')}")
            print(f"   Exercises: {workout.get('exercises_count', 0)}")
            if workout.get('workout_id'):
                print(f"   Workout ID: {workout.get('workout_id')}")
        
        # Export to JSON
        workout_results_json = workout_creator.export_workout_results_to_json(workout_results)
        print(f"\n📊 Workout Results JSON Length: {len(workout_results_json)} characters")
        
        return workout_results
        
    except Exception as e:
        print(f"❌ Error testing workout creation: {str(e)}")
        return []

def test_webhook_integration():
    """Test the complete webhook integration"""
    print("\n🧪 Testing Webhook Integration")
    print("=" * 50)
    
    # Sample Tally webhook data
    sample_webhook_data = {
        "eventId": "test-focus-area-system",
        "eventType": "FORM_RESPONSE",
        "createdAt": "2025-01-15T10:00:00.000Z",
        "data": {
            "responseId": "test-response-focus",
            "submissionId": "test-submission-focus",
            "respondentId": "test-respondent-focus",
            "formId": "test-form-focus",
            "formName": "Boon Fay's 16-Week Transformation Program",
            "createdAt": "2025-01-15T10:00:00.000Z",
            "fields": [
                {
                    "key": "question_zMWrpa",
                    "label": "First Name",
                    "type": "INPUT_TEXT",
                    "value": "Timmy"
                },
                {
                    "key": "question_59EG66",
                    "label": "Last Name",
                    "type": "INPUT_TEXT",
                    "value": "Explorer"
                },
                {
                    "key": "question_WReGQL",
                    "label": "What is your top fitness goal?",
                    "type": "INPUT_TEXT",
                    "value": "To lose weight and build muscle"
                },
                {
                    "key": "question_Dp0v2q",
                    "label": "How would you classify this goal: ",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["b0ec82cd-4ce0-42e2-a1d2-b303478ff4cd"],
                    "options": [
                        {"id": "b0ec82cd-4ce0-42e2-a1d2-b303478ff4cd", "text": "Weight Loss"}
                    ]
                },
                {
                    "key": "question_gqQypM",
                    "label": "How many days per week can you commit to exercise?",
                    "type": "INPUT_TEXT",
                    "value": "3"
                },
                {
                    "key": "question_y40KG6",
                    "label": "Which days?",
                    "type": "CHECKBOXES",
                    "value": ["0e8844f7-96ac-4f46-a665-c0f2688bf004", "fa97315b-71f4-41f4-a078-0ea61b2ff5ac"],
                    "options": [
                        {"id": "0e8844f7-96ac-4f46-a665-c0f2688bf004", "text": "Saturday"},
                        {"id": "fa97315b-71f4-41f4-a078-0ea61b2ff5ac", "text": "Sunday"}
                    ]
                },
                {
                    "key": "question_Ap6oao",
                    "label": "Age",
                    "type": "INPUT_TEXT",
                    "value": "25"
                },
                {
                    "key": "question_7KJBj6",
                    "label": "Height",
                    "type": "INPUT_TEXT",
                    "value": "5'10\""
                },
                {
                    "key": "question_be2Bg0",
                    "label": "Weight",
                    "type": "INPUT_TEXT",
                    "value": "180"
                },
                {
                    "key": "question_lOVlDB",
                    "label": "Sex at Birth",
                    "type": "INPUT_TEXT",
                    "value": "Male"
                },
                {
                    "key": "question_Ro8BKd",
                    "label": "Activity Level",
                    "type": "INPUT_TEXT",
                    "value": "Moderate"
                },
                {
                    "key": "question_BpLOg4",
                    "label": "Health Conditions",
                    "type": "INPUT_TEXT",
                    "value": "None"
                },
                {
                    "key": "question_a4jbkW",
                    "label": "What's holding you back?",
                    "type": "INPUT_TEXT",
                    "value": "Lack of time and motivation"
                },
                {
                    "key": "question_XoRVge",
                    "label": "Preferred workout length",
                    "type": "INPUT_TEXT",
                    "value": "30-45 minutes"
                },
                {
                    "key": "question_oRlV6e",
                    "label": "Start date",
                    "type": "INPUT_TEXT",
                    "value": "2025-01-15"
                }
            ]
        }
    }
    
    webhook_url = "http://localhost:6000/webhook/tally"
    
    try:
        print("📤 Sending POST request to webhook...")
        
        # Send POST request to webhook
        response = requests.post(
            webhook_url,
            json=sample_webhook_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook test successful!")
            print(f"📊 Full name: {result.get('full_name', 'N/A')}")
            print(f"📊 User ID: {result.get('user_id', 'N/A')}")
            print(f"📊 Focus areas: {len(result.get('focus_areas', []))}")
            print(f"📊 Exercise matches: {len(result.get('exercise_matches', []))}")
            print(f"📊 Weekly plan sections: {len(result.get('weekly_plan', {}).get('focus_areas', []))}")
            print(f"📊 Workout results: {len(result.get('workout_results', []))}")
            
            # Print focus areas
            focus_areas = result.get('focus_areas', [])
            for i, area in enumerate(focus_areas[:3], 1):  # Show first 3
                print(f"\n{i}. {area.get('area_name', 'N/A')} (Priority: {area.get('priority_level', 'N/A')})")
                print(f"   Description: {area.get('description', 'N/A')}")
                print(f"   Intensity: {area.get('intensity_level', 'N/A')}")
            
            # Print workout results
            workout_results = result.get('workout_results', [])
            for i, workout in enumerate(workout_results[:3], 1):  # Show first 3
                print(f"\nWorkout {i}: {workout.get('workout_name', 'N/A')}")
                print(f"   Status: {workout.get('status', 'N/A')}")
                print(f"   Focus Area: {workout.get('focus_area', 'N/A')}")
                print(f"   Exercises: {workout.get('exercises_count', 'N/A')}")
            
        else:
            print(f"❌ Webhook test failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to webhook server. Make sure it's running on localhost:6000")
    except Exception as e:
        print(f"❌ Error testing webhook: {str(e)}")

def main():
    """Main test function"""
    print("🚀 Testing New Fitness Focus Area System")
    print("=" * 60)
    
    # Test focus area generation
    focus_areas = test_focus_area_generation()
    
    # Test exercise matching
    exercise_matches = test_exercise_matching(focus_areas)
    
    # Test weekly plan creation
    weekly_plan = test_weekly_plan_creation(exercise_matches)
    
    # Test workout creation
    workout_results = test_workout_creation(exercise_matches)
    
    # Test webhook integration
    test_webhook_integration()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main() 