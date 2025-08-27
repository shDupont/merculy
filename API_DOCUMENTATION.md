# Merculy API Documentation

This document provides comprehensive documentation for the Merculy Flask API that has been refactored to use Azure Cosmos DB as the primary database.

## 📋 Table of Contents
- [Overview](#overview)
- [Architecture Changes](#architecture-changes)
- [Configuration](#configuration)
- [Authentication Endpoints](#authentication-endpoints)
- [User Management Endpoints](#user-management-endpoints)
- [News & Newsletter Endpoints](#news--newsletter-endpoints)
- [Data Models](#data-models)
- [Error Handling](#error-handling)

## 🎯 Overview

The Merculy API is a Flask-based backend service that provides:
- User authentication (Email/Password, Google OAuth, Facebook OAuth)
- Personalized newsletter generation using AI (Gemini)
- News aggregation and analysis
- User preference management
- Content management for newsletters and articles

## 🏗️ Architecture Changes

### Before (SQLite/SQLAlchemy)
- Used SQLite database with SQLAlchemy ORM
- Models: User, Newsletter, NewsArticle
- Flask-SQLAlchemy for database management
- Integer-based user IDs

### After (Azure Cosmos DB)
- Uses Azure Cosmos DB as primary database
- Custom user service with hash-based user IDs
- Cosmos DB collections: users, newsletters, news_articles, user_preferences
- Flask-Login compatible user loading
- No SQLAlchemy dependencies

### Key Benefits
- ✅ Cloud-native scalability
- ✅ Global distribution capabilities
- ✅ JSON-native storage
- ✅ Better performance for read-heavy workloads
- ✅ Flexible schema evolution

## ⚙️ Configuration

### Environment Variables
```bash
# Required
COSMOS_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/
COSMOS_KEY=your-cosmos-primary-key
COSMOS_DATABASE_NAME=merculy_db
COSMOS_CONTAINER_NAME=users

# Optional (OAuth)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
FACEBOOK_CLIENT_ID=your-facebook-app-id
FACEBOOK_CLIENT_SECRET=your-facebook-app-secret

# Optional (AI Services)
GEMINI_API_KEY=your-gemini-api-key
NEWS_API_KEY=your-news-api-key
NEWS_API_URL=https://newsapi.org/v2/everything

# Security
SECRET_KEY=your-secret-key-for-sessions
```

### Cosmos DB Collections Structure
```json
{
  "users": {
    "partitionKey": "/id",
    "schema": {
      "id": "string (MD5 hash of email)",
      "email": "string",
      "name": "string",
      "password_hash": "string (optional)",
      "google_id": "string (optional)",
      "facebook_id": "string (optional)",
      "interests": ["array of strings"],
      "newsletter_format": "string (single|by_topic)",
      "delivery_schedule": {
        "days": ["array of day names"],
        "time": "string (HH:MM)"
      },
      "created_at": "string (ISO datetime)",
      "last_login": "string (ISO datetime)",
      "is_active": "boolean",
      "type": "user"
    }
  },
  "newsletters": {
    "partitionKey": "/user_id",
    "schema": {
      "id": "string (user_id_timestamp)",
      "user_id": "string",
      "title": "string",
      "content": "string (HTML)",
      "topic": "string",
      "created_at": "string (ISO datetime)",
      "sent_at": "string (ISO datetime, optional)",
      "is_saved": "boolean",
      "type": "newsletter"
    }
  }
}
```

---

# 🔐 Authentication Endpoints

## POST /api/auth/register
Register a new user with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "securepassword",
  "interests": ["tecnologia", "política"],  // optional
  "newsletter_format": "single",           // optional: "single" | "by_topic"
  "delivery_schedule": {                   // optional
    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
    "time": "08:00"
  }
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "abc123...",
    "email": "user@example.com",
    "name": "John Doe",
    "interests": ["tecnologia", "política"],
    "newsletter_format": "single",
    "delivery_schedule": {
      "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "time": "08:00"
    },
    "created_at": "2024-01-01T10:00:00Z",
    "last_login": null,
    "is_active": true
  }
}
```

**Error Responses:**
- `400`: Missing required fields (email, password, name)
- `409`: User already exists
- `500`: Internal server error

---

## POST /api/auth/login
Login with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response (200):**
```json
{
  "message": "Login successful",
  "user": {
    "id": "abc123...",
    "email": "user@example.com",
    "name": "John Doe",
    "interests": ["tecnologia", "política"],
    "newsletter_format": "single",
    "delivery_schedule": {
      "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "time": "08:00"
    },
    "created_at": "2024-01-01T10:00:00Z",
    "last_login": "2024-01-02T09:30:00Z",
    "is_active": true
  }
}
```

**Error Responses:**
- `400`: Missing email or password
- `401`: Invalid credentials or account deactivated

---

## POST /api/auth/google-login
Login with Google OAuth token.

**Request Body:**
```json
{
  "token": "google-id-token-string"
}
```

**Response (200):**
```json
{
  "message": "Google login successful",
  "user": {
    "id": "abc123...",
    "email": "user@gmail.com",
    "name": "John Doe",
    "interests": [],
    "newsletter_format": "single",
    "delivery_schedule": {
      "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "time": "08:00"
    },
    "created_at": "2024-01-01T10:00:00Z",
    "last_login": "2024-01-02T09:30:00Z",
    "is_active": true
  }
}
```

**Error Responses:**
- `400`: Missing Google token
- `401`: Invalid Google token
- `500`: Failed to create or retrieve user

---

## POST /api/auth/facebook-login
Login with Facebook OAuth token.

**Request Body:**
```json
{
  "access_token": "facebook-access-token-string"
}
```

**Response (200):**
```json
{
  "message": "Facebook login successful",
  "user": {
    "id": "abc123...",
    "email": "user@facebook.com",
    "name": "John Doe",
    "interests": [],
    "newsletter_format": "single",
    "delivery_schedule": {
      "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "time": "08:00"
    },
    "created_at": "2024-01-01T10:00:00Z",
    "last_login": "2024-01-02T09:30:00Z",
    "is_active": true
  }
}
```

**Error Responses:**
- `400`: Missing Facebook token or email permission required
- `401`: Invalid Facebook token
- `500`: Failed to create or retrieve user

---

## POST /api/auth/logout
**Authentication Required**

Logout the current user.

**Response (200):**
```json
{
  "message": "Logout successful"
}
```

---

## GET /api/auth/me
**Authentication Required**

Get current user information.

**Response (200):**
```json
{
  "user": {
    "id": "abc123...",
    "email": "user@example.com",
    "name": "John Doe",
    "interests": ["tecnologia", "política"],
    "newsletter_format": "single",
    "delivery_schedule": {
      "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "time": "08:00"
    },
    "created_at": "2024-01-01T10:00:00Z",
    "last_login": "2024-01-02T09:30:00Z",
    "is_active": true
  }
}
```

---

## PUT /api/auth/update-profile
**Authentication Required**

Update user profile information.

**Request Body:**
```json
{
  "name": "John Smith",                    // optional
  "interests": ["tecnologia", "economia"], // optional
  "newsletter_format": "by_topic",        // optional
  "delivery_schedule": {                   // optional
    "days": ["monday", "wednesday", "friday"],
    "time": "07:00"
  }
}
```

**Response (200):**
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": "abc123...",
    "email": "user@example.com",
    "name": "John Smith",
    "interests": ["tecnologia", "economia"],
    "newsletter_format": "by_topic",
    "delivery_schedule": {
      "days": ["monday", "wednesday", "friday"],
      "time": "07:00"
    },
    "created_at": "2024-01-01T10:00:00Z",
    "last_login": "2024-01-02T09:30:00Z",
    "is_active": true
  }
}
```

**Error Responses:**
- `500`: Failed to update profile

---

## PUT /api/auth/change-password
**Authentication Required**

Change user password.

**Request Body:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newsecurepassword"
}
```

**Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

**Error Responses:**
- `400`: Missing current or new password
- `401`: Current password is incorrect
- `400`: Cannot change password for OAuth-only accounts
- `500`: Failed to change password

---

# 👤 User Management Endpoints

## GET /api/users
**Authentication Required**

Get all users (admin functionality).

**Query Parameters:**
- `limit` (optional): Maximum number of users to return (default: 100)

**Response (200):**
```json
[
  {
    "id": "abc123...",
    "email": "user1@example.com",
    "name": "User One",
    "interests": ["tecnologia"],
    "newsletter_format": "single",
    "delivery_schedule": {
      "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "time": "08:00"
    },
    "created_at": "2024-01-01T10:00:00Z",
    "last_login": "2024-01-02T09:30:00Z",
    "is_active": true
  }
]
```

---

## POST /api/users
**Authentication Required**

Create a new user (admin functionality).

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "name": "New User",
  "password": "securepassword",          // optional
  "interests": ["tecnologia"],           // optional
  "newsletter_format": "single",        // optional
  "delivery_schedule": {                 // optional
    "days": ["monday", "wednesday", "friday"],
    "time": "09:00"
  }
}
```

**Response (201):**
```json
{
  "id": "def456...",
  "email": "newuser@example.com",
  "name": "New User",
  "interests": ["tecnologia"],
  "newsletter_format": "single",
  "delivery_schedule": {
    "days": ["monday", "wednesday", "friday"],
    "time": "09:00"
  },
  "created_at": "2024-01-02T10:00:00Z",
  "last_login": null,
  "is_active": true
}
```

**Error Responses:**
- `400`: Missing email or name
- `409`: Failed to create user or user already exists

---

## GET /api/users/{user_id}
**Authentication Required**

Get user by ID.

**Response (200):**
```json
{
  "id": "abc123...",
  "email": "user@example.com",
  "name": "John Doe",
  "interests": ["tecnologia", "política"],
  "newsletter_format": "single",
  "delivery_schedule": {
    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
    "time": "08:00"
  },
  "created_at": "2024-01-01T10:00:00Z",
  "last_login": "2024-01-02T09:30:00Z",
  "is_active": true
}
```

**Error Responses:**
- `404`: User not found

---

## PUT /api/users/{user_id}
**Authentication Required**

Update user by ID. Users can only update their own profile.

**Request Body:**
```json
{
  "name": "Updated Name",               // optional
  "interests": ["economia", "saúde"],   // optional
  "newsletter_format": "by_topic",     // optional
  "delivery_schedule": {                // optional
    "days": ["tuesday", "thursday"],
    "time": "07:30"
  },
  "is_active": true                     // optional
}
```

**Response (200):**
```json
{
  "id": "abc123...",
  "email": "user@example.com",
  "name": "Updated Name",
  "interests": ["economia", "saúde"],
  "newsletter_format": "by_topic",
  "delivery_schedule": {
    "days": ["tuesday", "thursday"],
    "time": "07:30"
  },
  "created_at": "2024-01-01T10:00:00Z",
  "last_login": "2024-01-02T09:30:00Z",
  "is_active": true
}
```

**Error Responses:**
- `400`: No data provided
- `403`: Unauthorized (can only update own profile)
- `404`: User not found or update failed

---

## DELETE /api/users/{user_id}
**Authentication Required**

Delete user by ID. Users can only delete their own profile.

**Response (204):**
No content.

**Error Responses:**
- `403`: Unauthorized (can only delete own profile)
- `404`: User not found or deletion failed

---

# 📰 News & Newsletter Endpoints

## GET /api/topics
Get list of available news topics.

**Response (200):**
```json
{
  "topics": [
    "tecnologia",
    "política",
    "economia",
    "esportes",
    "saúde",
    "ciência",
    "entretenimento",
    "negócios",
    "educação",
    "meio ambiente"
  ],
  "sources": ["BBC", "CNN", "Reuters", "..."]
}
```

---

## GET /api/news/{topic}
**Authentication Required**

Get news articles by topic.

**Path Parameters:**
- `topic`: Topic name from available topics

**Query Parameters:**
- `limit` (optional): Maximum number of articles (default: 20, max: 100)

**Response (200):**
```json
{
  "topic": "tecnologia",
  "articles": [
    {
      "title": "New AI Technology Breakthrough",
      "content": "Article content...",
      "summary": "AI-generated summary...",
      "source": "TechNews",
      "url": "https://technews.com/article/123",
      "topic": "tecnologia",
      "political_bias": "center",
      "published_at": "2024-01-02T08:00:00Z"
    }
  ],
  "count": 20
}
```

**Error Responses:**
- `500`: Error fetching news articles

---

## GET /api/trending
**Authentication Required**

Get trending news articles.

**Query Parameters:**
- `limit` (optional): Maximum number of articles (default: 20)

**Response (200):**
```json
{
  "articles": [
    {
      "title": "Trending News Article",
      "content": "Article content...",
      "source": "NewsSource",
      "url": "https://news.com/trending/123",
      "published_at": "2024-01-02T08:00:00Z"
    }
  ],
  "count": 15
}
```

---

## GET /api/search
**Authentication Required**

Search for news articles.

**Query Parameters:**
- `q`: Search query (required)
- `limit` (optional): Maximum number of articles (default: 20)

**Response (200):**
```json
{
  "query": "artificial intelligence",
  "articles": [
    {
      "title": "AI Research Advances",
      "content": "Article content...",
      "source": "ScienceDaily",
      "url": "https://sciencedaily.com/ai/456",
      "published_at": "2024-01-02T07:30:00Z"
    }
  ],
  "count": 12
}
```

**Error Responses:**
- `400`: Query parameter is required

---

## POST /api/newsletter/generate
**Authentication Required**

Generate personalized newsletter for current user based on their interests.

**Request Body:** (optional)
```json
{}
```

**Response (201) - Single Format:**
```json
{
  "message": "Newsletter generated successfully",
  "newsletter": {
    "id": "user123_1641110400",
    "title": "Newsletter Personalizada - 02/01/2024",
    "content": "<h1>Newsletter Personalizada - 02/01/2024</h1><h2>Tecnologia</h2>...",
    "topic": "personalizada",
    "created_at": "2024-01-02T10:00:00Z",
    "sent_at": null,
    "is_saved": false
  },
  "format": "single"
}
```

**Response (201) - By Topic Format:**
```json
{
  "message": "Newsletters generated successfully",
  "newsletters": [
    {
      "id": "user123_1641110401",
      "title": "Newsletter Tecnologia - 02/01/2024",
      "content": "<h2>Tecnologia</h2>...",
      "topic": "tecnologia",
      "created_at": "2024-01-02T10:00:00Z",
      "sent_at": null,
      "is_saved": false
    },
    {
      "id": "user123_1641110402",
      "title": "Newsletter Política - 02/01/2024",
      "content": "<h2>Política</h2>...",
      "topic": "política",
      "created_at": "2024-01-02T10:00:00Z",
      "sent_at": null,
      "is_saved": false
    }
  ],
  "format": "by_topic"
}
```

**Error Responses:**
- `404`: No news articles found for user interests
- `500`: Error generating newsletter

---

## GET /api/newsletters
**Authentication Required**

Get user's newsletters with pagination.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 10)
- `topic` (optional): Filter by topic

**Response (200):**
```json
{
  "newsletters": [
    {
      "id": "user123_1641110400",
      "title": "Newsletter Personalizada - 02/01/2024",
      "content": "<h1>Newsletter content...</h1>",
      "topic": "personalizada",
      "created_at": "2024-01-02T10:00:00Z",
      "sent_at": null,
      "is_saved": false
    }
  ],
  "total": 25,
  "pages": 3,
  "current_page": 1
}
```

---

## POST /api/newsletters/{newsletter_id}/save
**Authentication Required**

Save or unsave a newsletter.

**Response (200):**
```json
{
  "message": "Newsletter save status toggled successfully",
  "newsletter_id": "user123_1641110400"
}
```

**Error Responses:**
- `404`: Newsletter not found or operation failed

---

## GET /api/newsletters/saved
**Authentication Required**

Get user's saved newsletters.

**Response (200):**
```json
{
  "newsletters": [
    {
      "id": "user123_1641110400",
      "title": "Newsletter Personalizada - 02/01/2024",
      "content": "<h1>Newsletter content...</h1>",
      "topic": "personalizada",
      "created_at": "2024-01-02T10:00:00Z",
      "sent_at": null,
      "is_saved": true
    }
  ],
  "count": 3
}
```

---

## GET /api/preferences/topics
**Authentication Required**

Get topic suggestions based on user history.

**Response (200):**
```json
{
  "suggested_topics": ["tecnologia", "economia", "política"],
  "all_topics": [
    "tecnologia",
    "política",
    "economia",
    "esportes",
    "saúde",
    "ciência",
    "entretenimento",
    "negócios",
    "educação",
    "meio ambiente"
  ]
}
```

---

## POST /api/articles/{article_id}/analyze
**Authentication Required**

Analyze article for fake news detection using AI.

**Response (200):**
```json
{
  "article_id": "article123",
  "analysis": {
    "score": 7,
    "indicators": [
      "Multiple reliable sources cited",
      "Author credentials verified",
      "Recent publication date"
    ],
    "recommendation": "trustworthy"
  }
}
```

**Error Responses:**
- `404`: Article not found

---

# 📊 Data Models

## User Model
```typescript
interface User {
  id: string;                    // MD5 hash of email
  email: string;                 // Unique email address
  name: string;                  // User's display name
  password_hash?: string;        // Hashed password (optional for OAuth users)
  google_id?: string;           // Google OAuth ID (optional)
  facebook_id?: string;         // Facebook OAuth ID (optional)
  interests: string[];          // Array of user interests/topics
  newsletter_format: 'single' | 'by_topic';  // Newsletter delivery format
  delivery_schedule: {
    days: string[];             // Days of the week
    time: string;               // Time in HH:MM format
  };
  created_at: string;           // ISO datetime
  last_login?: string;          // ISO datetime (optional)
  is_active: boolean;           // Account status
  type: 'user';                // Document type identifier
}
```

## Newsletter Model
```typescript
interface Newsletter {
  id: string;                   // user_id_timestamp
  user_id: string;             // Reference to user
  title: string;               // Newsletter title
  content: string;             // HTML content
  topic: string;               // Topic or 'personalizada'
  created_at: string;          // ISO datetime
  sent_at?: string;            // ISO datetime (optional)
  is_saved: boolean;           // Saved by user flag
  type: 'newsletter';          // Document type identifier
}
```

## NewsArticle Model
```typescript
interface NewsArticle {
  id: string;                  // topic_timestamp
  title: string;               // Article title
  content: string;             // Article content
  summary?: string;            // AI-generated summary (optional)
  source: string;              // News source
  url: string;                 // Original article URL
  topic: string;               // Article topic
  political_bias?: 'left' | 'center' | 'right';  // AI-analyzed bias
  published_at: string;        // ISO datetime
  created_at: string;          // ISO datetime
  type: 'news_article';        // Document type identifier
}
```

---

# ⚠️ Error Handling

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200  | OK - Request successful |
| 201  | Created - Resource created successfully |
| 204  | No Content - Request successful, no content returned |
| 400  | Bad Request - Invalid request data |
| 401  | Unauthorized - Authentication required or invalid credentials |
| 403  | Forbidden - Insufficient permissions |
| 404  | Not Found - Resource not found |
| 409  | Conflict - Resource already exists |
| 500  | Internal Server Error - Server error occurred |

## Error Response Format

All errors follow this format:

```json
{
  "error": "Error message describing what went wrong"
}
```

## Common Error Scenarios

### Authentication Errors
- Missing or invalid credentials
- Expired or invalid OAuth tokens
- Account deactivated
- Insufficient permissions

### Validation Errors
- Missing required fields
- Invalid email format
- Password requirements not met
- Invalid topic selection

### Resource Errors
- User not found
- Newsletter not found
- Article not found
- Failed to create/update resource

### Service Errors
- Cosmos DB connection issues
- AI service unavailable
- News API rate limits exceeded
- External service failures

---

# 🔧 Development Notes

## Testing Cosmos DB Connection
The application includes a connection test on startup that will log:
- ✅ Cosmos DB connection successful
- ❌ Cosmos DB connection failed - check your configuration

## Cosmos DB Collections
The application automatically creates the required collections:
- `users` (partitioned by `/id`)
- `newsletters` (partitioned by `/user_id`)
- `news_articles` (partitioned by `/topic`)
- `user_preferences` (partitioned by `/user_id`)

## User ID Generation
User IDs are generated using MD5 hash of the user's email address, ensuring consistency across OAuth providers while maintaining uniqueness.

## Flask-Login Integration
The custom `CosmosUser` class implements `UserMixin` and provides:
- `get_id()` method for Flask-Login
- Cosmos DB compatible data serialization
- OAuth and password authentication support
