// src/frontend/static/js/script.js

// Global variables
let sessionId = null;
let currentLanguage = "en";
let typing = false;

// DOM elements
const chatMessages = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const userInput = document.getElementById("userInput");
const suggestions = document.getElementById("suggestions");
const resetChatButton = document.getElementById("resetChat");
const languageMenu = document.getElementById("languageMenu");
const currentLanguageElement = document.getElementById("currentLanguage");

// Templates
const botMessageTemplate = document.getElementById("messageBotTemplate");
const userMessageTemplate = document.getElementById("messageUserTemplate");
const suggestionButtonTemplate = document.getElementById(
  "suggestionButtonTemplate"
);
const mediaImageTemplate = document.getElementById("mediaImageTemplate");
const mediaMapTemplate = document.getElementById("mediaMapTemplate");

// Initialize the chat application
document.addEventListener("DOMContentLoaded", initialize);

/**
 * Initialize the chat application
 */
async function initialize() {
  // Create error container
  const errorContainerElement = document.createElement("div");
  errorContainerElement.className = "error-container";
  document.body.appendChild(errorContainerElement);

  // Initialize error handler
  errorHandler.initErrorContainer(errorContainerElement);

  // Set up event listeners
  chatForm.addEventListener("submit", handleUserMessage);
  resetChatButton.addEventListener("click", resetChat);

  // Create a safer fetch with error handling
  window.safeFetch = errorHandler.createSafeFetch();

  try {
    // Start a new session
    await createSession();

    // Load initial data
    await Promise.all([loadLanguages(), loadSuggestions()]);

    // Add initial greeting from bot
    const greetingResponse = {
      text: "Hello! I'm your Egyptian tourism assistant. How can I help you explore Egypt today?",
      time: getCurrentTime(),
    };
    addBotMessage(greetingResponse);
  } catch (error) {
    errorHandler.handleError(error, {
      retryCallback: initialize,
    });
  }
}

/**
 * Create a new chat session
 */
async function createSession() {
  try {
    const response = await safeFetch("/api/reset", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({}),
    });

    const data = await response.json();
    sessionId = data.session_id;

    return sessionId;
  } catch (error) {
    console.error("Failed to create session:", error);
    throw new Error(
      "Failed to start chat session. Please try refreshing the page."
    );
  }
}

/**
 * Handle user message submission
 * @param {Event} event - Form submit event
 */
async function handleUserMessage(event) {
  event.preventDefault();

  const userMessageText = userInput.value.trim();
  if (!userMessageText) return;

  // Clear input
  userInput.value = "";

  // Add user message to chat
  addUserMessage(userMessageText);

  // Show typing indicator
  showTypingIndicator();

  try {
    // Prepare request payload
    const payload = {
      message: userMessageText,
      session_id: sessionId,
      language: currentLanguage,
    };

    // Get CSRF token
    const csrfResponse = await safeFetch("/api/csrf-token");
    const csrfData = await csrfResponse.json();
    const csrfToken = csrfData.csrf_token;

    // Send message to server
    const response = await safeFetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify(payload),
    });

    // Hide typing indicator
    hideTypingIndicator();

    // Handle response
    const data = await response.json();

    // Add bot response to chat
    addBotMessage(data);

    // Update suggestions if provided
    if (data.suggestions && data.suggestions.length > 0) {
      displaySuggestions(data.suggestions);
    }

    // Scroll to bottom
    scrollToBottom();
  } catch (error) {
    // Hide typing indicator
    hideTypingIndicator();

    // Handle error with retry option
    errorHandler.handleError(error, {
      retryCallback: () => {
        // Re-add the user's message to the input field
        userInput.value = userMessageText;
        // Focus the input field
        userInput.focus();
      },
    });

    // Add fallback response
    addBotErrorMessage();
  }
}

/**
 * Add a user message to the chat
 * @param {string} message - User message text
 */
function addUserMessage(message) {
  const template = document.importNode(userMessageTemplate.content, true);
  const messageElement = template.querySelector(".message");
  const messageText = template.querySelector(".message-text");
  const messageTime = template.querySelector(".message-time");

  // Set message text
  messageText.textContent = message;

  // Set message time
  messageTime.textContent = getCurrentTime();

  // Add message to chat
  chatMessages.appendChild(template);

  // Scroll to bottom
  scrollToBottom();
}

/**
 * Add a bot message to the chat
 * @param {Object} data - Bot response data
 */
function addBotMessage(data) {
  const template = document.importNode(botMessageTemplate.content, true);
  const messageElement = template.querySelector(".message");
  const messageText = template.querySelector(".message-text");
  const messageMedia = template.querySelector(".message-media");
  const messageTime = template.querySelector(".message-time");
  const messageFeedback = template.querySelector(".message-feedback");

  // Generate message ID
  const messageId = `msg_${Date.now()}`;
  messageElement.dataset.messageId = messageId;

  // Set message text with markdown parsing
  if (data.text) {
    messageText.innerHTML = DOMPurify.sanitize(marked.parse(data.text));
  }

  // Add media content if available
  if (data.media && data.media.length > 0) {
    for (const item of data.media) {
      if (item.type === "image") {
        const imgTemplate = document.importNode(
          mediaImageTemplate.content,
          true
        );
        const img = imgTemplate.querySelector("img");
        img.src = item.url;
        img.alt = item.alt_text || "Image";
        messageMedia.appendChild(imgTemplate);
      } else if (item.type === "map") {
        const mapTemplate = document.importNode(mediaMapTemplate.content, true);
        const iframe = mapTemplate.querySelector("iframe");
        iframe.src = item.url;
        messageMedia.appendChild(mapTemplate);
      }
    }
  }

  // Set message time
  messageTime.textContent = getCurrentTime();

  // Set up feedback buttons
  const feedbackButtons = messageFeedback.querySelectorAll(".feedback-btn");
  feedbackButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const rating = button.dataset.rating;

      // Toggle active class on buttons
      feedbackButtons.forEach((btn) => btn.classList.remove("active"));
      button.classList.add("active");

      // Send feedback to server
      submitFeedback(messageId, rating);
    });
  });

  // Add message to chat
  chatMessages.appendChild(template);

  // Scroll to bottom
  scrollToBottom();
}

