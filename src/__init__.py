"""
Fitness Program Generator Package

This package provides functionality to create personalized 16-week fitness programs
based on user form responses and vectorized exercise database searches.
"""

# Use absolute imports instead of relative imports
from user_context_parser import parse_user_context, UserContext, format_user_context_for_prompt
from exercise_generator import ExerciseGenerator, ExercisePrompt
from vector_search import VectorSearch
from fitness_program_orchestrator import FitnessProgramOrchestrator, FitnessProgram, create_fitness_program_from_json

__version__ = "1.0.0"
__author__ = "Boon Fay Fitness"

__all__ = [
    'parse_user_context',
    'UserContext', 
    'format_user_context_for_prompt',
    'ExerciseGenerator',
    'ExercisePrompt',
    'VectorSearch',
    'FitnessProgramOrchestrator',
    'FitnessProgram',
    'create_fitness_program_from_json'
] 