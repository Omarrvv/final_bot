import React from "react";

interface ChatButtonProps {
  onClick: () => void;
}

const ChatButton: React.FC<ChatButtonProps> = ({ onClick }) => {
  return (
    <div className="fixed bottom-6 right-6 z-50">
      <button
        onClick={onClick}
        className="bg-white rounded-full p-4 shadow-lg hover:shadow-xl transition-all duration-300 flex items-center space-x-3 group hover:scale-105 active:scale-95"
      >
        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
          <svg
            className="w-5 h-5 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
        </div>
        <div className="text-left pr-2">
          <div className="text-sm font-medium text-gray-900">
            Need help exploring Egypt?
          </div>
          <div className="text-xs text-gray-600">Let's chat</div>
        </div>
      </button>
    </div>
  );
};

export default ChatButton;
