import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class UserContext:
    """Structured user context extracted from form response"""
    # Basic Information
    first_name: str
    last_name: str
    email: str
    phone: str
    social_handle: str
    address: str
    country: str
    
    # Physical Information
    date_of_birth: str
    sex_at_birth: str
    height: str
    weight: str
    age: int
    
    # Fitness Goals
    top_fitness_goal: str
    goal_classification: List[str]
    holding_back: str
    
    # Activity & Health
    activity_level: str
    health_conditions: str
    food_allergies: str
    
    # Nutrition
    daily_eating_pattern: str
    favorite_foods: str
    disliked_foods: str
    meals_per_day: str
    metabolism_rating: int
    nutrition_history: str
    macro_familiarity: int
    
    # Exercise
    exercise_days_per_week: int
    exercise_days: List[str]
    preferred_workout_length: str
    start_date: str
    
    # Habits
    habits_to_destroy: List[str]
    habits_to_build: List[str]

def extract_goal_classification(fields: List[Dict[str, Any]]) -> List[str]:
    """Extract goal classification from form fields"""
    for field in fields:
        if field.get('key') == 'question_Dp0v2q':
            value = field.get('value', [])
            options = field.get('options', [])
            
            # Map option IDs to text
            option_map = {opt['id']: opt['text'] for opt in options}
            return [option_map.get(v, v) for v in value]
    
    return []

def extract_exercise_days(fields: List[Dict[str, Any]]) -> List[str]:
    """Extract exercise days from form fields"""
    for field in fields:
        if field.get('key') == 'question_y40KG6':
            value = field.get('value', [])
            options = field.get('options', [])
            
            # Map option IDs to text
            option_map = {opt['id']: opt['text'] for opt in options}
            return [option_map.get(v, v) for v in value]
    
    return []

def extract_habits_to_destroy(fields: List[Dict[str, Any]]) -> List[str]:
    """Extract habits to destroy from form fields"""
    for field in fields:
        if field.get('key') == 'question_zMWB1q':
            value = field.get('value', '')
            if value:
                # Split by newlines and filter out empty strings
                habits = [habit.strip() for habit in value.split('\n') if habit.strip()]
                return habits
    return []

def extract_habits_to_build(fields: List[Dict[str, Any]]) -> List[str]:
    """Extract habits to build from form fields"""
    for field in fields:
        if field.get('key') == 'question_59E0pd':
            value = field.get('value', '')
            if value:
                # Split by newlines and filter out empty strings
                habits = [habit.strip() for habit in value.split('\n') if habit.strip()]
                return habits
    return []

def get_field_value(fields: List[Dict[str, Any]], key: str, default: Any = None) -> Any:
    """Helper function to extract field value by key"""
    for field in fields:
        if field.get('key') == key:
            return field.get('value', default)
    return default

