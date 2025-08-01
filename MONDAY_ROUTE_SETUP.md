# Monday Weekly Check-in Route Setup

## Overview

The `/monday` route has been implemented to automatically send weekly check-in messages to all active clients every Monday. This route performs two main operations:

1. **Fetch Active Clients**: Calls the Trainerize API to get all active clients
2. **Send Mass Messages**: Sends personalized weekly check-in messages to all clients

## Route Details

- **Endpoint**: `POST /monday`
- **Purpose**: Weekly client check-in automation
- **Authentication**: Uses existing Trainerize API credentials
- **Response**: JSON with status, client count, and recipient details

## API Endpoints Used

### 1. Get Client List
- **URL**: Configured via `TRAINERIZE_CLIENT_LIST_URL` environment variable
- **Default**: `https://api.trainerize.com/v03/user/getClientList`
- **Method**: `POST`
- **Payload**:
```json
{
  "userID": 23372308,
  "view": "activeClient",
  "start": 0,
  "count": 100
}
```

### 2. Send Mass Message
- **URL**: Configured via `TRAINERIZE_MASS_MESSAGE_URL` environment variable
- **Default**: `https://api.trainerize.com/v03/message/sendMass`
- **Method**: `POST`
- **Payload**:
```json
{
  "userID": 23372308,
  "recipients": ["24292827", "24645450", "23544758", "24313444"],
  "body": "Hey [Client Name]! Hope you had a great weekend...",
  "type": "text",
  "threadType": "mainThread",
  "conversationType": "single"
}
```

## Environment Variables

The following environment variables are used for API configuration:

```bash
# Required
TRAINERIZE_AUTH=your_auth_token_here
TRAINERIZE_FIND=your_find_api_url_here

# Optional (with defaults)
TRAINERIZE_CLIENT_LIST_URL=https://api.trainerize.com/v03/user/getClientList
TRAINERIZE_MASS_MESSAGE_URL=https://api.trainerize.com/v03/message/sendMass
```

## Message Content

The weekly check-in message includes:
- Personalized greeting with client name
- 10 key questions about progress, workouts, nutrition, energy, wins, challenges, and feedback
- Encouragement for honest, short responses

## Cron Job Setup

### Option 1: Local Development
```bash
# Add to crontab (run every Monday at 9:00 AM)
0 9 * * 1 curl -X POST http://localhost:6000/monday
```

### Option 2: Production (Render)
```bash
# Add to crontab (run every Monday at 9:00 AM)
0 9 * * 1 curl -X POST https://trainerizegenerator.onrender.com/monday
```

### Option 3: Using a Cron Service
For production environments, consider using services like:
- **Cron-job.org**: Free online cron job service
- **EasyCron**: Reliable cron job hosting
- **SetCronJob**: Simple cron job management

## Testing

### Manual Test
```bash
# Test the route manually
curl -X POST http://localhost:6000/monday
```

### Test Mode (Kai LB Only)
For safe testing, you can use test mode to send messages only to Kai LB:

```bash
# Test with Kai LB only
curl -X POST http://localhost:6000/monday \
  -H "Content-Type: application/json" \
  -d '{
    "test_mode": true,
    "target_user_id": "24645450",
    "target_user_name": "Kai LB"
  }'
```

### Python Test Script
```bash
# Run the comprehensive test script
python test_monday_route.py

# Run the simple Kai LB only test
python test_kai_lb_only.py
```

### Test Mode Payload
```json
{
  "test_mode": true,
  "target_user_id": "24645450",
  "target_user_name": "Kai LB"
}
```

**Test Mode Features:**
- Sends message only to the specified user
- Bypasses the client list API call
- Adds "TEST MODE" prefix to response messages
- Includes test mode indicators in the response
- Safe for development and testing

## Response Format

