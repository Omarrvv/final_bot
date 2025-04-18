/**
 * Error handling utilities for the Egypt Tourism Chatbot frontend.
 * Provides centralized error handling, reporting, and user feedback.
 */

class ErrorHandler {
  /**
   * Initialize the error handler.
   */
  constructor() {
    this.errorContainer = null;
    this.retryCallbacks = {};
    this.nextErrorId = 1;

    // Initialize error handling
    this._initGlobalHandlers();
  }

  /**
   * Initialize global error handlers.
   * @private
   */
  _initGlobalHandlers() {
    // Handle unhandled Promise rejections
    window.addEventListener("unhandledrejection", (event) => {
      console.error("Unhandled promise rejection:", event.reason);
      this.handleError(event.reason);
    });

    // Handle global errors
    window.addEventListener("error", (event) => {
      console.error("Global error:", event.error);
      this.handleError(event.error);
    });
  }

  /**
   * Initialize the error container in the DOM.
   * @param {HTMLElement} container - The container element for errors
   */
  initErrorContainer(container) {
    this.errorContainer = container;
  }

  /**
   * Handle an error and display it to the user if needed.
   * @param {Error|string} error - The error to handle
   * @param {Object} options - Error handling options
   * @param {boolean} options.silent - Whether to suppress UI notifications
   * @param {Function} options.retryCallback - Function to call when retry is requested
   * @returns {string} Error ID for reference
   */
  handleError(error, options = {}) {
    const errorId = `error-${this.nextErrorId++}`;
    const errorMessage = this._getErrorMessage(error);

    // Log the error
    console.error(`Error ${errorId}:`, error);

    // Store retry callback if provided
    if (options.retryCallback && typeof options.retryCallback === "function") {
      this.retryCallbacks[errorId] = options.retryCallback;
    }

    // Display error notification unless silent
    if (!options.silent && this.errorContainer) {
      this._displayErrorNotification(errorId, errorMessage);
    }

    // TODO: Send error to server for logging
    this._reportErrorToServer(errorId, error);

    return errorId;
  }

  /**
   * Get a user-friendly error message.
   * @param {Error|string|Object} error - The error object
   * @returns {string} User-friendly error message
   * @private
   */
  _getErrorMessage(error) {
    if (!error) {
      return "An unknown error occurred";
    }

    if (typeof error === "string") {
      return error;
    }

    if (error.message) {
      return error.message;
    }

    if (error.status && error.statusText) {
      return `Server error: ${error.status} ${error.statusText}`;
    }

    if (error.responseJSON && error.responseJSON.message) {
      return error.responseJSON.message;
    }

    return "An unexpected error occurred";
  }

  /**
   * Display an error notification to the user.
   * @param {string} errorId - The error ID
   * @param {string} message - The error message
   * @private
   */
  _displayErrorNotification(errorId, message) {
    if (!this.errorContainer) {
      console.warn("Error container not initialized");
      return;
    }

    const errorElement = document.createElement("div");
    errorElement.className = "error-notification";
    errorElement.id = errorId;
    errorElement.innerHTML = `
      <div class="error-icon"><i class="fas fa-exclamation-circle"></i></div>
      <div class="error-content">
        <div class="error-message">${message}</div>
        <div class="error-actions">
          ${
            this.retryCallbacks[errorId]
              ? '<button class="retry-button">Retry</button>'
              : ""
          }
          <button class="dismiss-button">Dismiss</button>
        </div>
      </div>
    `;

    // Add event listeners
    const retryButton = errorElement.querySelector(".retry-button");
    if (retryButton) {
      retryButton.addEventListener("click", () => this._handleRetry(errorId));
    }

    const dismissButton = errorElement.querySelector(".dismiss-button");
    dismissButton.addEventListener("click", () => this._dismissError(errorId));

    // Add to container
    this.errorContainer.appendChild(errorElement);

    // Auto-dismiss after 10 seconds
    setTimeout(() => {
      if (document.getElementById(errorId)) {
        this._dismissError(errorId);
      }
    }, 10000);
  }

  /**
   * Handle retry button click.
   * @param {string} errorId - The error ID
   * @private
   */
  _handleRetry(errorId) {
    if (this.retryCallbacks[errorId]) {
      this.retryCallbacks[errorId]();
    }
    this._dismissError(errorId);
  }

  /**
   * Dismiss an error notification.
   * @param {string} errorId - The error ID
   * @private
   */
  _dismissError(errorId) {
    const errorElement = document.getElementById(errorId);
    if (errorElement) {
      // Fade out
      errorElement.style.opacity = "0";
      setTimeout(() => {
        if (errorElement.parentNode) {
          errorElement.parentNode.removeChild(errorElement);
        }
      }, 300);
    }

    // Clean up retry callback
    delete this.retryCallbacks[errorId];
  }

  /**
   * Report an error to the server for logging.
   * @param {string} errorId - The error ID
   * @param {Error|string|Object} error - The error object
   * @private
   */
  _reportErrorToServer(errorId, error) {
    // Avoid circular JSON
    const errorData = {
      errorId,
      message: this._getErrorMessage(error),
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    };

    if (error.stack) {
      errorData.stack = error.stack;
    }

    // Don't wait for response or handle errors here
    fetch("/api/error-report", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(errorData),
    }).catch((e) => console.error("Failed to send error report:", e));
  }

  /**
   * Create a wrapped fetch function with error handling.
   * @returns {Function} Wrapped fetch function
   */
  createSafeFetch() {
    return async (url, options = {}) => {
      try {
        const response = await fetch(url, options);

        if (!response.ok) {
          // Try to parse error message from response
          let errorData;
          try {
            errorData = await response.json();
          } catch (e) {
            errorData = { message: response.statusText };
          }

          const error = new Error(errorData.message || "Request failed");
          error.status = response.status;
          error.statusText = response.statusText;
          error.response = response;
          error.responseData = errorData;
          throw error;
        }

        return response;
      } catch (error) {
        this.handleError(error, {
          retryCallback: () => this.createSafeFetch()(url, options),
        });
        throw error;
      }
    };
  }
}

// Create a global instance
const errorHandler = new ErrorHandler();
