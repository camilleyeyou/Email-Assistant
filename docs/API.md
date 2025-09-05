# API Documentation

## Base URL
```
http://localhost:8000
```

## Health Check Endpoints

### GET /
Health check endpoint
```json
{
  "status": "healthy",
  "message": "Email Assistant API is running",
  "version": "1.0.0",
  "endpoints": {
    "dashboard": "/api/dashboard",
    "emails": "/api/emails",
    "accounts": "/api/accounts",
    "docs": "/docs"
  }
}
```

### GET /health
Detailed health check
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## Account Management

### POST /api/accounts
Add a new email account

**Request Body:**
```json
{
  "email": "user@gmail.com",
  "password": "app-password-here",
  "imap_server": "imap.gmail.com",
  "smtp_server": "smtp.gmail.com"
}
```

**Response:**
```json
{
  "status": "success",
  "account_id": 1,
  "message": "Email account added successfully"
}
```

### GET /api/accounts
Get all email accounts

**Response:**
```json
[
  {
    "id": 1,
    "email": "user@gmail.com",
    "imap_server": "imap.gmail.com",
    "smtp_server": "smtp.gmail.com"
  }
]
```

## Email Processing

### POST /api/process-emails/{account_id}
Process emails from specified account

**Parameters:**
- `account_id` (int): Account ID to process
- `limit` (int, optional): Number of emails to process (default: 10)

**Response:**
```json
{
  "status": "success",
  "processed_count": 5,
  "emails": [
    {
      "id": "email-hash-123",
      "subject": "Project Update",
      "sender": "colleague@company.com",
      "content": "Brief email content...",
      "category": "project",
      "priority": 3,
      "action_items": ["Review document", "Schedule meeting"],
      "deadlines": [
        {
          "text": "friday at 5pm",
          "extracted_at": "2024-01-15T10:30:00.000Z",
          "priority": "medium"
        }
      ],
      "sentiment": "neutral",
      "suggested_response": "Thank you for the project update..."
    }
  ]
}
```

## Email Retrieval

### GET /api/emails
Get processed emails with optional filtering

**Query Parameters:**
- `category` (string, optional): Filter by category
- `priority` (int, optional): Filter by minimum priority level

**Response:**
```json
[
  {
    "id": "email-hash-123",
    "subject": "Meeting Request",
    "sender": "boss@company.com",
    "content": "Email content here...",
    "category": "meeting",
    "priority": 4,
    "processed_at": "2024-01-15T10:30:00.000Z",
    "action_items": ["Check calendar", "Confirm attendance"],
    "deadlines": [],
    "sentiment": "neutral"
  }
]
```

## Dashboard Analytics

### GET /api/dashboard
Get dashboard statistics

**Response:**
```json
{
  "total_emails": 150,
  "recent_activity": 25,
  "categories": {
    "urgent": 5,
    "meeting": 12,
    "project": 18,
    "invoice": 3,
    "personal": 8,
    "newsletter": 45,
    "support": 2,
    "general": 57
  },
  "priorities": {
    "1": 20,
    "2": 45,
    "3": 50,
    "4": 25,
    "5": 10
  }
}
```

## Data Models

### EmailAccount
```json
{
  "email": "string (email format)",
  "password": "string",
  "imap_server": "string (default: imap.gmail.com)",
  "smtp_server": "string (default: smtp.gmail.com)"
}
```

### ProcessedEmail
```json
{
  "id": "string (unique hash)",
  "subject": "string",
  "sender": "string",
  "content": "string",
  "category": "string (urgent|meeting|project|invoice|personal|newsletter|support|general)",
  "priority": "integer (1-5)",
  "action_items": ["string"],
  "deadlines": [
    {
      "text": "string",
      "extracted_at": "string (ISO datetime)",
      "priority": "string (high|medium|low)"
    }
  ],
  "sentiment": "string (positive|negative|neutral)",
  "suggested_response": "string (optional)"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

## Categories

The system automatically categorizes emails into:

- **urgent**: Contains urgent keywords (asap, immediately, critical)
- **meeting**: Meeting-related content (meeting, call, conference)
- **project**: Project management (project, task, deliverable)
- **invoice**: Billing-related (invoice, payment, billing)
- **personal**: Personal communications
- **newsletter**: Marketing/newsletter content
- **support**: Support requests (help, issue, problem)
- **general**: Uncategorized emails

## Priority Levels

1. **Priority 1**: Low importance
2. **Priority 2**: Below average importance
3. **Priority 3**: Average importance
4. **Priority 4**: High importance
5. **Priority 5**: Critical/urgent

Priority is calculated based on:
- Email category
- Sentiment analysis
- Presence of deadlines
- Urgent keywords

## Rate Limits

- Email processing: Limited by email provider (Gmail: ~15 req/sec)
- API endpoints: No specific limits (local deployment)
- Database operations: SQLite concurrent access limits

## Authentication

Currently, the API runs locally without authentication. For production deployment, consider adding:
- API keys
- OAuth2 authentication
- Rate limiting
- HTTPS encryption