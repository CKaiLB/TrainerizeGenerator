#!/usr/bin/env python3
"""
Main application for the Fitness Program Generator

This script demonstrates how to use the new architecture to create
personalized 16-week fitness programs from JSON form responses.
"""

import json
import logging
import sys
import os
from typing import Dict, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.fitness_program_orchestrator import create_fitness_program_from_json, FitnessProgramOrchestrator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_example_json() -> Dict[str, Any]:
    """Load example JSON input for testing"""
    return {
        "eventId": "214f0ed8-9f45-47fe-b820-a33bd0032b70",
        "eventType": "FORM_RESPONSE",
        "createdAt": "2025-07-03T17:47:46.443Z",
        "data": {
            "responseId": "pbAxYky",
            "submissionId": "pbAxYky",
            "respondentId": "QZLVk1",
            "formId": "31Y66W",
            "formName": "Boon Fay's 16-Week Transformation Program",
            "createdAt": "2025-07-03T17:47:46.000Z",
            "fields": [
                {
                    "key": "question_zMWrpa",
                    "label": "First Name",
                    "type": "INPUT_TEXT",
                    "value": "Kai"
                },
                {
                    "key": "question_59EG66",
                    "label": "Last Name",
                    "type": "INPUT_TEXT",
                    "value": "Louie-Badua"
                },
                {
                    "key": "question_QRxgjl",
                    "label": "What is your email?",
                    "type": "INPUT_TEXT",
                    "value": "sweepautomation@gmail.com"
                },
                {
                    "key": "question_WReGQL",
                    "label": "What is your top fitness goal?",
                    "type": "INPUT_TEXT",
                    "value": "To lose weight"
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
                    "key": "question_a4jbkW",
                    "label": "What's holding you back?",
                    "type": "INPUT_TEXT",
                    "value": "giving in occasionally to breads chips and sweets."
                },
                {
                    "key": "question_lOVlDB",
                    "label": "Sex at Birth",
                    "type": "INPUT_TEXT",
                    "value": "male"
                },
                {
                    "key": "question_7KJBj6",
                    "label": "Height:",
                    "type": "INPUT_TEXT",
                    "value": "5'11"
                },
                {
                    "key": "question_be2Bg0",
                    "label": "Weight:",
                    "type": "INPUT_TEXT",
                    "value": "200"
                },
                {
                    "key": "question_Ap6oao",
                    "label": "Age:",
                    "type": "INPUT_TEXT",
                    "value": "50"
                },
                {
                    "key": "question_Ro8BKd",
                    "label": "What is your current activity level?",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["9eb5caae-0cf0-407c-9538-11654fb2076b"],
                    "options": [
                        {"id": "9eb5caae-0cf0-407c-9538-11654fb2076b", "text": "Sedentary"}
                    ]
                },
                {
                    "key": "question_BpLOg4",
                    "label": "Health conditions we should know about?",
                    "type": "TEXTAREA",
                    "value": "have low grade prostate cancer. I take thyroid medicine and high blood pressure medication and gout medicine and another medicine for prostate."
                },
                {
                    "key": "question_gqQypM",
                    "label": "How many days per week can you commit to exercise?",
                    "type": "INPUT_TEXT",
                    "value": "2"
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
                    "key": "question_XoRVge",
                    "label": "Preferred workout length:",
                    "type": "MULTIPLE_CHOICE",
                    "value": ["0de3cc6c-5754-4a90-90b3-54bbb09ced09"],
                    "options": [
                        {"id": "0de3cc6c-5754-4a90-90b3-54bbb09ced09", "text": "30 min"}
                    ]
                },
                {
                    "key": "question_14bZx4",
                    "label": "Rate your metabolism (1-10):",
                    "type": "LINEAR_SCALE",
                    "value": 5
                },
                {
                    "key": "question_JlVagz",
                    "label": "How familiar are you with counting macros?",
                    "type": "LINEAR_SCALE",
                    "value": 1
                },
                {
                    "key": "question_zMWB1q",
                    "label": "List 3 habits to DESTROY:",
                    "type": "TEXTAREA",
                    "value": "Impulsive eating\nImpulsive grocery shopping\nUsing being tired as an excuse to not exercise sometimes"
                },
                {
                    "key": "question_59E0pd",
                    "label": "List 3 habits to BUILD:",
                    "type": "TEXTAREA",
                    "value": "Exercising to build up muscle\nTrying to accomplish a task each day.\nTrying to cook more at home even though I'm not fond of cooking"
                }
            ]
        }
    }

def main():
    """Main function to demonstrate the fitness program generator"""
    print("🚀 Fitness Program Generator")
    print("=" * 50)
    
    try:
        # Load example JSON input
        json_input = load_example_json()
        print("✅ Loaded example JSON input")
        
        # Create fitness program
        print("\n🔄 Creating fitness program...")
        fitness_program = create_fitness_program_from_json(json_input)
        
        # Print summary
        orchestrator = FitnessProgramOrchestrator()
        orchestrator.print_program_summary(fitness_program)
        
        # Export to JSON
        json_output = orchestrator.export_program_to_json(fitness_program)
        
        # Save to file
        output_file = "fitness_program_output.json"
        with open(output_file, 'w') as f:
            f.write(json_output)
        
        print(f"\n💾 Program saved to: {output_file}")
        print(f"📊 Total sections: {len(fitness_program.sections)}")
        print(f"🏋️  Total exercises: {sum(len(section['exercises']) for section in fitness_program.sections)}")
        
        print("\n✅ Fitness program generation completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 