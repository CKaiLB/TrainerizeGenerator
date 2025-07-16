# Fitness Program Generator Webhook

This webhook server processes Tally survey responses and generates personalized 16-week fitness programs.

## System Overview

The webhook system works as follows:

1. **Receives Tally Survey Data**: Accepts JSON webhook from Tally forms
2. **Extracts User Information**: Parses first name, last name, and fitness goals
3. **Waits 30 Seconds**: As requested for processing time
4. **Calls Trainerize API**: Searches for the user in Trainerize system
5. **Generates Fitness Program**: Creates a personalized 16-week program using AI
6. **Returns Results**: Provides the complete fitness program as JSON

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key_here
QDRANT_URL=your_qdrant_url_here
QDRANT_API_KEY=your_qdrant_api_key_here
```

### 3. Start the Webhook Server

```bash
python webhook_server.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### POST /webhook/tally
Main webhook endpoint that accepts Tally survey data.

**Request Body**: Tally survey JSON (see example below)

**Response**: 
```json
{
  "status": "success",
  "full_name": "Kai Louie-Badua",
  "trainerize_result": {...},
  "fitness_program": {...},
  "created_at": "2025-07-12T11:47:35.259Z"
}
```

### GET /health
Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-12T11:47:35.259Z"
}
```

### GET /
Root endpoint with service information.

## Example Tally Webhook Data

```json
{
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
        "key": "question_WReGQL",
        "label": "What is your top fitness goal?",
        "type": "INPUT_TEXT",
        "value": "To lose weight"
      }
    ]
  }
}
```

## Testing

### Test the Webhook Server

```bash
python test_webhook.py
```

This will test both the health check and webhook endpoints.

### Manual Testing with curl

```bash
curl -X POST http://localhost:5000/webhook/tally \
  -H "Content-Type: application/json" \
  -d @sample_tally_data.json
```

## Integration with Tally

1. **Configure Tally Webhook**: In your Tally form settings, add the webhook URL:
   ```
   http://your-server.com/webhook/tally
   ```

2. **Set Webhook Method**: Configure Tally to send POST requests with JSON data

3. **Test the Integration**: Submit a test form to verify the webhook is working

## System Architecture

```
Tally Form → Webhook Server → Trainerize API → AI Generator → Qdrant Search → Response
```

### Components:

- **Flask Web Server**: Handles HTTP requests and responses
- **Tally Data Parser**: Extracts user information from survey responses
- **Trainerize API Client**: Searches for users in the Trainerize system
- **Fitness Program Orchestrator**: Generates personalized fitness programs
- **Vector Search**: Finds relevant exercises using AI embeddings

## Error Handling

The webhook server includes comprehensive error handling:

- **Invalid JSON**: Returns 400 Bad Request
- **Missing Required Fields**: Returns 500 with error details
- **API Failures**: Logs errors and returns appropriate status codes
- **Timeout Handling**: Manages long-running operations gracefully

## Logging

The server logs all operations with timestamps:

```
2025-07-12 11:47:35,259 - INFO - Received Tally webhook: 214f0ed8-9f45-47fe-b820-a33bd0032b70
2025-07-12 11:47:35,260 - INFO - Extracted full name: Kai Louie-Badua
2025-07-12 11:47:35,261 - INFO - Waiting 30 seconds before calling Trainerize API...
2025-07-12 11:48:05,262 - INFO - Searching for user: Kai Louie-Badua
```

## Deployment

### Local Development
```bash
python webhook_server.py
```

### Production Deployment
For production deployment, consider using:

- **Gunicorn**: `gunicorn -w 4 -b 0.0.0.0:5000 webhook_server:app`
- **Docker**: Create a Dockerfile for containerized deployment
- **Cloud Platforms**: Deploy to AWS, Google Cloud, or Azure

### Environment Variables for Production
```env
FLASK_ENV=production
PORT=5000
OPENAI_API_KEY=your_production_key
QDRANT_URL=your_production_qdrant_url
QDRANT_API_KEY=your_production_qdrant_key
```

## Security Considerations

- **Input Validation**: All incoming data is validated
- **Error Handling**: Sensitive information is not exposed in error messages
- **Rate Limiting**: Consider implementing rate limiting for production
- **Authentication**: Add authentication if needed for production use

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure the server is running on the correct port
2. **Import Errors**: Check that all dependencies are installed
3. **API Key Errors**: Verify environment variables are set correctly
4. **Timeout Issues**: The 30-second wait is intentional; this is normal behavior

### Debug Mode

Run the server in debug mode for detailed logging:

```bash
FLASK_ENV=development python webhook_server.py
```

## Support

For issues or questions, check the logs for detailed error information and ensure all environment variables are properly configured. 