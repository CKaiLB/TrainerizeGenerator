import os
import logging
from typing import List, Dict
import openai
from dotenv import load_dotenv
from dataclasses import dataclass

from user_context_parser import UserContext

load_dotenv()

logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

@dataclass
class ExercisePrompt:
    """Structured exercise prompt for a 2-week section"""
    section_name: str
    week_range: str
    focus_areas: List[str]
    intensity_level: str
    special_considerations: str
    prompt_text: str

class ExerciseGenerator:
    """Generates exercise prompts for 16-week fitness program sections"""
    
    def __init__(self):
        self.sections = [
            {
                "name": "Foundation & Assessment",
                "week_range": "Weeks 1-2",
                "focus": "Basic movement patterns, form assessment, establishing routine",
                "intensity": "Low to moderate",
                "considerations": "Focus on proper form and building confidence"
            },
            {
                "name": "Building Fundamentals",
                "week_range": "Weeks 3-4", 
                "focus": "Progressive overload, compound movements, endurance building",
                "intensity": "Moderate",
                "considerations": "Introduce more challenging variations"
            },
            {
                "name": "Strength Development",
                "week_range": "Weeks 5-6",
                "focus": "Strength training, muscle building, power development",
                "intensity": "Moderate to high",
                "considerations": "Focus on compound lifts and progressive overload"
            },
            {
                "name": "Metabolic Conditioning",
                "week_range": "Weeks 7-8",
                "focus": "Cardiovascular fitness, fat burning, metabolic efficiency",
                "intensity": "High",
                "considerations": "High-intensity intervals and circuit training"
            },
            {
                "name": "Advanced Strength",
                "week_range": "Weeks 9-10",
                "focus": "Advanced strength techniques, muscle hypertrophy, power",
                "intensity": "High",
                "considerations": "Complex movements and advanced techniques"
            },
            {
                "name": "Endurance & Stamina",
                "week_range": "Weeks 11-12",
                "focus": "Muscular endurance, cardiovascular stamina, work capacity",
                "intensity": "Moderate to high",
                "considerations": "Longer sets and extended cardio sessions"
            },
            {
                "name": "Peak Performance",
                "week_range": "Weeks 13-14",
                "focus": "Maximum performance, advanced techniques, competition prep",
                "intensity": "Very high",
                "considerations": "Peak intensity and advanced programming"
            },
            {
                "name": "Maintenance & Transition",
                "week_range": "Weeks 15-16",
                "focus": "Maintenance, skill refinement, program transition",
                "intensity": "Moderate",
                "considerations": "Sustain gains and prepare for next phase"
            }
        ]
    
    def generate_section_prompt(self, user_context: UserContext, section_index: int) -> ExercisePrompt:
        """Generate exercise prompt for a specific 2-week section"""
        if section_index >= len(self.sections):
            raise ValueError(f"Invalid section index: {section_index}")
        
        section = self.sections[section_index]
        
        # Create specialized prompt based on section
        prompt_text = self._create_section_prompt(user_context, section)
        
        return ExercisePrompt(
            section_name=section["name"],
            week_range=section["week_range"],
            focus_areas=section["focus"].split(", "),
            intensity_level=section["intensity"],
            special_considerations=section["considerations"],
            prompt_text=prompt_text
        )
    
    def _create_section_prompt(self, user_context: UserContext, section: Dict[str, str]) -> str:
        """Create specialized prompt for each section"""
        
        base_context = f"""
Client Profile:
- Name: {user_context.first_name} {user_context.last_name}
- Age: {user_context.age} | Height: {user_context.height} | Weight: {user_context.weight} lbs
- Sex: {user_context.sex_at_birth}
- Activity Level: {user_context.activity_level}
- Top Goal: {user_context.top_fitness_goal}
- Goal Classification: {', '.join(user_context.goal_classification)}
- Exercise Days: {user_context.exercise_days_per_week} days per week ({', '.join(user_context.exercise_days)})
- Preferred Workout Length: {user_context.preferred_workout_length}
- Health Conditions: {user_context.health_conditions}
- What's Holding Back: {user_context.holding_back}
- Metabolism Rating: {user_context.metabolism_rating}/10
- Macro Familiarity: {user_context.macro_familiarity}/10
"""
        
        section_specific_prompt = self._get_section_specific_prompt(section, user_context)
        
        return f"{base_context}\n{section_specific_prompt}"
    
    def _get_section_specific_prompt(self, section: Dict[str, str], user_context: UserContext) -> str:
        """Get section-specific prompt based on the 2-week period"""
        
        section_name = section["name"]
        week_range = section["week_range"]
        focus = section["focus"]
        intensity = section["intensity"]
        considerations = section["considerations"]
        
        if section_name == "Foundation & Assessment":
            return f"""
Section: {section_name} ({week_range})
Focus: {focus}
Intensity: {intensity}
Special Considerations: {considerations}

Generate 5 exercises that focus on:
1. Basic movement patterns (squat, hinge, push, pull, carry)
2. Form assessment and correction
3. Building confidence and establishing routine
4. Low-impact, beginner-friendly movements
5. Exercises that can be easily modified for the client's fitness level

Consider the client's health conditions and current activity level. Focus on exercises that will help establish a solid foundation for the 16-week program.
"""
        
        elif section_name == "Building Fundamentals":
            return f"""
Section: {section_name} ({week_range})
Focus: {focus}
Intensity: {intensity}
Special Considerations: {considerations}

Generate 5 exercises that focus on:
1. Progressive overload principles
2. Compound movements that engage multiple muscle groups
3. Building endurance and work capacity
4. Introducing more challenging variations of basic movements
5. Exercises that prepare for more advanced training

Focus on movements that will build strength and endurance while maintaining proper form.
"""
        
        elif section_name == "Strength Development":
            return f"""
Section: {section_name} ({week_range})
Focus: {focus}
Intensity: {intensity}
Special Considerations: {considerations}

Generate 5 exercises that focus on:
1. Primary compound lifts (squat, deadlift, bench press, overhead press)
2. Muscle building and hypertrophy
3. Power development and explosive movements
4. Progressive overload with heavier weights
5. Strength-specific training protocols

Emphasize proper form and technique while building strength. Consider the client's goals and current strength level.
"""
        
        elif section_name == "Metabolic Conditioning":
            return f"""
Section: {section_name} ({week_range})
Focus: {focus}
Intensity: {intensity}
Special Considerations: {considerations}

Generate 5 exercises that focus on:
1. High-intensity interval training (HIIT)
2. Fat burning and metabolic efficiency
3. Cardiovascular fitness improvement
4. Circuit training and supersets
5. Exercises that elevate heart rate and burn calories

Focus on movements that can be performed in intervals or circuits to maximize metabolic effect.
"""
        
        elif section_name == "Advanced Strength":
            return f"""
Section: {section_name} ({week_range})
Focus: {focus}
Intensity: {intensity}
Special Considerations: {considerations}

Generate 5 exercises that focus on:
1. Advanced strength techniques (drop sets, rest-pause, etc.)
2. Muscle hypertrophy and size gains
3. Power development and explosive strength
4. Complex movements and advanced variations
5. Strength-specific programming

Include advanced techniques and complex movements that challenge the client's current strength level.
"""
        
        elif section_name == "Endurance & Stamina":
            return f"""
Section: {section_name} ({week_range})
Focus: {focus}
Intensity: {intensity}
Special Considerations: {considerations}

Generate 5 exercises that focus on:
1. Muscular endurance and stamina
2. Cardiovascular endurance
3. Work capacity and conditioning
4. Longer duration sets and extended sessions
5. Exercises that build lasting endurance

Focus on movements that can be performed for longer durations to build endurance and stamina.
"""
        
        elif section_name == "Peak Performance":
            return f"""
Section: {section_name} ({week_range})
Focus: {focus}
Intensity: {intensity}
Special Considerations: {considerations}

Generate 5 exercises that focus on:
1. Maximum performance and peak intensity
2. Advanced techniques and complex movements
3. Competition preparation and peak conditioning
4. High-intensity training protocols
5. Exercises that push limits and maximize results

This is the most challenging phase - focus on exercises that will push the client to their peak performance level.
"""
        
        elif section_name == "Maintenance & Transition":
            return f"""
Section: {section_name} ({week_range})
Focus: {focus}
Intensity: {intensity}
Special Considerations: {considerations}

Generate 5 exercises that focus on:
1. Maintaining gains and progress
2. Skill refinement and technique improvement
3. Preparing for program transition
4. Sustainable training practices
5. Exercises that can be continued long-term

Focus on exercises that will help maintain progress while preparing for the next phase of training.
"""
        
        else:
            return f"""
Section: {section_name} ({week_range})
Focus: {focus}
Intensity: {intensity}
Special Considerations: {considerations}

Generate 5 exercises appropriate for this phase of the 16-week program.
"""

    def generate_all_section_prompts(self, user_context: UserContext) -> List[ExercisePrompt]:
        """Generate all 8 section prompts for the 16-week program"""
        prompts = []
        
        for i in range(8):
            try:
                prompt = self.generate_section_prompt(user_context, i)
                prompts.append(prompt)
                logger.info(f"Generated prompt for section {i+1}: {prompt.section_name}")
            except Exception as e:
                logger.error(f"Error generating prompt for section {i+1}: {str(e)}")
                raise
        
        return prompts 