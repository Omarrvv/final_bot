import React, { useState, useRef } from 'react';
import './MessageInput.css';

/**
 * Message input component for sending chat messages
 */
const MessageInput = ({
  onSendMessage,
  disabled = false,
  language = 'en',
  placeholder = null
}) => {
  const [message, setMessage] = useState('');
  const [isComposing, setIsComposing] = useState(false);
  const inputRef = useRef(null);

  const defaultPlaceholder = placeholder || 
    (language === 'ar' ? 'اكتب رسالتك هنا...' : 'Type your message here...');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled && !isComposing) {
      onSendMessage(message.trim());
      setMessage('');
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleCompositionStart = () => {
    setIsComposing(true);
  };

  const handleCompositionEnd = () => {
    setIsComposing(false);
  };

  return (
    <form className="message-input-form" onSubmit={handleSubmit}>
      <div className="input-container">
        <input
          ref={inputRef}
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          onCompositionStart={handleCompositionStart}
          onCompositionEnd={handleCompositionEnd}
          placeholder={defaultPlaceholder}
          disabled={disabled}
          className="message-input"
          autoComplete="off"
          maxLength={1000}
          aria-label={language === 'ar' ? 'اكتب رسالتك' : 'Type your message'}
        />
        
        <button
          type="submit"
          disabled={disabled || !message.trim() || isComposing}
          className="send-button"
          aria-label={language === 'ar' ? 'إرسال' : 'Send message'}
          title={language === 'ar' ? 'إرسال' : 'Send'}
        >
          <span className="send-icon">
            {disabled ? '⏳' : '➤'}
          </span>
        </button>
      </div>
      
      {/* Character counter for long messages */}
      {message.length > 800 && (
        <div className="character-counter">
          {1000 - message.length} {language === 'ar' ? 'حرف متبقي' : 'characters remaining'}
        </div>
      )}
    </form>
  );
};

export default MessageInput;