import React from "react";
import "./LanguageSelector.css";

/**
 * Language selector component for Egypt Tourism Chatbot
 */
const LanguageSelector = ({
  currentLanguage = "en",
  onLanguageChange,
  disabled = false,
}) => {
  const languages = [
    { code: "en", name: "EN", fullName: "English" },
    { code: "ar", name: "AR", fullName: "العربية" },
  ];

  const handleLanguageChange = (languageCode) => {
    if (languageCode !== currentLanguage && !disabled) {
      onLanguageChange?.(languageCode);
    }
  };

  const handleKeyDown = (e, languageCode) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleLanguageChange(languageCode);
    }
  };

  return (
    <div className="language-selector">
      {languages.map((language) => (
        <button
          key={language.code}
          className={`language-option ${
            currentLanguage === language.code ? "active" : ""
          }`}
          onClick={() => handleLanguageChange(language.code)}
          onKeyDown={(e) => handleKeyDown(e, language.code)}
          disabled={disabled}
          aria-label={`Switch to ${language.fullName}`}
          aria-pressed={currentLanguage === language.code}
          title={language.fullName}
        >
          <span className="language-text">{language.name}</span>
        </button>
      ))}
    </div>
  );
};

export default LanguageSelector;
