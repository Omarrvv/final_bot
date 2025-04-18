/**
 * Get the current time formatted as a string
 * @param {string} locale - Locale for time formatting (e.g., 'en-US', 'ar-EG')
 * @return {string} Formatted time string
 */
export const getCurrentTime = (locale = "en-US") => {
  return new Date().toLocaleTimeString(locale, {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
};

/**
 * Format a timestamp as a readable time string
 * @param {Date|string|number} timestamp - Timestamp to format
 * @param {string} locale - Locale for time formatting (e.g., 'en-US', 'ar-EG')
 * @return {string} Formatted time string
 */
export const formatTime = (timestamp, locale = "en-US") => {
  return new Date(timestamp).toLocaleTimeString(locale, {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
};

/**
 * Format a date as a readable string
 * @param {Date|string|number} date - Date to format
 * @param {string} locale - Locale for date formatting (e.g., 'en-US', 'ar-EG')
 * @return {string} Formatted date string
 */
export const formatDate = (date, locale = "en-US") => {
  return new Date(date).toLocaleDateString(locale, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};
