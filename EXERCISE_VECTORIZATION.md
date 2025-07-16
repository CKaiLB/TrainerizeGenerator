# Trainerize Exercise Vectorization

This script fetches exercises from the Trainerize API (IDs 1-730) and vectorizes them into a Qdrant database for semantic search capabilities.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key

# Optional: Override default settings
COLLECTION_NAME=trainerize_exercises
```

### 3. Run the Script

```bash
# Run the full vectorization (exercises 1-730)
python src/injest.py

# Or run the test script first
python src/test_injest.py
```

## 📋 Features

### Core Functionality

- **API Integration**: Fetches exercises from Trainerize API using the existing authentication
- **Text Processing**: Converts exercise data into searchable text format
- **Vector Embedding**: Uses sentence-transformers to create semantic embeddings
- **Batch Processing**: Processes exercises in configurable batches
- **Error Handling**: Robust error handling with retry logic
- **Progress Tracking**: Detailed logging and progress reporting

### Exercise Data Processing

The script processes the following exercise fields:
- Name and description
- Instructions and form cues
- Category and muscle groups
- Equipment requirements
- Difficulty level
- Tags and variations

### Vector Search Capabilities

Once vectorized, you can search exercises using natural language:

```python
from injest import search_exercises

# Search for chest exercises
results = search_exercises("chest press exercises", limit=10)

# Search for beginner exercises
results = search_exercises("beginner friendly workouts", limit=5)

# Search for specific equipment
results = search_exercises("dumbbell exercises", limit=8)
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `QDRANT_URL` | Qdrant server URL | Required |
| `QDRANT_API_KEY` | Qdrant API key | Required |
| `COLLECTION_NAME` | Qdrant collection name | `trainerize_exercises` |

### Script Parameters

You can modify the script to change:

- **Exercise ID Range**: Edit the `fetch_and_vectorize_exercises(1, 730)` call
- **Batch Size**: Change `batch_size=5` in `batch_upload_exercises`
- **Model**: Change the sentence transformer model in the script
- **Collection Name**: Modify `COLLECTION_NAME` variable

## 📊 Usage Examples

### Basic Vectorization

```python
from injest import fetch_and_vectorize_exercises

# Vectorize exercises 1-100
fetch_and_vectorize_exercises(1, 100)

# Vectorize a specific range
fetch_and_vectorize_exercises(200, 300)
```

### Search Exercises

```python
from injest import search_exercises

# Find chest exercises
chest_exercises = search_exercises("chest press", limit=10)
for result in chest_exercises:
    print(f"{result['payload']['name']}: {result['score']:.3f}")

# Find beginner exercises
beginner_exercises = search_exercises("beginner friendly", limit=5)
```

### Test the System

```bash
# Run comprehensive tests
python src/test_injest.py

# Test specific functionality
python -c "
from injest import fetch_exercise_from_trainerize, prepare_exercise_text
exercise = fetch_exercise_from_trainerize(1)
if exercise:
    text = prepare_exercise_text(exercise)
    print(f'Exercise: {exercise.get(\"name\")}')
    print(f'Text: {text[:200]}...')
"
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python src/test_injest.py

# Expected output:
# 🚀 Starting Trainerize Exercise Vectorization Tests
# ============================================================
# ✅ Environment variables configured
# 
# ==================== Single Exercise Fetch ====================
# 🧪 Testing single exercise fetch...
# ✅ Successfully fetched exercise 1
# Name: Barbell Bench Press
# Category: compound
# Prepared text length: 245 characters
# Text preview: Exercise: Barbell Bench Press | Description: A compound exercise...
# ✅ Embedding created successfully (dimensions: 384)
# ✅ Single Exercise Fetch PASSED
```

### Test Individual Components

