import React, { useState } from "react";
import { ChatMessage } from "../types";
import MessageInput from "./MessageInput";
import ImageCard from "./ImageCard";

interface ChatViewProps {
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
}

const ChatView: React.FC<ChatViewProps> = ({ messages, onSendMessage }) => {
  const egyptCards = [
    {
      id: "pyramids",
      image:
        "https://images.unsplash.com/photo-1539650116574-8efeb43e2750?w=400",
      text: "Explore the Great Pyramids of Giza",
    },
    {
      id: "nile",
      image: "https://images.unsplash.com/photo-1553913861-c0fddf2619ee?w=400",
      text: "Cruise the Nile River in luxury",
    },
  ];

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Welcome Message */}
        <div className="flex items-start space-x-4">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
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
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>
          <div className="flex-1">
            <div className="text-3xl font-bold text-blue-600 mb-4">Hello!</div>
            <div className="text-sm text-gray-600 leading-relaxed mb-4">
              I'm your Egypt Tourism expert. Use the prompts below for quick
              answers or ask me anything about Egypt!
            </div>
            <button className="text-xs text-blue-600 border border-blue-200 rounded-full px-4 py-2 hover:bg-blue-50 transition-colors flex items-center space-x-2">
              <svg
                className="w-3 h-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
              <span>Log in to save your trip plans</span>
            </button>
          </div>
        </div>

        {/* Image Cards */}
        <div className="space-y-4">
          {egyptCards.map((card) => (
            <ImageCard
              key={card.id}
              {...card}
              onClick={() => onSendMessage(card.text)}
            />
          ))}
        </div>

        {/* Messages */}
        {messages.slice(1).map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.isBot ? "justify-start" : "justify-end"
            }`}
          >
            <div
              className={`max-w-[80%] p-3 rounded-lg ${
                message.isBot
                  ? "bg-gray-100 text-gray-900"
                  : "bg-blue-600 text-white"
              }`}
            >
              <div className="text-sm">{message.content}</div>
            </div>
          </div>
        ))}
      </div>

      <MessageInput onSendMessage={onSendMessage} />
    </div>
  );
};

export default ChatView;
