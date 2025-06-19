/**
 * Session service for managing chat sessions with the Egypt Tourism Chatbot backend
 */

import { chatService } from './chatService';

class SessionService {
  constructor() {
    this.currentSession = null;
    this.sessionStorage = this.getSessionStorage();
  }

  /**
   * Get session storage interface
   * @returns {Object} Storage interface
   */
  getSessionStorage() {
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        return {
          setItem: (key, value) => window.sessionStorage.setItem(key, value),
          getItem: (key) => window.sessionStorage.getItem(key),
          removeItem: (key) => window.sessionStorage.removeItem(key)
        };
      }
    } catch (error) {
      console.warn('SessionStorage not available:', error);
    }

    // Fallback to in-memory storage
    const memoryStorage = {};
    return {
      setItem: (key, value) => { memoryStorage[key] = value; },
      getItem: (key) => memoryStorage[key] || null,
      removeItem: (key) => { delete memoryStorage[key]; }
    };
  }

  /**
   * Generate a fallback session ID
   * @returns {string} Generated session ID
   */
  generateFallbackSessionId() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 15);
    return `fallback-${timestamp}-${random}`;
  }

  /**
   * Create a new chat session
   * @param {string} apiUrl - API base URL
   * @returns {Promise<Object>} Session data
   */
  async createSession(apiUrl) {
    try {
      // Check for existing session
      const existingSessionId = this.sessionStorage.getItem('egypt_tourism_session_id');
      const existingSessionExpiry = this.sessionStorage.getItem('egypt_tourism_session_expiry');
      
      if (existingSessionId && existingSessionExpiry) {
        const expiryTime = parseInt(existingSessionExpiry, 10);
        if (Date.now() < expiryTime) {
          // Existing session is still valid
          this.currentSession = {
            session_id: existingSessionId,
            success: true,
            message: 'Using existing session'
          };
          return this.currentSession;
        }
      }

      // Create new session via API
      const response = await chatService.makeRequest('/api/sessions', {
        method: 'POST'
      });

      if (response.session_id) {
        // Store session with expiry (24 hours)
        const expiryTime = Date.now() + (24 * 60 * 60 * 1000);
        this.sessionStorage.setItem('egypt_tourism_session_id', response.session_id);
        this.sessionStorage.setItem('egypt_tourism_session_expiry', expiryTime.toString());

        this.currentSession = {
          session_id: response.session_id,
          success: true,
          message: response.message || 'Session created successfully'
        };

        return this.currentSession;
      }

      throw new Error('No session ID received from API');

    } catch (error) {
      console.warn('Failed to create session via API, using fallback:', error);

      // Create fallback session
      const fallbackSessionId = this.generateFallbackSessionId();
      
      this.currentSession = {
        session_id: fallbackSessionId,
        success: true,
        message: 'Using fallback session (offline mode)',
        isFallback: true
      };

      // Store fallback session
      const expiryTime = Date.now() + (24 * 60 * 60 * 1000);
      this.sessionStorage.setItem('egypt_tourism_session_id', fallbackSessionId);
      this.sessionStorage.setItem('egypt_tourism_session_expiry', expiryTime.toString());

      return this.currentSession;
    }
  }

  /**
   * Get current session
   * @returns {Object|null} Current session data
   */
  getCurrentSession() {
    return this.currentSession;
  }

  /**
   * Validate session
   * @param {string} sessionId - Session ID to validate
   * @param {string} apiUrl - API base URL
   * @returns {Promise<boolean>} Session validity
   */
  async validateSession(sessionId, apiUrl) {
    try {
      const response = await chatService.makeRequest('/api/v1/auth/validate-session', {
        method: 'POST',
        body: JSON.stringify({ session_id: sessionId })
      });

      return response.valid === true;

    } catch (error) {
      console.warn('Session validation failed:', error);
      return false;
    }
  }

  /**
   * Refresh session
   * @param {string} apiUrl - API base URL
   * @returns {Promise<Object>} New session data
   */
  async refreshSession(apiUrl) {
    try {
      if (!this.currentSession) {
        return await this.createSession(apiUrl);
      }

      const response = await chatService.makeRequest('/api/v1/auth/refresh-session', {
        method: 'POST',
        body: JSON.stringify({ session_id: this.currentSession.session_id })
      });

      if (response.session_id) {
        // Update stored session
        const expiryTime = Date.now() + (24 * 60 * 60 * 1000);
        this.sessionStorage.setItem('egypt_tourism_session_id', response.session_id);
        this.sessionStorage.setItem('egypt_tourism_session_expiry', expiryTime.toString());

        this.currentSession = {
          session_id: response.session_id,
          success: true,
          message: 'Session refreshed successfully'
        };

        return this.currentSession;
      }

      throw new Error('Failed to refresh session');

    } catch (error) {
      console.warn('Session refresh failed, creating new session:', error);
      return await this.createSession(apiUrl);
    }
  }

  /**
   * End current session
   * @param {string} apiUrl - API base URL
   * @returns {Promise<boolean>} Success status
   */
  async endSession(apiUrl) {
    try {
      if (this.currentSession && !this.currentSession.isFallback) {
        await chatService.makeRequest('/api/v1/auth/end-session', {
          method: 'POST',
          body: JSON.stringify({ session_id: this.currentSession.session_id })
        });
      }

      // Clear stored session
      this.sessionStorage.removeItem('egypt_tourism_session_id');
      this.sessionStorage.removeItem('egypt_tourism_session_expiry');
      this.currentSession = null;

      return true;

    } catch (error) {
      console.warn('Failed to end session properly:', error);
      
      // Clear local storage anyway
      this.sessionStorage.removeItem('egypt_tourism_session_id');
      this.sessionStorage.removeItem('egypt_tourism_session_expiry');
      this.currentSession = null;

      return false;
    }
  }

  /**
   * Reset session (end current and create new)
   * @param {string} apiUrl - API base URL
   * @returns {Promise<Object>} New session data
   */
  async resetSession(apiUrl) {
    await this.endSession(apiUrl);
    return await this.createSession(apiUrl);
  }

  /**
   * Get session statistics
   * @returns {Object} Session statistics
   */
  getSessionStats() {
    const sessionId = this.sessionStorage.getItem('egypt_tourism_session_id');
    const sessionExpiry = this.sessionStorage.getItem('egypt_tourism_session_expiry');
    
    if (!sessionId || !sessionExpiry) {
      return {
        hasSession: false,
        isActive: false,
        timeRemaining: 0
      };
    }

    const expiryTime = parseInt(sessionExpiry, 10);
    const timeRemaining = Math.max(0, expiryTime - Date.now());
    
    return {
      hasSession: true,
      isActive: timeRemaining > 0,
      timeRemaining: timeRemaining,
      sessionId: sessionId.substring(0, 8) + '...',
      expiresAt: new Date(expiryTime).toISOString()
    };
  }
}

// Create and export singleton instance
export const sessionService = new SessionService();