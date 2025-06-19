import React from "react";
import "./SuggestionChips.css";

/**
 * Clean suggestion chips component for quick message options
 */
const SuggestionChips = ({
  suggestions = [],
  onSuggestionClick,
  language = "en",
}) => {
  if (!suggestions || suggestions.length === 0) {
    return null;
  }

  const handleSuggestionClick = (suggestion) => {
    onSuggestionClick?.(suggestion);
  };

  const handleKeyDown = (e, suggestion) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleSuggestionClick(suggestion);
    }
  };

  return (
    <div className="suggestion-chips">
      <div className="chips-container">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            className="suggestion-chip"
            onClick={() => handleSuggestionClick(suggestion)}
            onKeyDown={(e) => handleKeyDown(e, suggestion)}
            aria-label={`${
              language === "ar" ? "اقتراح" : "Suggestion"
            }: ${suggestion}`}
            title={suggestion}
          >
            <span className="chip-text">{suggestion}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default SuggestionChips;
