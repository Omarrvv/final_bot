import { useState, useEffect, useCallback, useRef } from 'react';
import { chatService } from '../services/chatService';
import { sessionService } from '../services/sessionService';

/**
 * Custom hook for managing chat functionality
 * Handles messages, session management, and API communication
 */
export const useChat = (apiUrl, language = 'en') => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  
  // Refs for cleanup
  const abortControllerRef = useRef(null);
  const sessionInitialized = useRef(false);

  // Initialize session on mount
  useEffect(() => {
    if (!sessionInitialized.current) {
      initializeSession();
      sessionInitialized.current = true;
    }
    
    // Cleanup on unmount
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Initialize chat session
  const initializeSession = async () => {
    try {
      setError(null);
      const session = await sessionService.createSession(apiUrl);
      setSessionId(session.session_id);
      setIsConnected(true);
      
      // Add welcome message
      addSystemMessage(
        language === 'ar' 
          ? 'مرحباً! أنا مساعدك للسياحة المصرية. كيف يمكنني مساعدتك اليوم؟'
          : 'Welcome! I\'m your Egypt Tourism Assistant. How can I help you explore Egypt today?'
      );
      
    } catch (err) {
      console.error('Failed to initialize session:', err);
      setError(err.message);
      setIsConnected(false);
      
      // Create fallback session ID
      setSessionId(`fallback-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);
      
      addSystemMessage(
        language === 'ar'
          ? 'مرحباً! أنا مساعدك للسياحة المصرية. (وضع عدم الاتصال)'
          : 'Welcome! I\'m your Egypt Tourism Assistant. (Offline mode)'
      );
    }
  };

  // Add system message to chat
  const addSystemMessage = (text) => {
    const systemMessage = {
      id: `system-${Date.now()}`,
      text,
      sender: 'bot',
      timestamp: new Date().toISOString(),
      type: 'system'
    };
    setMessages(prev => [...prev, systemMessage]);
  };

  // Add user message to chat
  const addUserMessage = (text) => {
    const userMessage = {
      id: `user-${Date.now()}`,
      text,
      sender: 'user',
      timestamp: new Date().toISOString(),
      type: 'user'
    };
    setMessages(prev => [...prev, userMessage]);
    return userMessage;
  };

  // Add bot message to chat
  const addBotMessage = (text, data = {}) => {
    const botMessage = {
      id: `bot-${Date.now()}`,
      text,
      sender: 'bot',
      timestamp: new Date().toISOString(),
      type: 'bot',
      ...data
    };
    setMessages(prev => [...prev, botMessage]);
    return botMessage;
  };

  // Send message to API
  const sendMessage = useCallback(async (messageText) => {
    if (!messageText.trim() || isLoading) {
      return;
    }

    // Cancel any pending requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    try {
      setIsLoading(true);
      setError(null);

      // Add user message immediately
      const userMessage = addUserMessage(messageText);

      // Send to API
      const response = await chatService.sendMessage({
        message: messageText,
        sessionId: sessionId,
        language: language,
        apiUrl: apiUrl
      }, abortControllerRef.current.signal);

      // Add bot response
      addBotMessage(response.text || response.message || 'I apologize, but I couldn\'t process your request.', {
        responseType: response.response_type,
        suggestions: response.suggestions || [],
        debug: response.debug_info
      });

      setIsConnected(true);

    } catch (err) {
      if (err.name === 'AbortError') {
        return; // Request was cancelled
      }

      console.error('Failed to send message:', err);
      setError(err.message);
      setIsConnected(false);

      // Add error message
      addBotMessage(
        language === 'ar'
          ? 'عذراً، واجهت مشكلة في معالجة طلبك. يرجى المحاولة مرة أخرى.'
          : 'I\'m sorry, I encountered an issue processing your request. Please try again.',
        { type: 'error' }
      );

    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  }, [sessionId, language, apiUrl, isLoading]);

  // Retry connection
  const retryConnection = useCallback(async () => {
    await initializeSession();
  }, [language]);

  // Clear messages
  const clearMessages = useCallback(() => {
    setMessages([]);
    addSystemMessage(
      language === 'ar'
        ? 'تم مسح المحادثة. كيف يمكنني مساعدتك؟'
        : 'Chat cleared. How can I help you?'
    );
  }, [language]);

  // Reset chat
  const resetChat = useCallback(async () => {
    setMessages([]);
    setError(null);
    setIsLoading(false);
    sessionInitialized.current = false;
    await initializeSession();
  }, [language]);

  return {
    messages,
    isLoading,
    error,
    sessionId,
    isConnected,
    sendMessage,
    clearMessages,
    resetChat,
    retryConnection
  };
};