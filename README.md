# Fitness Program Generator

A comprehensive system for creating personalized 16-week fitness programs based on user form responses and vectorized exercise database searches.

## Architecture Overview

The system follows a modular architecture with four main components:

### 1. User Context Parser (`src/user_context_parser.py`)
- Parses JSON form responses from fitness assessment forms
- Extracts relevant user information (goals, health conditions, preferences, etc.)
- Structures data into a `UserContext` object for easy access

### 2. Exercise Generator (`src/exercise_generator.py`)
- Contains 8 different OpenAI-driven functions for each 2-week section
- Generates specialized prompts based on program progression
- Creates exercise prompts tailored to user context and program phase

### 3. Vector Search (`src/vector_search.py`)
- Searches the Qdrant vector database for relevant exercises
- Uses semantic similarity to find exercises matching AI-generated prompts
- Returns 5 most relevant exercises per section

### 4. Fitness Program Orchestrator (`src/fitness_program_orchestrator.py`)
- Coordinates all components to create complete 16-week programs
- Manages the entire pipeline from JSON input to final program
- Exports programs in structured JSON format

## Program Sections (16-Week Program)

The 16-week program is divided into 8 sections, each lasting 2 weeks:

1. **Foundation & Assessment** (Weeks 1-2)
   - Basic movement patterns, form assessment, establishing routine
   - Low to moderate intensity
   - Focus on proper form and building confidence

2. **Building Fundamentals** (Weeks 3-4)
   - Progressive overload, compound movements, endurance building
   - Moderate intensity
   - Introduce more challenging variations

3. **Strength Development** (Weeks 5-6)
   - Strength training, muscle building, power development
   - Moderate to high intensity
   - Focus on compound lifts and progressive overload

4. **Metabolic Conditioning** (Weeks 7-8)
   - Cardiovascular fitness, fat burning, metabolic efficiency
   - High intensity
   - High-intensity intervals and circuit training

5. **Advanced Strength** (Weeks 9-10)
   - Advanced strength techniques, muscle hypertrophy, power
   - High intensity
   - Complex movements and advanced techniques

6. **Endurance & Stamina** (Weeks 11-12)
   - Muscular endurance, cardiovascular stamina, work capacity
   - Moderate to high intensity
   - Longer sets and extended cardio sessions

7. **Peak Performance** (Weeks 13-14)
   - Maximum performance, advanced techniques, competition prep
   - Very high intensity
   - Peak intensity and advanced programming

8. **Maintenance & Transition** (Weeks 15-16)
   - Maintenance, skill refinement, program transition
   - Moderate intensity
   - Sustain gains and prepare for next phase

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# Core API Keys
export OPENAI_API_KEY="your-openai-api-key"
export QDRANT_URL="your-qdrant-url"
export QDRANT_API_KEY="your-qdrant-api-key"

# Trainerize API Configuration (Required)
export TRAINERIZE_AUTH="your-trainerize-auth-token"
export TRAINERIZE_FIND="your-trainerize-find-url"

# Trainerize API Endpoints (Optional - with defaults)
export TRAINERIZE_CLIENT_LIST_URL="https://api.trainerize.com/v03/user/getClientList"
export TRAINERIZE_MASS_MESSAGE_URL="https://api.trainerize.com/v03/message/sendMass"
export TRAINERIZE_PROGRAM_ADD="your-trainerize-program-add-url"
export TRAINERIZE_WORKOUT_ADD="your-trainerize-workout-add-url"

# Server Configuration
export PORT="6000"
```

**Note**: Copy `env_template.txt` to `.env` and fill in your actual values for easier configuration.

## Usage

### Basic Usage

```python
from src.fitness_program_orchestrator import create_fitness_program_from_json

# Load your JSON form response
with open('form_response.json', 'r') as f:
    json_input = json.load(f)

# Create the fitness program
fitness_program = create_fitness_program_from_json(json_input)

# Export to JSON
orchestrator = FitnessProgramOrchestrator()
json_output = orchestrator.export_program_to_json(fitness_program)
```

### Running the Demo

```bash
python main.py
```

This will:
1. Load an example JSON form response
2. Create a complete 16-week fitness program
3. Print a summary of the program
4. Save the program to `fitness_program_output.json`

## JSON Input Format

The system expects JSON input in this format:

```json
{
  "eventId": "unique-event-id",
  "eventType": "FORM_RESPONSE",
  "createdAt": "2025-07-03T17:47:46.443Z",
  "data": {
    "responseId": "response-id",
    "submissionId": "submission-id",
    "respondentId": "respondent-id",
    "formId": "form-id",
    "formName": "Boon Fay's 16-Week Transformation Program",
    "createdAt": "2025-07-03T17:47:46.000Z",
    "fields": [
      {
        "key": "question_zMWrpa",
        "label": "First Name",
        "type": "INPUT_TEXT",
        "value": "John"
      },
      {
        "key": "question_59EG66",
        "label": "Last Name",
        "type": "INPUT_TEXT",
        "value": "Doe"
      },
      {
        "key": "question_WReGQL",
        "label": "What is your top fitness goal?",
        "type": "INPUT_TEXT",
        "value": "To lose weight and build muscle"
      }
      // ... more fields
    ]
  }
}
```

## Output Format

The system generates a structured fitness program with:

- **Client Information**: Name, goals, health conditions, etc.
- **Program Details**: Start date, duration, sections
- **8 Program Sections**: Each with 5 exercises and metadata
- **Exercise Details**: Name, description, type, muscle groups, equipment, etc.
- **Relevance Scores**: How well each exercise matches the section requirements

## Key Features

### 1. Personalized Exercise Selection
- Uses vector similarity search to find exercises matching user context
- Considers health conditions, fitness level, and goals
- Adapts exercise selection based on program progression

### 2. Progressive Programming
- 8 distinct phases with increasing complexity
- Each section builds upon previous sections
- Maintains proper progression and safety

### 3. Comprehensive Exercise Database
- 650+ exercises from Trainerize API
- Vectorized for semantic search
- Rich metadata (muscle groups, equipment, difficulty, etc.)

### 4. Modular Architecture
- Easy to extend and modify
- Clear separation of concerns
- Testable components

## File Structure

```
├── main.py                          # Main application entry point
├── src/
│   ├── __init__.py                  # Package initialization
│   ├── user_context_parser.py       # JSON parsing and user context extraction
│   ├── exercise_generator.py        # AI-driven exercise prompt generation
│   ├── vector_search.py             # Qdrant vector database search
│   ├── fitness_program_orchestrator.py  # Main orchestrator
│   └── injest.py                    # Original exercise ingestion script
├── requirements.txt                 # Python dependencies
└── README.md                       # This file
```

## Environment Variables

Required environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key for AI-driven prompt generation
- `QDRANT_URL`: Your Qdrant vector database URL
- `QDRANT_API_KEY`: Your Qdrant API key

## Dependencies

- `openai`: For AI-driven exercise prompt generation
- `sentence-transformers`: For text embedding and vector search
- `qdrant-client`: For vector database operations
- `numpy`: For numerical operations
- `python-dotenv`: For environment variable management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions or support, please contact the development team. 