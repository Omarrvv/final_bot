import React from "react";
import "./MessageBubble.css";

/**
 * Message bubble component with Qatar-style spacing
 */
const MessageBubble = ({ message, language = "en", isLatest = false }) => {
  const { sender, text, timestamp, type = "text" } = message;

  const formatTime = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "";
    }
  };

  const formatMessage = (text) => {
    // Simple formatting for line breaks
    return text.split("\n").map((line, index) => (
      <React.Fragment key={index}>
        {line}
        {index < text.split("\n").length - 1 && <br />}
      </React.Fragment>
    ));
  };

  return (
    <div className={`message ${sender} ${type}`}>
      <div className="message-content-wrapper">
        {sender === "bot" && <div className="message-avatar">🇪🇬</div>}

        <div className="message-bubble">
          <div className="message-text">{formatMessage(text)}</div>
          {timestamp && (
            <div className="message-time">{formatTime(timestamp)}</div>
          )}
        </div>

        {sender === "user" && <div className="message-avatar">👤</div>}
      </div>
    </div>
  );
};

export default MessageBubble;
