# Egypt Tourism Chatbot: Authentication Guide

## What's New: Simple Session-Based Authentication

The Egypt Tourism Chatbot now uses a simple session-based approach for authentication. This means:

- **No user accounts needed** - Users don't need to register or log in with username/password
- **Automatic sessions** - Sessions are created automatically when users start using the chatbot
- **Seamless experience** - Authentication happens behind the scenes

## How It Works

1. When a user first visits the chatbot, a session is automatically created
2. The session keeps track of the conversation history and user preferences
3. The session stays active for 24 hours by default (or 30 days with "remember me" option)
4. No personal information is required to use the chatbot

## Benefits for Users

- **Privacy** - No need to share personal information
- **Convenience** - No registration forms or passwords to remember
- **Continuity** - The chatbot remembers the conversation even if the user refreshes the page

## Benefits for Integration

- **Easy to implement** - Simple API endpoints for session management
- **Lightweight** - Minimal server resources required
- **Flexible** - Can store custom data with each session

## Using the Authentication API

### Creating a Session

When a user first interacts with the chatbot, create a session:

```javascript
// Example: Creating a session when the chat page loads
async function initializeChat() {
  // Create a session with user's language preference
  const response = await fetch('/api/v1/auth/session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      metadata: { language: 'en' },
      remember_me: true  // Keep session for 30 days
    }),
    credentials: 'include'
  });
  
  if (response.ok) {
    // Session created successfully, now load the chat interface
    loadChatInterface();
  }
}
```

### Using the Session in Chat Requests

Once a session is created, all chat requests will automatically use it:

```javascript
// Example: Sending a message to the chatbot
async function sendMessage(message) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: message }),
    credentials: 'include'  // Important: include the session cookie
  });
  
  const reply = await response.json();
  displayMessage(reply.message);
}
```

### Checking if a Session is Valid

Before showing the chat interface, you can check if the user has a valid session:

```javascript
// Example: Checking if the user has a valid session
async function checkSession() {
  try {
    const response = await fetch('/api/v1/auth/validate-session', {
      method: 'POST',
      credentials: 'include'
    });
    
    if (response.ok) {
      // Session is valid, show the chat interface
      showChatInterface();
    } else {
      // No valid session, create a new one
      createNewSession();
    }
  } catch (error) {
    console.error('Error checking session:', error);
    // Handle error case
  }
}
```

### Ending a Session

When the user wants to clear their chat history or start fresh:

```javascript
// Example: Ending a session when user clicks "Clear History"
async function clearChatHistory() {
  const response = await fetch('/api/v1/auth/end-session', {
    method: 'POST',
    credentials: 'include'
  });
  
  if (response.ok) {
    // Session ended successfully, create a new one
    createNewSession();
    // Clear the chat display
    clearChatDisplay();
  }
}
```

## Integration Examples

### Website Integration

```html
<!-- Example: Adding the chatbot to a website -->
<div id="egypt-chatbot"></div>

<script>
  document.addEventListener('DOMContentLoaded', async function() {
    // Initialize the chatbot with a session
    await fetch('/api/v1/auth/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        metadata: { 
          referrer: document.referrer,
          page: window.location.pathname
        }
      }),
      credentials: 'include'
    });
    
    // Now load the chatbot interface
    loadChatbotInterface('egypt-chatbot');
  });
</script>
```

### Mobile App Integration

```javascript
// Example: Initializing the chatbot in a mobile app
async function initializeChatbot() {
  // Create a session with device information
  const deviceInfo = await getDeviceInfo();
  
  const response = await fetch('https://your-api.com/api/v1/auth/session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      metadata: { 
        device: deviceInfo.model,
        platform: deviceInfo.platform,
        language: deviceInfo.language
      },
      remember_me: true
    })
  });
  
  // Store the session token for future requests
  const data = await response.json();
  saveTokenToSecureStorage(data.token);
  
  // Now the chatbot is ready to use
  showChatInterface();
}
```

## Customizing Sessions

You can store custom information with each session to personalize the experience:

```javascript
// Example: Storing user preferences in the session
async function updateUserPreferences(preferences) {
  // First validate the current session
  const validationResponse = await fetch('/api/v1/auth/validate-session', {
    method: 'POST',
    credentials: 'include'
  });
  
  if (validationResponse.ok) {
    // Session is valid, now create a new session with updated preferences
    const response = await fetch('/api/v1/auth/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        metadata: { 
          language: preferences.language,
          interests: preferences.interests,
          theme: preferences.theme
        },
        remember_me: true
      }),
      credentials: 'include'
    });
    
    if (response.ok) {
      // Preferences updated successfully
      showSuccessMessage('Preferences saved!');
    }
  }
}
```

## Best Practices

1. **Always include credentials** in your fetch requests to send the session cookie
2. **Create a session early** when the user first visits your site
3. **Check session validity** before making important requests
4. **Provide a way to clear history** by ending the session
5. **Store relevant preferences** in the session metadata for personalization

## Need Help?

If you have questions about implementing the authentication system, please contact our support team at support@egyptchatbot.com.
