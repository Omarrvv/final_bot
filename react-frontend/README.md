# Egypt Tourism Chatbot - React Frontend

This is a modern React frontend for the Egypt Tourism Chatbot. It provides a floating chat widget with a modern UI while leveraging the powerful Flask backend for natural language understanding and dialog management.

## Features

- Modern, responsive UI with Tailwind CSS
- Floating chat widget that can be minimized/maximized
- Mobile-friendly design with touch interface
- Multi-language support with RTL layout for Arabic
- Markdown rendering for rich text responses
- Feedback mechanism for bot responses
- Suggestion chips for guided conversations
- Animated typing indicators and transitions

## Setup and Installation

### Prerequisites

- Node.js 16+ and npm
- Egypt Tourism Chatbot backend running on port 5000

### Installation

1. Navigate to the react-frontend directory:

   ```
   cd react-frontend
   ```

2. Install dependencies:

   ```
   npm install
   ```

3. Start the development server:

   ```
   npm start
   ```

4. Build for production:
   ```
   npm run build
   ```

## Integration with Flask Backend

This React frontend is designed to work with the existing Flask backend. It communicates with the backend through a set of API endpoints:

- `/api/reset` - Start a new chat session
- `/api/chat` - Send a message to the chatbot
- `/api/csrf-token` - Get a CSRF token for secure requests
- `/api/feedback` - Submit feedback for a response
- `/api/languages` - Get supported languages
- `/api/suggestions` - Get suggested messages

## Deployment

### Development

For development, the React app proxies requests to the Flask backend on port 5000. This is configured in `package.json`:

```json
"proxy": "http://localhost:5000"
```

### Production

For production deployment, build the React app and configure the Flask app to serve the static files:

1. Build the React app:

   ```
   npm run build
   ```

2. Copy the contents of the `build` directory to the Flask app's static directory:

   ```
   cp -r build/* ../src/static/
   ```

3. Configure the Flask app to serve the React app from the root URL.

## Customization

- Edit `src/components/EgyptTourismChatbot.js` to customize the chat UI
- Edit `tailwind.config.js` to customize colors and styling
- Edit `src/services/ChatbotService.js` to modify API communication

## License

This project is licensed under the MIT License - see the LICENSE file for details.
