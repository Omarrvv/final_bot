import axios from 'axios';

// Create an axios instance with default settings
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for CSRF protection
});

// Intercept responses to handle common errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(error);
  }
);

const ChatbotService = {
  /**
   * Start a new chat session
   * @returns {Promise<Object>} Session object with session_id
   */
  createSession: async () => {
    try {
      // Get CSRF token first
      const csrfData = await ChatbotService.getCsrfToken().catch(() => {
        return { csrf_token: null }; // Provide fallback token
      });

      const response = await apiClient.post(
        '/api/reset',
        {}, // Empty body
        {
          headers: csrfData.csrf_token
            ? {
                'X-CSRF-Token': csrfData.csrf_token,
              }
            : {},
        }
      );

      return response.data;
    } catch {
      return { session_id: null, error: 'Error resetting session' };
    }
  },

  /**
   * Get a CSRF token for secure requests
   * @returns {Promise<Object>} CSRF token object
   */
  getCsrfToken: async () => {
    try {
      const response = await apiClient.get('/api/csrf-token');
      return response.data;
    } catch {
      return { csrf_token: null }; // Return a dummy token
    }
  },

  /**
   * Send a message to the chatbot
   * @param {string} message - User message text
   * @param {string} sessionId - Current session ID
   * @param {string} language - Language code (e.g., 'en', 'ar')
   * @returns {Promise<Object>} Chatbot response
   */
  sendMessage: async (message, sessionId, language = 'en') => {
    try {
      const csrfData = await ChatbotService.getCsrfToken().catch(() => {
        return { csrf_token: null }; // Provide fallback token
      });

      const response = await apiClient.post(
        '/api/chat',
        {
          message,
          session_id: sessionId,
          language,
        },
        {
          headers: csrfData.csrf_token
            ? {
                'X-CSRF-Token': csrfData.csrf_token,
              }
            : {},
        }
      );

      // Normalize response format - ensure it has required fields
      const normalizedResponse = {
        message:
          response.data.message ||
          response.data.text ||
          'No response from chatbot',
        session_id: response.data.session_id || sessionId,
        message_id: response.data.message_id || `msg_${Date.now()}`,
        suggestions: response.data.suggestions || [],
        success: response.data.status !== 'error',
        timestamp: new Date().toISOString(),
      };

      return normalizedResponse;
    } catch {
      return {
        message: 'I apologize, but I experienced an error. Please try again later.',
        success: false,
        session_id: sessionId,
        message_id: `error_${Date.now()}`,
        timestamp: new Date().toISOString(),
      };
    }
  },

  /**
   * Submit feedback for a message
   * @param {string} messageId - ID of the message receiving feedback
   * @param {string} rating - Feedback rating (0 or 1)
   * @returns {Promise<Object>} Response data
   */
  submitFeedback: async (messageId, rating) => {
    try {
      const csrfData = await ChatbotService.getCsrfToken();

      const response = await apiClient.post(
        '/api/feedback',
        {
          message_id: messageId,
          rating,
        },
        {
          headers: csrfData.csrf_token
            ? {
                'X-CSRF-Token': csrfData.csrf_token,
              }
            : {},
        }
      );

      return response.data;
    } catch {
      return { success: false, error: 'Failed to submit feedback' };
    }
  },

  /**
   * Get supported languages
   * @returns {Promise<Object>} Languages data
   */
  getLanguages: async () => {
    try {
      const response = await apiClient.get('/api/languages');
      return response.data;
    } catch {
      // Return default languages if API fails
      return {
        languages: [
          { code: 'en', name: 'English', flag: 'us', direction: 'ltr' },
          { code: 'ar', name: 'العربية', flag: 'eg', direction: 'rtl' },
        ],
      };
    }
  },

  /**
   * Get suggested messages
   * @param {string} sessionId - Current session ID
   * @param {string} language - Language code
   * @returns {Promise<Object>} Suggestions data
   */
  getSuggestions: async (sessionId, language = 'en') => {
    try {
      const url = sessionId
        ? `/api/suggestions?session_id=${sessionId}&language=${language}`
        : `/api/suggestions?language=${language}`;

      const response = await apiClient.get(url);
      return response.data;
    } catch {
      return { suggestions: [] }; // Return empty suggestions on error
    }
  },
};

export default ChatbotService;
