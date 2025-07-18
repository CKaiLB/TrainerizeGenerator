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

# Circuit breaker for OpenAI API
_openai_failure_count = 0
_openai_last_failure_time = 0
_openai_circuit_breaker_threshold = 3  # Failures before circuit opens
_openai_circuit_breaker_timeout = 300  # 5 minutes before circuit resets

# Configure OpenAI with shorter timeout
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=10.0  # 10 second timeout for faster failure detection
)

@dataclass
class FitnessFocusArea:
    area_name: str
    description: str
    priority_level: int  # 1-8, where 1 is highest priority
    target_muscle_groups: List[str]
    training_frequency: str
    intensity_level: str
    special_considerations: str
    expected_outcomes: List[str]

class FitnessFocusGenerator:
    def __init__(self):
        self.system_prompt = (
            "You are an expert fitness coach and personal trainer with deep knowledge of exercise science, biomechanics, and program design. "
            "Your task is to analyze a client's profile and create 8 custom fitness focus areas that will form the foundation of their personalized 16-week transformation program.\n\n"
            "For each focus area, consider:\n"
            "1. The client's specific goals and current limitations\n"
            "2. Their exercise experience and available time\n"
            "3. Any health conditions or physical limitations\n"
            "4. Their preferred workout style and intensity\n"
            "5. Realistic progression and sustainability\n"
            "6. Exercise ability disregarding nutrition\n\n"
            "Return exactly 8 focus areas in JSON format with the following structure for each:\n"
            "{\n"
            "  \"area_name\": \"Descriptive name of the fitness focus area\",\n"
            "  \"description\": \"Detailed explanation of what this focus area entails\",\n"
            "  \"priority_level\": 1-8 (1 being highest priority),\n"
            "  \"target_muscle_groups\": [\"list\", \"of\", \"primary\", \"muscle\", \"groups\"],\n"
            "  \"training_frequency\": \"How often this should be trained (e.g., '2-3 times per week')\",\n"
            "  \"intensity_level\": \"Low/Moderate/High/Very High\",\n"
            "  \"special_considerations\": \"Any specific considerations for this client\",\n"
            "  \"expected_outcomes\": [\"list\", \"of\", \"expected\", \"results\"]\n"
            "}\n\n"
            "Ensure the focus areas are:\n"
            "- Personalized to the client's specific needs\n"
            "- Realistic and achievable\n"
            "- Complementary to each other\n"
            "- Progressive in nature\n"
            "- Sustainable long-term"
        )

    def _is_circuit_breaker_open(self) -> bool:
        global _openai_failure_count, _openai_last_failure_time
        current_time = time.time()
        # Reset circuit breaker if enough time has passed
        if current_time - _openai_last_failure_time > _openai_circuit_breaker_timeout:
            _openai_failure_count = 0
            return False
        # Circuit is open if failure count exceeds threshold
        return _openai_failure_count >= _openai_circuit_breaker_threshold

    def _record_openai_failure(self):
        global _openai_failure_count, _openai_last_failure_time
        _openai_failure_count += 1
        _openai_last_failure_time = time.time()
        logger.warning(f"OpenAI failure recorded. Total failures: {_openai_failure_count}")

    def generate_fitness_focus_areas(self, user_context: UserContext) -> List[FitnessFocusArea]:
        # Check circuit breaker first
        if self._is_circuit_breaker_open():
            logger.warning("OpenAI circuit breaker is open, using default focus areas")
            return self._get_default_focus_areas(user_context)
        max_retries = 2  # Reduced retries for faster failure
        retry_delay = 1
        for attempt in range(max_retries):
            try:
                logger.info(f"Generating fitness focus areas for {user_context.first_name} {user_context.last_name} (attempt {attempt + 1}/{max_retries})")
                # Create the user context prompt
                user_prompt = self._create_user_context_prompt(user_context)
                # Call OpenAI API with shorter timeout
                response = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                    timeout=30.0  # Increased timeout to 30 seconds
                )
                # Extract and parse the response
                response_content = response.choices[0].message.content
                logger.info(f"Received response from OpenAI")
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
                logger.error(f"Prompt: {user_prompt}")
                logger.error(f"Model: gpt-4.1-mini, Timeout: 30.0s")
                self._record_openai_failure()
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("All retry attempts failed, using default focus areas")
                    return self._get_default_focus_areas(user_context)

    def _create_user_context_prompt(self, user_context: UserContext) -> str:
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
7. Not focus on their nutrition

