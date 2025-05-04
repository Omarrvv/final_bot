# Egypt Tourism Chatbot API Reference

This document provides a simple reference for the Egypt Tourism Chatbot API, with a focus on the new authentication endpoints.

## Authentication Endpoints

### Create Session

Creates a new anonymous session for the user.

**Endpoint:** `POST /api/v1/auth/session`

**Request:**
```json
{
  "metadata": {
    "language": "en",
    "interests": ["pyramids", "beaches"]
  },
  "remember_me": true
}
```

- `metadata` (optional): Any information you want to store with the session
- `remember_me` (optional): Set to `true` to keep the session active for 30 days instead of 24 hours

**Response:**
```json
{
  "session_id": "abc123def456",
  "token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer",
  "expires_in": 2592000
}
```

**Notes:**
- The session token is automatically stored as a cookie
- You don't need to manually handle the token in most cases

### Validate Session

Checks if a session is valid.

**Endpoint:** `POST /api/v1/auth/validate-session`

**Request:** No body needed (uses the session cookie)

**Response (valid session):**
```json
{
  "valid": true,
  "session_id": "abc123def456",
  "created_at": "2023-06-15T10:30:00Z",
  "last_accessed": "2023-06-15T11:45:00Z"
}
```

**Response (invalid session):**
```json
{
  "detail": "No session token provided"
}
```

### Refresh Session

Extends the lifetime of a session.

**Endpoint:** `POST /api/v1/auth/refresh-session`

**Request:** No body needed (uses the session cookie)

**Response:**
```json
{
  "session_id": "abc123def456",
  "token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Notes:**
- The new token automatically replaces the old cookie
- Use this to keep a session active for longer than the default expiration

### End Session

Terminates a session (logs out).

**Endpoint:** `POST /api/v1/auth/end-session`

**Request:** No body needed (uses the session cookie)

**Response:**
```json
{
  "message": "Session ended successfully"
}
```

**Notes:**
- This clears the session cookie
- Use this when a user wants to clear their chat history

## Chat Endpoints

### Send Message

Sends a message to the chatbot.

**Endpoint:** `POST /api/chat`

**Request:**
```json
{
  "message": "Tell me about the pyramids",
  "language": "en"
}
```

**Response:**
```json
{
  "message": "The Egyptian pyramids are ancient masonry structures...",
  "suggestions": ["Tell me more", "How tall are they?", "When were they built?"]
}
```

**Notes:**
- Uses the session automatically (include credentials in your request)
- The session helps the chatbot remember the conversation context

### Reset Conversation

Resets the current conversation without ending the session.

**Endpoint:** `POST /api/reset`

**Request:**
```json
{
  "language": "en"
}
```

**Response:**
```json
{
  "message": "Conversation has been reset. How can I help you?",
  "suggestions": ["Tell me about Egypt", "Popular attractions", "Best time to visit"]
}
```

## Example: Complete Chat Flow

Here's a complete example of how to use the API for a chat interaction:

1. **Create a session when the user first visits**
```javascript
// When the page loads
async function initChat() {
  const sessionResponse = await fetch('/api/v1/auth/session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ remember_me: true }),
    credentials: 'include'
  });
  
  // Session created, now show the chat interface
  showChatInterface();
}
```

2. **Send and receive messages**
```javascript
// When user sends a message
async function sendUserMessage(messageText) {
  // Show user message in the UI
  displayUserMessage(messageText);
  
  // Send to API
  const chatResponse = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: messageText }),
    credentials: 'include'
  });
  
  const data = await chatResponse.json();
  
  // Display bot response
  displayBotMessage(data.message);
  
  // Show suggestions if available
  if (data.suggestions && data.suggestions.length > 0) {
    displaySuggestions(data.suggestions);
  }
}
```

3. **Reset conversation if needed**
```javascript
// When user clicks "New Chat" button
async function startNewChat() {
  const resetResponse = await fetch('/api/reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ language: 'en' }),
    credentials: 'include'
  });
  
  const data = await resetResponse.json();
  
  // Clear chat display
  clearChatMessages();
  
  // Show welcome message
  displayBotMessage(data.message);
  displaySuggestions(data.suggestions);
}
```

4. **End session when user wants to clear history**
```javascript
// When user clicks "Clear History" button
async function clearHistory() {
  // End the current session
  await fetch('/api/v1/auth/end-session', {
    method: 'POST',
    credentials: 'include'
  });
  
  // Create a new session
  await fetch('/api/v1/auth/session', {
    method: 'POST',
    credentials: 'include'
  });
  
  // Reset the UI
  clearChatMessages();
  displayWelcomeMessage();
}
```

## Common Questions

### Do I need to include the token in my requests?

No, the token is automatically included as a cookie when you set `credentials: 'include'` in your fetch requests.

### How long does a session last?

By default, sessions last for 24 hours. If you set `remember_me: true` when creating a session, it will last for 30 days.

### Can I store user preferences without requiring login?

Yes! You can store preferences in the session metadata when creating a session. For example:

```json
{
  "metadata": {
    "language": "en",
    "theme": "dark",
    "interests": ["history", "food"]
  }
}
```

### How do I check if a user has an active session?

Use the `/api/v1/auth/validate-session` endpoint to check if a session is valid before showing the chat interface.

### What happens if a session expires?

If a session expires, the chatbot will create a new session automatically when the user sends their next message. However, the conversation history will be lost.