def parse_user_context(json_input: Dict[str, Any]) -> UserContext:
    """Parse JSON input and extract user context for fitness program generation"""
    try:
        # Extract form fields
        data = json_input.get('data', {})
        fields = data.get('fields', [])
        
        # Extract basic information
        first_name = get_field_value(fields, 'question_zMWrpa', '')
        last_name = get_field_value(fields, 'question_59EG66', '')
        email = get_field_value(fields, 'question_QRxgjl', '')
        phone = get_field_value(fields, 'question_VPo1QE', '')
        social_handle = get_field_value(fields, 'question_erN1yJ', '')
        address = get_field_value(fields, 'question_d0Q2qq', '')
        country = get_field_value(fields, 'question_YGVzD5', '')
        
        # Extract physical information
        date_of_birth = get_field_value(fields, 'question_6K1b4o', '')
        sex_at_birth = get_field_value(fields, 'question_lOVlDB', '')
        height = get_field_value(fields, 'question_7KJBj6', '')
        weight = get_field_value(fields, 'question_be2Bg0', '')
        age = int(get_field_value(fields, 'question_Ap6oao', 0))
        
        # Extract fitness goals
        top_fitness_goal = get_field_value(fields, 'question_WReGQL', '')
        goal_classification = extract_goal_classification(fields)
        holding_back = get_field_value(fields, 'question_a4jbkW', '')
        
        # Extract activity & health
        activity_level = get_field_value(fields, 'question_Ro8BKd', '')
        health_conditions = get_field_value(fields, 'question_BpLOg4', '')
        food_allergies = get_field_value(fields, 'question_kG0Dpd', '')
        
        # Extract nutrition
        daily_eating_pattern = get_field_value(fields, 'question_vD07pX', '')
        favorite_foods = get_field_value(fields, 'question_KxP7gz', '')
        disliked_foods = get_field_value(fields, 'question_LKEAgz', '')
        meals_per_day = get_field_value(fields, 'question_po0jMy', '')
        metabolism_rating = int(get_field_value(fields, 'question_14bZx4', 5))
        nutrition_history = get_field_value(fields, 'question_MarkgE', '')
        macro_familiarity = int(get_field_value(fields, 'question_JlVagz', 1))
        
        # Extract exercise
        exercise_days_per_week = int(get_field_value(fields, 'question_gqQypM', 0))
        exercise_days = extract_exercise_days(fields)
        preferred_workout_length = get_field_value(fields, 'question_XoRVge', '')
        start_date = get_field_value(fields, 'question_oRlV6e', '')
        
        # Extract habits
        habits_to_destroy = extract_habits_to_destroy(fields)
        habits_to_build = extract_habits_to_build(fields)
        
        # Create UserContext object
        user_context = UserContext(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            social_handle=social_handle,
            address=address,
            country=country,
            date_of_birth=date_of_birth,
            sex_at_birth=sex_at_birth,
            height=height,
            weight=weight,
            age=age,
            top_fitness_goal=top_fitness_goal,
            goal_classification=goal_classification,
            holding_back=holding_back,
            activity_level=activity_level,
            health_conditions=health_conditions,
            food_allergies=food_allergies,
            daily_eating_pattern=daily_eating_pattern,
            favorite_foods=favorite_foods,
            disliked_foods=disliked_foods,
            meals_per_day=meals_per_day,
            metabolism_rating=metabolism_rating,
            nutrition_history=nutrition_history,
            macro_familiarity=macro_familiarity,
            exercise_days_per_week=exercise_days_per_week,
            exercise_days=exercise_days,
            preferred_workout_length=preferred_workout_length,
            start_date=start_date,
            habits_to_destroy=habits_to_destroy,
            habits_to_build=habits_to_build
        )
        
        logger.info(f"Successfully parsed user context for {user_context.first_name} {user_context.last_name}")
        return user_context
        
    except Exception as e:
        logger.error(f"Error parsing user context: {str(e)}")
        raise

def format_user_context_for_prompt(user_context: UserContext) -> str:
    """Format user context into a readable string for AI prompts"""
    context_parts = [
        f"Client: {user_context.first_name} {user_context.last_name}",
        f"Age: {user_context.age} | Height: {user_context.height} | Weight: {user_context.weight} lbs",
        f"Sex: {user_context.sex_at_birth}",
        f"Activity Level: {user_context.activity_level}",
        f"Top Fitness Goal: {user_context.top_fitness_goal}",
        f"Goal Classification: {', '.join(user_context.goal_classification)}",
        f"What's Holding Back: {user_context.holding_back}",
        f"Exercise Days: {user_context.exercise_days_per_week} days per week ({', '.join(user_context.exercise_days)})",
        f"Preferred Workout Length: {user_context.preferred_workout_length}",
        f"Metabolism Rating: {user_context.metabolism_rating}/10",
        f"Macro Familiarity: {user_context.macro_familiarity}/10",
        f"Health Conditions: {user_context.health_conditions}",
        f"Food Allergies: {user_context.food_allergies}",
        f"Daily Eating Pattern: {user_context.daily_eating_pattern}",
        f"Favorite Foods: {user_context.favorite_foods}",
        f"Disliked Foods: {user_context.disliked_foods}",
        f"Habits to Destroy: {', '.join(user_context.habits_to_destroy)}",
        f"Habits to Build: {', '.join(user_context.habits_to_build)}"
    ]
    
    return "\n".join(context_parts) 