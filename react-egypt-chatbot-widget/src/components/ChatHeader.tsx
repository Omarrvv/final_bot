import React from "react";

interface ChatHeaderProps {
  activeTab: "chat" | "trip";
  onTabChange: (tab: "chat" | "trip") => void;
  onClose: () => void;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
  activeTab,
  onTabChange,
  onClose,
}) => {
  return (
    <div className="flex items-center justify-between p-4 border-b">
      <div className="flex space-x-1">
        <button
          onClick={() => onTabChange("chat")}
          className={`px-6 py-2 rounded-full text-sm font-medium transition-colors ${
            activeTab === "chat"
              ? "bg-gray-100 text-gray-900"
              : "text-gray-600 hover:text-gray-900"
          }`}
        >
          Chat
        </button>
        <button
          onClick={() => onTabChange("trip")}
          className={`px-6 py-2 rounded-full text-sm font-medium transition-colors ${
            activeTab === "trip"
              ? "bg-gray-100 text-gray-900"
              : "text-gray-600 hover:text-gray-900"
          }`}
        >
          My Trip
        </button>
      </div>
      <button
        onClick={onClose}
        className="p-2 hover:bg-gray-100 rounded-full transition-colors"
      >
        <svg
          className="w-4 h-4 text-gray-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
};

export default ChatHeader;