"Here are examples of good fitness focus areas:\n"
    "- Upper Body Push Strength (e.g., chest press, push-ups)\n"
    "- Lower Body Pull (e.g., deadlifts, hamstring curls)\n"
    "- Core Stability (e.g., planks, anti-rotation)\n"
    "- Hip Mobility (e.g., hip flexor stretches, dynamic lunges)\n"
    "- Shoulder Flexibility (e.g., band pull-aparts, wall slides)\n"
    "- Cardiovascular Endurance (e.g., treadmill, cycling)\n"
    "- Full Body Power (e.g., kettlebell swings, jump squats)\n"
    "- Balance and Coordination (e.g., single-leg balance, BOSU work)\n"
    "Avoid abstract or non-exercise-based focus areas like: 'Holistic Wellness', 'Lifestyle Optimization', 'Mindset Transformation', 'General Health'.\n"
    "Each focus area should be specific, actionable, and map to common exercise types, movement patterns, or muscle groups. Avoid abstract or overly broad categories.\n"

Return the response as a valid JSON array with exactly 8 focus areas. Try to not generate similar fitness focus areas but don't directly more than 3 examples.
"""
        return prompt

    def _parse_openai_response(self, response_content: str) -> List[Dict[str, Any]]:
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
        logger.info("Using default focus areas as fallback")
        default_areas = [
            FitnessFocusArea(
                area_name="Foundation Building",
                description="Establish basic movement patterns and form, focus on proper form and building confidence",
                priority_level=1,
                target_muscle_groups=["Full Body"],
                training_frequency="2 times per week",
                intensity_level="Low to Moderate",
                special_considerations="Focus on proper form and building confidence",
                expected_outcomes=["Improved movement quality", "Increased confidence"]
            ),
            FitnessFocusArea(
                area_name="Strength Development",
                description="Build foundational strength through compound movements, progressive overload with proper form",
                priority_level=2,
                target_muscle_groups=["Legs", "Back", "Chest", "Shoulders"],
                training_frequency="2 times per week",
                intensity_level="Moderate",
                special_considerations="Progressive overload with proper form",
                expected_outcomes=["Increased strength", "Better muscle tone"]
            ),
            FitnessFocusArea(
                area_name="Cardiovascular Fitness",
                description="Improve heart health and endurance, start with low impact options",
                priority_level=3,
                target_muscle_groups=["Cardiovascular System"],
                training_frequency="2 times per week",
                intensity_level="Moderate to High",
                special_considerations="Start with low impact options",
                expected_outcomes=["Improved endurance", "Better cardiovascular health"]
            ),
            FitnessFocusArea(
                area_name="Core Stability",
                description="Strengthen core muscles for better posture and stability, focus on controlled movements",
                priority_level=4,
                target_muscle_groups=["Core"],
                training_frequency="2 times per week",
                intensity_level="Moderate",
                special_considerations="Focus on controlled movements",
                expected_outcomes=["Better posture", "Improved stability"]
            ),
            FitnessFocusArea(
                area_name="Flexibility & Mobility",
                description="Improve range of motion and reduce injury risk, gentle stretching and mobility work",
                priority_level=5,
                target_muscle_groups=["Full Body"],
                training_frequency="2 times per week",
                intensity_level="Low",
                special_considerations="Gentle stretching and mobility work",
                expected_outcomes=["Increased flexibility", "Better range of motion"]
            ),
            FitnessFocusArea(
                area_name="Functional Movement",
                description="Train movements that translate to daily activities, focus on real-world applications",
                priority_level=6,
                target_muscle_groups=["Full Body"],
                training_frequency="2 times per week",
                intensity_level="Moderate",
                special_considerations="Focus on real-world applications",
                expected_outcomes=["Better daily function", "Reduced injury risk"]
            ),
            FitnessFocusArea(
                area_name="Recovery & Regeneration",
                description="Optimize recovery for better performance, gentle recovery techniques",
                priority_level=7,
                target_muscle_groups=["Full Body"],
                training_frequency="Daily",
                intensity_level="Low",
                special_considerations="Gentle recovery techniques",
                expected_outcomes=["Faster recovery", "Better performance"]
            ),
            FitnessFocusArea(
                area_name="Mind-Body Connection",
                description="Develop awareness and control over movement, focus on mindfulness and control",
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