import { useState, useEffect, useCallback } from 'react';
import { chatService } from '../services/chatService';

/**
 * Custom hook for managing chat suggestions
 * Loads and manages suggested queries for the chat interface
 */
export const useSuggestions = (apiUrl, language = 'en') => {
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Default fallback suggestions
  const defaultSuggestions = {
    en: [
      'Tell me about the Pyramids of Giza',
      'Best time to visit Egypt',
      'Top attractions in Cairo',
      'Hotels in Luxor',
      'Egyptian cuisine recommendations',
      'Nile River cruise information'
    ],
    ar: [
      'أخبرني عن أهرامات الجيزة',
      'أفضل وقت لزيارة مصر',
      'أفضل المعالم في القاهرة',
      'فنادق في الأقصر',
      'توصيات المأكولات المصرية',
      'معلومات رحلة نيل كروز'
    ]
  };

  // Load suggestions from API
  const loadSuggestions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await chatService.getSuggestions(apiUrl, language);
      
      if (response.suggestions && Array.isArray(response.suggestions)) {
        // Transform API response to expected format
        const formattedSuggestions = response.suggestions.map(suggestion => {
          if (typeof suggestion === 'string') {
            return suggestion;
          }
          return suggestion.text || suggestion.action || suggestion;
        });
        
        setSuggestions(formattedSuggestions);
      } else {
        // Use fallback suggestions
        setSuggestions(defaultSuggestions[language] || defaultSuggestions.en);
      }

    } catch (err) {
      console.warn('Failed to load suggestions, using fallbacks:', err);
      setError(err.message);
      
      // Use fallback suggestions on error
      setSuggestions(defaultSuggestions[language] || defaultSuggestions.en);
      
    } finally {
      setIsLoading(false);
    }
  }, [apiUrl, language]);

  // Load suggestions when API URL or language changes
  useEffect(() => {
    loadSuggestions();
  }, [loadSuggestions]);

  // Refresh suggestions
  const refreshSuggestions = useCallback(() => {
    loadSuggestions();
  }, [loadSuggestions]);

  // Add custom suggestion
  const addCustomSuggestion = useCallback((suggestion) => {
    setSuggestions(prev => {
      const newSuggestions = [...prev];
      if (!newSuggestions.includes(suggestion)) {
        newSuggestions.unshift(suggestion);
        // Keep only latest 8 suggestions
        return newSuggestions.slice(0, 8);
      }
      return newSuggestions;
    });
  }, []);

  // Remove suggestion
  const removeSuggestion = useCallback((suggestionToRemove) => {
    setSuggestions(prev => prev.filter(s => s !== suggestionToRemove));
  }, []);

  // Get suggestions by category (if API supports it)
  const getSuggestionsByCategory = useCallback(async (category) => {
    try {
      setIsLoading(true);
      
      // This would be an enhanced API call for categorized suggestions
      const response = await chatService.getSuggestions(apiUrl, language, { category });
      
      if (response.suggestions && Array.isArray(response.suggestions)) {
        return response.suggestions.map(suggestion => 
          typeof suggestion === 'string' ? suggestion : suggestion.text || suggestion
        );
      }
      
      return [];
      
    } catch (err) {
      console.warn('Failed to load categorized suggestions:', err);
      return [];
      
    } finally {
      setIsLoading(false);
    }
  }, [apiUrl, language]);

  return {
    suggestions,
    isLoading,
    error,
    loadSuggestions,
    refreshSuggestions,
    addCustomSuggestion,
    removeSuggestion,
    getSuggestionsByCategory
  };
};