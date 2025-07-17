import os
import json
import logging
import time
from typing import Dict, Any, List
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv

from user_context_parser import UserContext

load_dotenv()

logger = logging.getLogger(__name__)

# Configure OpenAI with timeout
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=30.0  # 30 second timeout
)

@dataclass
class FitnessFocusArea:
    """Represents a custom fitness focus area"""
    area_name: str
    description: str
    priority_level: int  # 1-8, where 1 is highest priority
    target_muscle_groups: List[str]
    training_frequency: str
    intensity_level: str
    special_considerations: str
    expected_outcomes: List[str]

class FitnessFocusGenerator:
    """Generates 8 custom fitness focus areas based on user context"""
    
    def __init__(self):
        self.system_prompt = """You are an expert fitness coach and personal trainer with deep knowledge of exercise science, biomechanics, and program design. Your task is to analyze a client's profile and create 8 custom fitness focus areas that will form the foundation of their personalized 16-week transformation program.

For each focus area, consider:
1. The client's specific goals and current limitations
2. Their exercise experience and available time
3. Any health conditions or physical limitations
4. Their preferred workout style and intensity
5. Realistic progression and sustainability
6. Exercise ability disregarding nutrition

Return exactly 8 focus areas in JSON format with the following structure for each:
{
    "area_name": "Descriptive name of the fitness focus area",
    "description": "Detailed explanation of what this focus area entails",
    "priority_level": 1-8 (1 being highest priority),
    "target_muscle_groups": ["list", "of", "primary", "muscle", "groups"],
    "training_frequency": "How often this should be trained (e.g., '2-3 times per week')",
    "intensity_level": "Low/Moderate/High/Very High",
    "special_considerations": "Any specific considerations for this client",
    "expected_outcomes": ["list", "of", "expected", "results"]
}

Ensure the focus areas are:
- Personalized to the client's specific needs
- Realistic and achievable
- Complementary to each other
- Progressive in nature
- Sustainable long-term"""

    def generate_fitness_focus_areas(self, user_context: UserContext) -> List[FitnessFocusArea]:
        """Generate 8 custom fitness focus areas based on user context"""
        max_retries = 3
        retry_delay = 2
        for attempt in range(max_retries):
            try:
                logger.info(f"Generating fitness focus areas for {user_context.first_name} {user_context.last_name} (attempt {attempt + 1}/{max_retries})")
                
                # Create the user context prompt
                user_prompt = self._create_user_context_prompt(user_context)
                
                # Call OpenAI API using the new client with timeout
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                    timeout=25.0  #25second timeout for the request
                )
                
                # Extract and parse the response
                response_content = response.choices[0].message.content
                logger.info("Received response from OpenAI")
                
                # Parse the JSON response
                focus_areas_data = self._parse_openai_response(response_content)
                
                # Convert to FitnessFocusArea objects
                focus_areas = []
                for area_data in focus_areas_data:
                    focus_area = FitnessFocusArea(
                        area_name=area_data.get("area_name", ""),
                        description=area_data.get("description", ""),
                        priority_level=area_data.get("priority_level", 1),
                        target_muscle_groups=area_data.get("target_muscle_groups", []),
                        training_frequency=area_data.get("training_frequency", ""),
                        intensity_level=area_data.get("intensity_level", "Moderate"),
                        special_considerations=area_data.get("special_considerations", ""),
                        expected_outcomes=area_data.get("expected_outcomes", [])
                    )
                    focus_areas.append(focus_area)
                
                # Sort by priority level
                focus_areas.sort(key=lambda x: x.priority_level)
                
                logger.info(f"Generated {len(focus_areas)} fitness focus areas")
                return focus_areas
                
            except Exception as e:
                logger.error(f"Error generating fitness focus areas (attempt {attempt + 1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("All retry attempts failed, using default focus areas")
                    # Return default focus areas as fallback
                    return self._get_default_focus_areas(user_context)
    
    def _create_user_context_prompt(self, user_context: UserContext) -> str:
        """Create a detailed prompt with user context"""
        
        prompt = f"""
Please analyze this client's profile and create 8 custom fitness focus areas for their 16-week transformation program:

CLIENT PROFILE:
- Name: {user_context.first_name} {user_context.last_name}
- Age: {user_context.age} years old
- Height: {user_context.height}
- Weight: {user_context.weight} lbs
- Sex: {user_context.sex_at_birth}
- Activity Level: {user_context.activity_level}

FITNESS GOALS:
- Primary Goal: {user_context.top_fitness_goal}
- Goal Classification: {', '.join(user_context.goal_classification)}
- What's Holding Them Back: {user_context.holding_back}

EXERCISE PREFERENCES:
- Exercise Days: {user_context.exercise_days_per_week} days per week
- Preferred Days: {', '.join(user_context.exercise_days)}
- Preferred Workout Length: {user_context.preferred_workout_length}
- Start Date: {user_context.start_date}

HEALTH & NUTRITION:
- Health Conditions: {user_context.health_conditions}
- Food Allergies: {user_context.food_allergies}
- Daily Eating Pattern: {user_context.daily_eating_pattern}
- Metabolism Rating: {user_context.metabolism_rating}/10
- Macro Familiarity: {user_context.macro_familiarity}/10

HABITS:
- Habits to Destroy: {', '.join(user_context.habits_to_destroy)}
- Habits to Build: {', '.join(user_context.habits_to_build)}

Based on this comprehensive profile, create 8 custom fitness focus areas that will:
1. Address their specific goals and limitations
2. Build sustainable habits
3. Provide progressive challenges
4. Work within their time constraints
5. Consider their health conditions
6. Align with their preferences

Return the response as a valid JSON array with exactly 8 focus areas.
"""
        
        return prompt
    
    def _parse_openai_response(self, response_content: str) -> List[Dict[str, Any]]:
        """Parse the OpenAI response and extract the JSON data"""
        try:
            # Try to find JSON in the response
            start_idx = response_content.find('[')
            end_idx = response_content.rfind(']') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_content[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Try to find individual JSON objects
                import re
                json_pattern = r'\{[^{}]*\}'
                matches = re.findall(json_pattern, response_content)
                
                if matches:
                    focus_areas = []
                    for match in matches[:8]:  # Limit to 8
                        try:
                            area_data = json.loads(match)
                            focus_areas.append(area_data)
                        except json.JSONDecodeError:
                            continue
                    return focus_areas
                else:
                    raise ValueError("Could not parse JSON from response")
                    
        except Exception as e:
            logger.error(f"Error parsing OpenAI response: {str(e)}")
            logger.error(f"Response content: {response_content}")
            raise
    
    def _get_default_focus_areas(self, user_context: UserContext) -> List[FitnessFocusArea]:
        """Provide default focus areas as fallback"""
        logger.info("Using default focus areas as fallback")
        
        default_areas = [
            FitnessFocusArea(
                area_name="Foundation Building",
                description="Establish basic movement patterns and form",
                priority_level=1,
                target_muscle_groups=["Full Body"],
                training_frequency="2-3 times per week",
                intensity_level="Low to Moderate",
                special_considerations="Focus on proper form and building confidence",
                expected_outcomes=["Improved movement quality", "Increased confidence"]
            ),
            FitnessFocusArea(
                area_name="Strength Development",
                description="Build foundational strength through compound movements",
                priority_level=2,
                target_muscle_groups=["Legs", "Back", "Chest", "Shoulders"],
                training_frequency="2-3 times per week",
                intensity_level="Moderate",
                special_considerations="Progressive overload with proper form",
                expected_outcomes=["Increased strength", "Better muscle tone"]
            ),
            FitnessFocusArea(
                area_name="Cardiovascular Fitness",
                description="Improve heart health and endurance",
                priority_level=3,
                target_muscle_groups=["Cardiovascular System"],
                training_frequency="2-3 times per week",
                intensity_level="Moderate to High",
                special_considerations="Start with low impact options",
                expected_outcomes=["Improved endurance", "Better cardiovascular health"]
            ),
            FitnessFocusArea(
                area_name="Core Stability",
                description="Strengthen core muscles for better posture and stability",
                priority_level=4,
                target_muscle_groups=["Core", "Lower Back"],
                training_frequency="2-3 times per week",
                intensity_level="Moderate",
                special_considerations="Focus on controlled movements",
                expected_outcomes=["Better posture", "Improved stability"]
            ),
            FitnessFocusArea(
                area_name="Flexibility & Mobility",
                description="Improve range of motion and reduce injury risk",
                priority_level=5,
                target_muscle_groups=["Full Body"],
                training_frequency="2-3 times per week",
                intensity_level="Low",
                special_considerations="Gentle stretching and mobility work",
                expected_outcomes=["Increased flexibility", "Better range of motion"]
            ),
            FitnessFocusArea(
                area_name="Functional Movement",
                description="Train movements that translate to daily activities",
                priority_level=6,
                target_muscle_groups=["Full Body"],
                training_frequency="2 times per week",
                intensity_level="Moderate",
                special_considerations="Focus on real-world applications",
                expected_outcomes=["Better daily function", "Reduced injury risk"]
            ),
            FitnessFocusArea(
                area_name="Recovery & Regeneration",
                description="Optimize recovery for better performance",
                priority_level=7,
                target_muscle_groups=["Full Body"],
                training_frequency="Daily",
                intensity_level="Low",
                special_considerations="Gentle recovery techniques",
                expected_outcomes=["Faster recovery", "Better performance"]
            ),
            FitnessFocusArea(
                area_name="Mind-Body Connection",
                description="Develop awareness and control over movement",
                priority_level=8,
                target_muscle_groups=["Full Body"],
                training_frequency="2 times per week",
                intensity_level="Low to Moderate",
                special_considerations="Focus on mindfulness and control",
                expected_outcomes=["Better body awareness", "Improved movement quality"]
            )
        ]
        
        return default_areas
    
    def export_focus_areas_to_json(self, focus_areas: List[FitnessFocusArea]) -> str:
        """Export focus areas to JSON format"""
        try:
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
            
            return json.dumps(focus_areas_data, indent=2)
            
        except Exception as e:
            logger.error(f"Error exporting focus areas to JSON: {str(e)}")
            return "[]" 