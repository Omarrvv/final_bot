import React from "react";
import { ChatMessage } from "../types";
import ChatHeader from "./ChatHeader";
import ChatView from "./ChatView";
import TripView from "./TripView";

interface ChatWindowProps {
  isOpen: boolean;
  activeTab: "chat" | "trip";
  messages: ChatMessage[];
  onClose: () => void;
  onTabChange: (tab: "chat" | "trip") => void;
  onSendMessage: (content: string) => void;
}

const ChatWindow: React.FC<ChatWindowProps> = ({
  isOpen,
  activeTab,
  messages,
  onClose,
  onTabChange,
  onSendMessage,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-[calc(100vw-3rem)] sm:w-96 h-[600px] max-h-[calc(100vh-3rem)] flex flex-col animate-slide-in-from-bottom animate-slide-in-from-right">
        <ChatHeader
          activeTab={activeTab}
          onTabChange={onTabChange}
          onClose={onClose}
        />

        <div className="flex-1 overflow-hidden">
          {activeTab === "chat" ? (
            <ChatView messages={messages} onSendMessage={onSendMessage} />
          ) : (
            <TripView onTabChange={onTabChange} />
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;