/**
 * Add an error message from the bot
 */
function addBotErrorMessage() {
  const errorMessage =
    currentLanguage === "ar"
      ? "عذراً، حدث خطأ ما. يرجى المحاولة مرة أخرى."
      : "Sorry, something went wrong. Please try again.";

  const template = document.importNode(botMessageTemplate.content, true);
  const messageText = template.querySelector(".message-text");
  const messageTime = template.querySelector(".message-time");

  // Set message text
  messageText.textContent = errorMessage;

  // Set message time
  messageTime.textContent = getCurrentTime();

  // Add message to chat
  chatMessages.appendChild(template);

  // Scroll to bottom
  scrollToBottom();
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
  if (typing) return;

  typing = true;

  const indicatorDiv = document.createElement("div");
  indicatorDiv.className = "typing-indicator";
  indicatorDiv.id = "typingIndicator";

  for (let i = 0; i < 3; i++) {
    const dot = document.createElement("span");
    indicatorDiv.appendChild(dot);
  }

  chatMessages.appendChild(indicatorDiv);
  scrollToBottom();
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
  typing = false;
  const indicator = document.getElementById("typingIndicator");
  if (indicator) {
    indicator.remove();
  }
}

/**
 * Load conversation suggestions
 */
async function loadSuggestions() {
  try {
    const url = `/api/suggestions${
      sessionId ? `?session_id=${sessionId}` : ""
    }`;
    const response = await safeFetch(url);
    const data = await response.json();

    if (data.suggestions && data.suggestions.length > 0) {
      displaySuggestions(data.suggestions);
    }
  } catch (error) {
    errorHandler.handleError(error, {
      silent: true, // Don't show UI notification for this
      retryCallback: loadSuggestions,
    });

    // Use default suggestions as fallback
    const defaultSuggestions = [
      { text: "Tell me about the pyramids" },
      { text: "Best time to visit Egypt" },
      { text: "Hotels in Cairo" },
    ];
    displaySuggestions(defaultSuggestions);
  }
}

/**
 * Load supported languages
 */
async function loadLanguages() {
  try {
    const response = await safeFetch("/api/languages");
    const data = await response.json();

    if (data.languages && data.languages.length > 0) {
      // Clear existing languages
      languageMenu.innerHTML = "";

      // Add languages to dropdown
      data.languages.forEach((lang) => {
        const li = document.createElement("li");
        const button = document.createElement("button");
        button.className = "dropdown-item";
        button.innerHTML = `<span class="flag-icon flag-icon-${lang.flag}"></span> ${lang.name}`;
        button.addEventListener("click", () => {
          changeLanguage(lang.code, lang.name, lang.direction);
        });

        li.appendChild(button);
        languageMenu.appendChild(li);
      });
    }
  } catch (error) {
    errorHandler.handleError(error, {
      silent: true, // Don't show UI notification for this
      retryCallback: loadLanguages,
    });
  }
}

/**
 * Change the interface language
 * @param {string} langCode - Language code
 * @param {string} langName - Language name
 * @param {string} direction - Text direction (ltr or rtl)
 */
function changeLanguage(langCode, langName, direction) {
  // Update current language
  currentLanguage = langCode;

  // Update language display
  currentLanguageElement.textContent = langName;

  // Update text direction
  document.documentElement.setAttribute("dir", direction);

  // Reload suggestions
  loadSuggestions();
}

/**
 * Reset the chat conversation
 */
async function resetChat() {
  if (
    !confirm(
      currentLanguage === "ar"
        ? "هل أنت متأكد أنك تريد بدء محادثة جديدة؟"
        : "Are you sure you want to start a new conversation?"
    )
  ) {
    return;
  }

  try {
    // Clear chat messages
    chatMessages.innerHTML = "";

    // Clear suggestions
    suggestions.innerHTML = "";

    // Add loading indicator
    showTypingIndicator();

    // Call API to reset session
    const response = await fetch("/api/reset", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
      }),
    });

    const data = await response.json();

    // Update session ID
    if (data.session_id) {
      sessionId = data.session_id;
    }

    // Create new session
    createSession();
  } catch (error) {
    console.error("Error resetting chat:", error);
    hideTypingIndicator();
    addBotErrorMessage();
  }
}

/**
 * Submit feedback for a message
 * @param {string} messageId - Message ID
 * @param {string} rating - Feedback rating (0 or 1)
 */
async function submitFeedback(messageId, rating) {
  try {
    await fetch("/api/feedback", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        message_id: messageId,
        rating: rating,
      }),
    });
  } catch (error) {
    console.error("Error submitting feedback:", error);
  }
}

/**
 * Get current time in HH:MM format
 * @returns {string} Time string
 */
function getCurrentTime() {
  const now = new Date();
  return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/**
 * Scroll chat to bottom
 */
function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}
