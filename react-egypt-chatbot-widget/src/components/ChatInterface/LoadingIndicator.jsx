import React from 'react';
import './LoadingIndicator.css';

/**
 * Loading indicator component for showing bot typing state
 */
const LoadingIndicator = ({ language = 'en' }) => {
  return (
    <div className="loading-indicator">
      <div className="loading-bubble">
        <div className="bot-avatar">
          🇪🇬
        </div>
        <div className="loading-content">
          <div className="typing-indicator">
            <div className="typing-dots">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
          </div>
          <div className="loading-text">
            {language === 'ar' ? 'يكتب...' : 'Typing...'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingIndicator;