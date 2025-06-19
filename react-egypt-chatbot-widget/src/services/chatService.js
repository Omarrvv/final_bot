/**
 * Chat service for handling API communication with the Egypt Tourism Chatbot backend
 */

const DEFAULT_TIMEOUT = 30000; // 30 seconds

class ChatService {
  constructor() {
    this.baseUrl = '';
    this.timeout = DEFAULT_TIMEOUT;
  }

  /**
   * Set base URL for API calls
   * @param {string} url - Base URL
   */
  setBaseUrl(url) {
    this.baseUrl = url.replace(/\/$/, ''); // Remove trailing slash
  }

  /**
   * Create request options with timeout and abort signal
   * @param {Object} options - Request options
   * @param {AbortSignal} signal - Abort signal
   * @returns {Object} Enhanced request options
   */
  createRequestOptions(options = {}, signal) {
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options.headers
      },
      timeout: this.timeout,
      signal,
      ...options
    };

    return defaultOptions;
  }

  /**
   * Make HTTP request with error handling
   * @param {string} url - Request URL
   * @param {Object} options - Request options
   * @param {AbortSignal} signal - Abort signal
   * @returns {Promise<Object>} Response data
   */
  async makeRequest(url, options = {}, signal) {
    const fullUrl = url.startsWith('http') ? url : `${this.baseUrl}${url}`;
    const requestOptions = this.createRequestOptions(options, signal);

    try {
      const response = await fetch(fullUrl, requestOptions);

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error');
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return await response.text();
      }

    } catch (error) {
      if (error.name === 'AbortError') {
        throw error;
      }

      // Handle network errors
      if (error.message.includes('fetch')) {
        throw new Error('Network error: Please check your connection and try again.');
      }

      // Handle timeout
      if (error.message.includes('timeout')) {
        throw new Error('Request timeout: The server took too long to respond.');
      }

      throw error;
    }
  }

  /**
   * Send a chat message to the API
   * @param {Object} messageData - Message data
   * @param {string} messageData.message - The message text
   * @param {string} messageData.sessionId - Session ID
   * @param {string} messageData.language - Language code
   * @param {string} messageData.apiUrl - API base URL
   * @param {AbortSignal} signal - Abort signal
   * @returns {Promise<Object>} Chat response
   */
  async sendMessage({ message, sessionId, language = 'en', apiUrl }, signal) {
    this.setBaseUrl(apiUrl);

    const requestBody = {
      message: message.trim(),
      session_id: sessionId,
      language: language
    };

    const response = await this.makeRequest('/api/chat', {
      method: 'POST',
      body: JSON.stringify(requestBody)
    }, signal);

    // Validate response structure
    if (typeof response !== 'object') {
      throw new Error('Invalid response format from server');
    }

    // Handle different response formats
    if (response.text || response.message || response.response) {
      return {
        text: response.text || response.message || response.response,
        session_id: response.session_id || sessionId,
        response_type: response.response_type || 'text',
        suggestions: response.suggestions || [],
        debug_info: response.debug_info || null,
        language: response.language || language
      };
    }

    throw new Error('No valid response content received');
  }

  /**
   * Get suggestions from the API
   * @param {string} apiUrl - API base URL
   * @param {string} language - Language code
   * @param {Object} options - Additional options
   * @returns {Promise<Object>} Suggestions response
   */
  async getSuggestions(apiUrl, language = 'en', options = {}) {
    this.setBaseUrl(apiUrl);

    try {
      const queryParams = new URLSearchParams({
        language,
        ...options
      });

      const response = await this.makeRequest(`/api/suggestions?${queryParams}`, {
        method: 'GET'
      });

      // Handle different response formats
      if (Array.isArray(response)) {
        return { suggestions: response };
      }

      if (response.suggestions && Array.isArray(response.suggestions)) {
        return response;
      }

      // Transform object format to array
      if (typeof response === 'object' && !Array.isArray(response)) {
        const suggestions = Object.values(response).filter(item => 
          typeof item === 'string' || (item && item.text)
        );
        return { suggestions };
      }

      return { suggestions: [] };

    } catch (error) {
      console.warn('Failed to fetch suggestions:', error);
      return { suggestions: [] };
    }
  }

  /**
   * Get available languages
   * @param {string} apiUrl - API base URL
   * @returns {Promise<Array>} Available languages
   */
  async getLanguages(apiUrl) {
    this.setBaseUrl(apiUrl);

    try {
      const response = await this.makeRequest('/api/languages', {
        method: 'GET'
      });

      if (Array.isArray(response)) {
        return response;
      }

      if (response.languages && Array.isArray(response.languages)) {
        return response.languages;
      }

      // Default languages if API doesn't provide them
      return [
        { code: 'en', name: 'English', nativeName: 'English' },
        { code: 'ar', name: 'Arabic', nativeName: 'العربية' }
      ];

    } catch (error) {
      console.warn('Failed to fetch languages:', error);
      return [
        { code: 'en', name: 'English', nativeName: 'English' },
        { code: 'ar', name: 'Arabic', nativeName: 'العربية' }
      ];
    }
  }

  /**
   * Submit feedback
   * @param {Object} feedbackData - Feedback data
   * @param {string} apiUrl - API base URL
   * @returns {Promise<Object>} Feedback response
   */
  async submitFeedback(feedbackData, apiUrl) {
    this.setBaseUrl(apiUrl);

    const response = await this.makeRequest('/api/feedback', {
      method: 'POST',
      body: JSON.stringify(feedbackData)
    });

    return response;
  }

  /**
   * Check API health
   * @param {string} apiUrl - API base URL
   * @returns {Promise<Object>} Health status
   */
  async checkHealth(apiUrl) {
    this.setBaseUrl(apiUrl);

    const response = await this.makeRequest('/api/health', {
      method: 'GET'
    });

    return response;
  }
}

// Create and export singleton instance
export const chatService = new ChatService();