import DOMPurify from "dompurify";
import { marked } from "marked";

/**
 * Process markdown text and sanitize HTML
 * @param {string} text - Markdown text to process
 * @return {string} Sanitized HTML
 */
export const processMarkdown = (text) => {
  if (!text) return "";
  return DOMPurify.sanitize(marked.parse(text));
};

/**
 * Truncate text to a specified length with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @return {string} Truncated text
 */
export const truncateText = (text, maxLength = 100) => {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
};

/**
 * Get appropriate text direction based on language
 * @param {string} language - Language code
 * @return {string} Text direction ('rtl' or 'ltr')
 */
export const getTextDirection = (language) => {
  const rtlLanguages = ["ar", "he", "fa", "ur"];
  return rtlLanguages.includes(language) ? "rtl" : "ltr";
};

/**
 * Get appropriate locale code for a language
 * @param {string} language - Language code
 * @return {string} Locale code
 */
export const getLocaleCode = (language) => {
  const localeMap = {
    en: "en-US",
    ar: "ar-EG",
    fr: "fr-FR",
    es: "es-ES",
    de: "de-DE",
  };

  return localeMap[language] || "en-US";
};
