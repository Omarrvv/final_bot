import React, { useState, useEffect } from "react";

interface ChatMessage {
  id: string;
  type: "text" | "card" | "welcome" | "system" | "error";
  content: string;
  image?: string;
  isBot: boolean;
  timestamp: Date;
  suggestions?: string[];
}

interface ChatResponse {
  session_id: string;
  text: string;
  response_type: string;
  language: string;
  suggestions?: string[];
  debug_info?: any;
}

interface Props {
  config?: {
    apiUrl?: string;
    theme?: string;
    position?: string;
    language?: string;
  };
}

const EgyptTourismChatbot = ({ config }: Props) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"chat" | "trip">("chat");
  const [inputMessage, setInputMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      type: "welcome",
      content:
        "I'm Egypt's travel expert. Use the prompts below for quick answers or ask me anything about Egypt!",
      isBot: true,
      timestamp: new Date(),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const apiUrl = config?.apiUrl || "http://localhost:5050";

  // Egypt-specific suggestion cards
  const cardData = [
    {
      id: "pyramids",
      image:
        "https://images.unsplash.com/photo-1539650116574-75c0c6d4d6d7?auto=format&fit=crop&w=800&q=80",
      text: "Tell me about the Pyramids of Giza",
    },
    {
      id: "nile-cruise",
      image:
        "https://images.unsplash.com/photo-1547036967-23d11aacaee0?auto=format&fit=crop&w=800&q=80",
      text: "Plan a Nile cruise trip",
    },
  ];

  const sendMessageToAPI = async (message: string): Promise<ChatResponse> => {
    const response = await fetch(`${apiUrl}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
        session_id: sessionId,
        language: config?.language || "en",
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: "text",
      content: inputMessage,
      isBot: false,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const response = await sendMessageToAPI(inputMessage);

      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
      }

      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "text",
        content: response.text,
        isBot: true,
        timestamp: new Date(),
        suggestions: response.suggestions,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "error",
        content:
          "Sorry, I'm having trouble connecting. Please try again later.",
        isBot: true,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCardClick = (text: string) => {
    setInputMessage(text);
    // Auto-send the message
    setTimeout(() => {
      handleSendMessage();
    }, 100);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={() => setIsOpen(true)}
          className="bg-white rounded-full p-4 shadow-lg hover:shadow-xl transition-all duration-300 flex items-center space-x-3 group hover:scale-105 active:scale-95"
        >
          <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-amber-600 rounded-full flex items-center justify-center">
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
              Need some help?
            </div>
            <div className="text-xs text-gray-600">Let's chat</div>
          </div>
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-[calc(100vw-3rem)] sm:w-96 h-[600px] max-h-[calc(100vh-3rem)] flex flex-col animate-in slide-in-from-bottom-4 slide-in-from-right-4 duration-300">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex space-x-1">
            <button
              onClick={() => setActiveTab("chat")}
              className={`px-6 py-2 rounded-full text-sm font-medium transition-colors ${
                activeTab === "chat"
                  ? "bg-gray-100 text-gray-900"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Chat
            </button>
            <button
              onClick={() => setActiveTab("trip")}
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
            onClick={() => setIsOpen(false)}
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

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {activeTab === "chat" ? (
            <div className="h-full flex flex-col">
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Welcome Message */}
                <div className="flex items-start space-x-4">
                  <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-amber-600 rounded-full flex items-center justify-center flex-shrink-0">
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
                    <div className="text-3xl font-bold text-amber-600 mb-4">
                      Hello!
                    </div>
                    <div className="text-sm text-gray-600 leading-relaxed mb-4">
                      I'm Egypt's travel expert. Use the prompts below for quick
                      answers or ask me anything about Egypt!
                    </div>
                    <button className="text-xs text-amber-600 border border-amber-200 rounded-full px-4 py-2 hover:bg-amber-50 transition-colors flex items-center space-x-2">
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
                      <span>Log in to view your existing trip</span>
                    </button>
                  </div>
                </div>

                {/* Image Cards */}
                {messages.length === 1 && (
                  <div className="space-y-4">
                    {cardData.map((card) => (
                      <div
                        key={card.id}
                        onClick={() => handleCardClick(card.text)}
                        className="relative rounded-2xl overflow-hidden cursor-pointer hover:scale-[1.02] transition-transform shadow-sm"
                      >
                        <img
                          src={card.image}
                          alt={card.text}
                          className="w-full h-48 object-cover"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                        <div className="absolute bottom-6 left-6 right-6">
                          <div className="text-white font-semibold text-base">
                            {card.text}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* User Messages */}
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
                          ? message.type === "error"
                            ? "bg-red-100 text-red-800 border border-red-200"
                            : "bg-gray-100 text-gray-900"
                          : "bg-amber-600 text-white"
                      }`}
                    >
                      <div className="text-sm whitespace-pre-wrap">
                        {message.content}
                      </div>
                    </div>
                  </div>
                ))}

                {/* Loading indicator */}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 p-3 rounded-lg">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: "0.1s" }}
                        ></div>
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: "0.2s" }}
                        ></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Input Field */}
              <div className="p-4 border-t">
                <div className="flex items-center space-x-3">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Start a conversation..."
                      className="w-full p-3 pr-12 border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent text-sm"
                      disabled={isLoading}
                    />
                    <button className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600">
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                        />
                      </svg>
                    </button>
                  </div>
                  <button
                    onClick={handleSendMessage}
                    disabled={isLoading || !inputMessage.trim()}
                    className="w-10 h-10 bg-gradient-to-br from-amber-500 to-amber-600 rounded-full flex items-center justify-center text-white hover:from-amber-600 hover:to-amber-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                      />
                    </svg>
                  </button>
                </div>
                <div className="text-xs text-gray-400 text-center mt-2">
                  AI assistance in use. Check official travel sources
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col p-6">
              <div className="text-center mb-6">
                <div className="text-3xl font-bold text-amber-600 mb-4">
                  Plan your next adventure
                </div>
                <button className="text-xs text-amber-600 border border-amber-200 rounded-full px-4 py-2 hover:bg-amber-50 transition-colors flex items-center space-x-2 mx-auto">
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
                  <span>Log in to view your existing trip</span>
                </button>
              </div>

              <div className="flex-1 space-y-4">
                {/* Main image card */}
                <div className="relative rounded-2xl overflow-hidden shadow-sm">
                  <img
                    src="https://images.unsplash.com/photo-1547036967-23d11aacaee0?auto=format&fit=crop&w=800&q=80"
                    alt="Plan your Egypt adventure"
                    className="w-full h-48 object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                  <div className="absolute bottom-6 left-6 right-6">
                    <div className="text-white font-semibold text-base">
                      Plan your Egypt adventure
                    </div>
                  </div>
                </div>

                {/* Smaller image cards */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="relative rounded-xl overflow-hidden shadow-sm">
                    <img
                      src="https://images.unsplash.com/photo-1539650116574-75c0c6d4d6d7?auto=format&fit=crop&w=800&q=80"
                      alt="Pyramids"
                      className="w-full h-24 object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
                  </div>
                  <div className="relative rounded-xl overflow-hidden shadow-sm">
                    <img
                      src="https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80"
                      alt="Ancient temples"
                      className="w-full h-24 object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
                  </div>
                </div>
              </div>

              {/* Bottom button */}
              <button
                onClick={() => setActiveTab("chat")}
                className="w-full bg-amber-600 text-white py-4 rounded-xl font-medium mt-6 hover:bg-amber-700 transition-colors"
              >
                Take me to the chat
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EgyptTourismChatbot;
