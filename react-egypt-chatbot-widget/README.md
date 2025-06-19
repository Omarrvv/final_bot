# Egypt Tourism Chatbot Widget

A modern React-based embeddable widget for the Egypt Tourism Chatbot system.

## 🚀 Quick Start

### Development Server
```bash
npm install
npm run dev
```

The widget will be available at `http://localhost:3000` with a development interface.

### Production Build
```bash
npm run build
```

This creates a minified widget at `build/egypt-tourism-widget.min.js`.

## 📝 Integration

### Basic Integration
```html
<!-- Add this to any website -->
<div id="egypt-tourism-chatbot"></div>
<script>
  window.EgyptTourismWidgetConfig = {
    apiUrl: 'http://localhost:5050',
    theme: 'light',
    position: 'bottom-right',
    language: 'en'
  };
</script>
<script src="path/to/egypt-tourism-widget.min.js"></script>
```

### Advanced Configuration
```javascript
window.EgyptTourismWidgetConfig = {
  apiUrl: 'https://your-api-domain.com',
  theme: 'light', // 'light' or 'dark'
  position: 'bottom-right', // 'bottom-right', 'bottom-left', 'top-right', 'top-left'
  language: 'en', // 'en' or 'ar'
  autoOpen: false, // Open chat automatically
  greeting: 'Custom welcome message'
};
```

## 🎯 Features

### ✅ Core Functionality
- **Real-time Chat**: Connects to FastAPI backend for LLM responses
- **Session Management**: Maintains conversation context
- **Bilingual Support**: English and Arabic languages
- **Responsive Design**: Works on desktop and mobile
- **Clickable Widget**: Floating button that opens chat window

### ✅ Advanced Features
- **Modern UI**: Clean, contemporary design with smooth animations
- **Suggestion Chips**: Quick-start conversation prompts
- **Loading States**: Visual feedback during API calls
- **Error Handling**: Graceful fallback for connection issues
- **Accessibility**: Screen reader friendly with proper ARIA labels
- **Cross-browser**: Compatible with all modern browsers

### ✅ Customization
- **Themes**: Light and dark mode support
- **Positioning**: Four corner positions
- **Languages**: English and Arabic with RTL support
- **Styling**: CSS custom properties for easy theming

## 🔧 API Integration

The widget connects to these backend endpoints:

- `POST /api/sessions` - Create chat session
- `POST /api/chat` - Send chat messages
- `GET /api/suggestions` - Get suggested queries
- `GET /api/languages` - Get supported languages

## 🌟 Widget States

### Chat Button
- Shows when chat is closed
- Displays unread message count
- Egypt flag and chat icon
- Smooth hover animations

### Chat Window
- Modern message bubbles
- Typing indicators
- Suggestion chips
- Language selector
- Minimize/expand controls

## 📱 Responsive Design

- **Desktop**: Full-featured chat window (380px × 600px)
- **Mobile**: Optimized for smaller screens with touch-friendly controls
- **Tablet**: Adaptive sizing for medium screens

## 🎨 Theming

### CSS Custom Properties
```css
:root {
  --primary-color: #1a56db;
  --secondary-color: #f59e0b;
  --accent-color: #10b981;
  --text-color: #1f2937;
  --background: #ffffff;
  /* ... more variables */
}
```

### Dark Theme
Automatically applied when `theme: 'dark'` is set in configuration.

## 🌍 Internationalization

### Supported Languages
- **English (en)**: Default language
- **Arabic (ar)**: Full RTL support with Arabic translations

### Language Switching
Users can switch languages using the language selector in the chat header.

## 📋 Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🔒 Security

- **CORS Configured**: Backend properly configured for cross-origin requests
- **Input Sanitization**: User input is properly handled
- **XSS Protection**: Secure rendering of user content

## 🚀 Performance

- **Bundle Size**: ~212KB minified (includes React)
- **Load Time**: Fast initialization with lazy loading
- **Memory**: Efficient memory usage with cleanup
- **Network**: Optimized API calls with caching

## 🧪 Testing

### Development Testing
1. Start backend: `python -m src.main`
2. Start widget: `npm run dev`
3. Open `http://localhost:3000`
4. Test chat functionality

### Production Testing
1. Build widget: `npm run build`
2. Serve from CDN or static hosting
3. Test integration on target websites

## 📝 Development

### Project Structure
```
src/
├── components/
│   ├── ChatWidget/     # Main widget components
│   ├── ChatInterface/  # Chat UI components
│   └── Controls/       # Control components
├── hooks/              # React hooks
├── services/           # API services
└── utils/              # Utility functions
```

### Key Components
- **ChatWidget**: Main container component
- **ChatButton**: Floating chat button
- **ChatWindow**: Full chat interface
- **MessageList**: Message display area
- **MessageInput**: Text input component

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run test` - Run tests

## 🤝 Contributing

1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Ensure accessibility compliance

## 📄 License

MIT License - see LICENSE file for details.

---

## ✅ Implementation Status

### Completed Features ✅
- [x] Project setup and build configuration
- [x] React widget architecture
- [x] Chat button and window components
- [x] API integration with FastAPI backend
- [x] Session management
- [x] Real-time messaging
- [x] Loading states and error handling
- [x] Suggestion chips
- [x] Language switching (EN/AR)
- [x] Responsive design
- [x] Accessibility features
- [x] Production build system

### Ready for Enhancement 🔧
- [ ] Voice input/output
- [ ] Booking integration
- [ ] Advanced analytics
- [ ] File upload support
- [ ] Rich message types
- [ ] Emoji support

This widget is **production-ready** and fully functional with your existing Egypt Tourism Chatbot backend!