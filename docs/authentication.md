# Egypt Tourism Chatbot Authentication API

This document describes the lightweight session-based authentication system used by the Egypt Tourism Chatbot. The authentication system is designed to be simple and secure, providing session management without requiring user accounts.

## Overview

The Egypt Tourism Chatbot uses a lightweight session-based authentication approach with the following features:

- **Anonymous Sessions**: Users don't need to create accounts or provide credentials
- **JWT Tokens**: Secure JSON Web Tokens for session management
- **Cookie-Based**: Session tokens are stored in HTTP-only cookies
- **Stateful**: Session data is stored on the server for enhanced security
- **Automatic Expiration**: Sessions expire automatically after a configurable period

## Authentication Flow

1. **Session Creation**: When a user first interacts with the chatbot, an anonymous session is created
2. **Token Storage**: The session token is stored in an HTTP-only cookie
3. **Request Authentication**: Subsequent requests include the session token cookie
4. **Token Validation**: The server validates the token for each request
5. **Token Refresh**: Tokens can be refreshed to extend the session
6. **Session Termination**: Sessions can be explicitly terminated

## API Endpoints

### Create Anonymous Session

Creates a new anonymous session for the user.

**Endpoint**: `POST /api/v1/auth/session`

**Request Body**:
```json
{
  "metadata": {
    "language": "en",
    "interests": ["history", "beaches"],
    "device_type": "mobile"
  },
  "remember_me": false
}
```

- `metadata` (optional): Custom data to store with the session
- `remember_me` (optional): Whether to extend the session lifetime (default: false)

**Response**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

- `session_id`: Unique identifier for the session
- `token`: JWT token for authentication
- `token_type`: Type of token (always "bearer")
- `expires_in`: Token expiration time in seconds

**Notes**:
- The token is also set as an HTTP-only cookie named `session_token`
- If `remember_me` is true, the cookie will expire after 30 days; otherwise, it expires after 24 hours

### Validate Session

Validates a session token and returns session information.

**Endpoint**: `POST /api/v1/auth/validate-session`

**Request**:
- No request body required
- Session token should be included in the `session_token` cookie or in the `Authorization` header as a Bearer token

**Response (Success)**:
```json
{
  "valid": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2023-06-15T10:30:00Z",
  "last_accessed": "2023-06-15T11:45:00Z"
}
```

**Response (Error)**:
```json
{
  "detail": "Invalid session token"
}
```

### Refresh Session

Refreshes a session token to extend its validity period.

**Endpoint**: `POST /api/v1/auth/refresh-session`

**Request**:
- No request body required
- Session token should be included in the `session_token` cookie or in the `Authorization` header as a Bearer token

**Response (Success)**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Response (Error)**:
```json
{
  "detail": "Failed to refresh session"
}
```

**Notes**:
- The new token is set as an HTTP-only cookie, replacing the old one
- The session's `last_accessed` timestamp is updated

### End Session

Terminates a session, invalidating the token.

**Endpoint**: `POST /api/v1/auth/end-session`

**Request**:
- No request body required
- Session token should be included in the `session_token` cookie or in the `Authorization` header as a Bearer token

**Response**:
```json
{
  "message": "Session ended successfully"
}
```

**Notes**:
- The `session_token` cookie is cleared
- The session data is removed from the server

## Usage Examples

### Example 1: Initial Session Creation

When a user first visits the chatbot, create an anonymous session:

```javascript
// Client-side JavaScript example
async function createSession() {
  const response = await fetch('/api/v1/auth/session', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      metadata: {
        language: 'en',
        referrer: document.referrer
      }
    }),
    credentials: 'include' // Important: include cookies
  });
  
  const data = await response.json();
  console.log('Session created:', data.session_id);
  return data;
}
```

### Example 2: Validating a Session

Before making API calls, validate that the session is still active:

```javascript
// Client-side JavaScript example
async function validateSession() {
  try {
    const response = await fetch('/api/v1/auth/validate-session', {
      method: 'POST',
      credentials: 'include' // Important: include cookies
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.valid;
    }
    return false;
  } catch (error) {
    console.error('Session validation error:', error);
    return false;
  }
}
```

### Example 3: Refreshing a Session

Refresh the session token periodically to keep the session active:

```javascript
// Client-side JavaScript example
async function refreshSession() {
  try {
    const response = await fetch('/api/v1/auth/refresh-session', {
      method: 'POST',
      credentials: 'include' // Important: include cookies
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('Session refreshed, expires in:', data.expires_in);
      return true;
    }
    return false;
  } catch (error) {
    console.error('Session refresh error:', error);
    return false;
  }
}

// Refresh the session every 12 hours
setInterval(refreshSession, 12 * 60 * 60 * 1000);
```

### Example 4: Ending a Session

When the user is done, end the session:

```javascript
// Client-side JavaScript example
async function endSession() {
  try {
    const response = await fetch('/api/v1/auth/end-session', {
      method: 'POST',
      credentials: 'include' // Important: include cookies
    });
    
    if (response.ok) {
      console.log('Session ended successfully');
      return true;
    }
    return false;
  } catch (error) {
    console.error('Session end error:', error);
    return false;
  }
}
```

## Security Considerations

1. **Token Storage**:
   - Tokens are stored in HTTP-only cookies to prevent JavaScript access
   - The SameSite attribute is set to "lax" to prevent CSRF attacks
   - In production, the Secure flag should be enabled to ensure cookies are only sent over HTTPS

2. **Token Expiration**:
   - Tokens have a default expiration time of 24 hours
   - With "remember_me" enabled, tokens can last up to 30 days
   - Regularly refresh tokens to maintain session validity

3. **Rate Limiting**:
   - The API implements rate limiting to prevent abuse
   - Too many requests from the same session will be rejected

4. **Data Storage**:
   - Only store necessary information in session metadata
   - Avoid storing sensitive information in the session

## Best Practices

1. **Always use HTTPS** in production to protect token transmission
2. **Include credentials** in fetch/axios requests to send cookies
3. **Validate sessions** before making sensitive API calls
4. **Refresh tokens** periodically to maintain session validity
5. **End sessions** explicitly when the user is done
6. **Handle errors** gracefully, redirecting to session creation when needed