### Success Response (200)
```json
{
  "status": "success",
  "message": "Successfully sent weekly check-in messages to 4 clients",
  "clients_count": 4,
  "recipients": ["24292827", "24645450", "23544758", "24313444"],
  "client_names": {
    "24292827": "Daniel Centeno",
    "24645450": "Kai LB",
    "23544758": "Monica Ewing",
    "24313444": "Robert Jones"
  },
  "worker_pid": 12345,
  "timestamp": "2025-07-22T19:30:00.000Z"
}
```

### Test Mode Response (200)
```json
{
  "status": "success",
  "message": "TEST MODE: Successfully sent weekly check-in messages to 1 clients",
  "clients_count": 1,
  "recipients": ["24645450"],
  "client_names": {
    "24645450": "Kai LB"
  },
  "test_mode": true,
  "target_user": "Kai LB",
  "worker_pid": 12345,
  "timestamp": "2025-07-22T19:30:00.000Z"
}
```

### Error Response (500)
```json
{
  "status": "error",
  "message": "Failed to retrieve active clients from Trainerize",
  "worker_pid": 12345,
  "timestamp": "2025-07-22T19:30:00.000Z"
}
```

## Logging

The route provides comprehensive logging:
- Client list retrieval status
- Number of active clients found
- Mass message sending status
- Recipient details
- Error handling and debugging information

## Error Handling

The route handles various error scenarios:
- **API Connection Errors**: Network issues with Trainerize
- **Authentication Errors**: Invalid API credentials
- **Empty Client Lists**: No active clients to message
- **Message Sending Failures**: Issues with mass message API

## Security Considerations

- Uses existing Trainerize API authentication
- Excludes trainer ID (23372308) from recipient list
- **Excludes specific user ID (23544758) from weekly check-ins**
- Validates client data before sending messages
- Comprehensive error logging for monitoring

## User Exclusion

The Monday route automatically excludes specific users from receiving weekly check-in messages:

### Excluded Users
- **User ID 23544758** (Monica Ewing) - Automatically excluded from all weekly check-ins
- **Trainer ID 23372308** - Excluded as the sender

### Exclusion Behavior
- **Normal Mode**: User 23544758 is filtered out from the client list before sending messages
- **Test Mode**: If test mode targets user 23544758, a warning is returned instead of sending a message
- **Logging**: All excluded users are logged for transparency
- **Response**: Excluded users are listed in the response for monitoring

### Example Response with Exclusions
```json
{
  "status": "success",
  "message": "Successfully sent weekly check-in messages to 3 clients",
  "clients_count": 3,
  "recipients": ["24292827", "24645450", "24313444"],
  "client_names": {
    "24292827": "Daniel Centeno",
    "24645450": "Kai LB",
    "24313444": "Robert Jones"
  },
  "excluded_users": ["Monica Ewing"],
  "worker_pid": 12345,
  "timestamp": "2025-07-22T19:30:00.000Z"
}
```

## Monitoring

Monitor the route execution through:
- Application logs
- Response status codes
- Client count tracking
- Error rate monitoring

## Troubleshooting

### Common Issues

1. **No clients found**: Check if clients are marked as "active" in Trainerize
2. **Authentication errors**: Verify TRAINERIZE_AUTH environment variable
3. **API endpoint errors**: Verify TRAINERIZE_CLIENT_LIST_URL and TRAINERIZE_MASS_MESSAGE_URL environment variables
4. **Network timeouts**: Check internet connectivity and API availability
5. **Message sending failures**: Verify message format and recipient IDs

### Debug Steps

1. Check application logs for detailed error messages
2. Verify all environment variables are set correctly:
   ```bash
   echo $TRAINERIZE_AUTH
   echo $TRAINERIZE_FIND
   echo $TRAINERIZE_CLIENT_LIST_URL
   echo $TRAINERIZE_MASS_MESSAGE_URL
   ```
3. Test API endpoints manually with curl
4. Verify environment variables are set correctly
5. Test with a single client first

## Future Enhancements

Potential improvements:
- **Message Personalization**: Include client-specific progress data
- **Response Tracking**: Monitor client responses to check-ins
- **Scheduling Flexibility**: Allow different check-in schedules
- **Message Templates**: Multiple message variations
- **Analytics**: Track engagement and response rates 