```python
# Test API connection
from injest import fetch_exercise_from_trainerize
exercise = fetch_exercise_from_trainerize(1)
print(f"API Test: {'✅' if exercise else '❌'}")

# Test text processing
from injest import prepare_exercise_text
text = prepare_exercise_text(exercise) if exercise else ""
print(f"Text Processing: {'✅' if text else '❌'}")

# Test embedding
from injest import create_exercise_embedding
embedding = create_exercise_embedding(text) if text else None
print(f"Embedding: {'✅' if embedding is not None else '❌'}")
```

## 📈 Performance

### Expected Performance

- **API Calls**: ~730 requests to Trainerize API
- **Processing Time**: ~15-30 minutes for full dataset
- **Memory Usage**: ~2-4GB RAM during processing
- **Storage**: ~50-100MB in Qdrant (depending on exercise data)

### Optimization Tips

1. **Batch Size**: Increase `batch_size` for faster processing (if memory allows)
2. **Parallel Processing**: Consider using `concurrent.futures` for API calls
3. **Caching**: Cache exercise data to avoid re-fetching
4. **Memory Management**: The script includes garbage collection for large datasets

## 🔍 Search Examples

### Common Search Queries

```python
# Find compound exercises
results = search_exercises("compound movements", limit=10)

# Find exercises for specific muscle groups
results = search_exercises("quadriceps exercises", limit=8)

# Find exercises by equipment
results = search_exercises("barbell exercises", limit=10)

# Find beginner-friendly exercises
results = search_exercises("beginner level", limit=5)

# Find advanced exercises
results = search_exercises("advanced difficulty", limit=5)
```

### Search Result Format

```python
[
    {
        "score": 0.892,
        "payload": {
            "exercise_id": 123,
            "name": "Barbell Bench Press",
            "category": "compound",
            "muscle_groups": ["chest", "triceps", "shoulders"],
            "equipment": ["barbell", "bench"],
            "difficulty": "intermediate",
            "text": "Exercise: Barbell Bench Press | Description: ...",
            "source": "trainerize_api",
            "uploaded_at": 1703123456.789
        },
        "id": "exercise_123"
    }
]
```

## 🚨 Troubleshooting

### Common Issues

1. **API Connection Errors**
   ```bash
   # Check network connectivity
   curl -X POST https://api.trainerize.com/v03/exercise/get \
     -H "Content-Type: application/json" \
     -H "Authorization: Basic NjMxOTMzOmU3TmlmSkRUVWlSQm5ydE0ycXlB" \
     -d '{"id": 1}'
   ```

2. **Qdrant Connection Issues**
   ```bash
   # Check Qdrant server
   curl http://localhost:6333/collections
   ```

3. **Memory Issues**
   - Reduce batch size in `batch_upload_exercises`
   - Process smaller ranges of exercises
   - Monitor memory usage during processing

4. **Model Loading Issues**
   ```bash
   # Reinstall sentence-transformers
   pip uninstall sentence-transformers
   pip install sentence-transformers
   ```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Logs

The script provides detailed logging:

```
2024-01-15 10:30:00 - INFO - Starting exercise vectorization from ID 1 to 730
2024-01-15 10:30:01 - INFO - Creating new collection 'trainerize_exercises'...
2024-01-15 10:30:02 - INFO - Collection 'trainerize_exercises' created successfully.
2024-01-15 10:30:03 - INFO - Fetching exercise 1/730
2024-01-15 10:30:04 - INFO - Successfully uploaded exercise 1: Barbell Bench Press
...
```

## 🔄 Maintenance

### Updating Exercise Data

To refresh the exercise database:

```python
# Clear existing collection
from qdrant_client import QdrantClient
client = QdrantClient(url="http://localhost:6333")
client.delete_collection("trainerize_exercises")

# Re-run vectorization
from injest import fetch_and_vectorize_exercises
fetch_and_vectorize_exercises(1, 730)
```

### Monitoring Collection Size

```python
from qdrant_client import QdrantClient
client = QdrantClient(url="http://localhost:6333")
collection_info = client.get_collection("trainerize_exercises")
print(f"Collection size: {collection_info.points_count} points")
```

## 📄 License

This script is part of the AI-powered fitness program generator project and follows the same licensing terms. 