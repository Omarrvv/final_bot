import React, { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";
import LoadingIndicator from "./LoadingIndicator";
import "./MessageList.css";

/**
 * Message list component that displays chat messages with proper spacing
 */
const MessageList = ({
  messages = [],
  isLoading = false,
  error = null,
  language = "en",
}) => {
  const messagesEndRef = useRef(null);
  const listRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Welcome message when no messages
  const renderWelcome = () => (
    <div className="welcome-section">
      <div className="welcome-avatar">{language === "ar" ? "🇪🇬" : "🇪🇬"}</div>
      <h3 className="welcome-title">
        {language === "ar" ? "مرحباً!" : "Hello!"}
      </h3>
      <p className="welcome-subtitle">
        {language === "ar"
          ? "أنا خبير السفر في مصر. استخدم المطالبات أدناه للحصول على إجابات سريعة أو اسألني أي شيء عن مصر!"
          : "I'm Egypt's travel expert. Use the prompts below for quick answers or ask me anything about Egypt!"}
      </p>
    </div>
  );

  return (
    <div className="message-list-container" ref={listRef}>
      <div className="message-list">
        {/* Show welcome message if no messages */}
        {messages.length === 0 && !isLoading && !error && renderWelcome()}

        {/* Render messages with proper spacing */}
        {messages.map((message, index) => (
          <MessageBubble
            key={message.id || index}
            message={message}
            isLatest={index === messages.length - 1}
            language={language}
          />
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="loading-message">
            <LoadingIndicator />
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            <span>
              {language === "ar"
                ? "عذراً، حدث خطأ. يرجى المحاولة مرة أخرى."
                : "Sorry, something went wrong. Please try again."}
            </span>
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default MessageList;
