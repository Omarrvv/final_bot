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
  const [activeTab, setActiveTab] = useState<"Chat" | "My Trip">("Chat");
  const [inputMessage, setInputMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const apiUrl = config?.apiUrl || "http://localhost:5050";

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

  return (
    <div
      style={{
        fontFamily:
          "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        fontWeight: "400",
      }}
    >
      {/* Chat Widget */}
      <div className="fixed bottom-6 right-6 z-50">
        {isOpen ? (
          <div className="bg-white rounded-3xl shadow-2xl border border-gray-200 w-[480px] h-[700px] max-h-[calc(100vh-6rem)] flex flex-col overflow-hidden">
            {/* Header with fully visible rounded top */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white rounded-t-3xl">
              <div className="flex items-center gap-1">
                <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
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
                      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                </button>
              </div>

              <div className="flex bg-gray-100 rounded-full p-1">
                <button
                  onClick={() => setActiveTab("Chat")}
                  className={`px-6 py-2 rounded-full text-sm font-normal transition-colors ${
                    activeTab === "Chat"
                      ? "bg-white text-gray-900 shadow-sm"
                      : "text-gray-600 hover:text-gray-900"
                  }`}
                >
                  Chat
                </button>
                <button
                  onClick={() => setActiveTab("My Trip")}
                  className={`px-6 py-2 rounded-full text-sm font-normal transition-colors ${
                    activeTab === "My Trip"
                      ? "bg-white text-gray-900 shadow-sm"
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

            {/* Chat Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {activeTab === "Chat" ? (
                <>
                  {/* Welcome Message */}
                  <div className="text-center space-y-4">
                    <h2 className="text-3xl font-normal text-[#DC143C]">
                      Ahlan wa Sahlan!
                    </h2>
                    <p className="text-base text-gray-600 leading-relaxed px-4 font-normal">
                      I'm Visit Egypt's travel expert. Use the prompts below for
                      quick answers or ask me anything about Egypt!
                    </p>
                  </div>

                  {/* Login Button - Only show if no messages */}
                  {messages.length === 0 && (
                    <div className="flex justify-center pt-2">
                      <button className="text-[#DC143C] border border-[#DC143C] hover:bg-[#DC143C] hover:text-white px-6 py-2 text-sm font-normal rounded-full transition-colors flex items-center space-x-2">
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
                            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                          />
                        </svg>
                        <span>Log in to view your existing trip</span>
                      </button>
                    </div>
                  )}

                  {/* Main Featured Card - Only show if no messages */}
                  {messages.length === 0 && (
                    <div
                      className="relative rounded-xl overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
                      onClick={() =>
                        handleCardClick("Best Nile cruise experiences?")
                      }
                    >
                      <img
                        src="/images/nile-cruise.jpg"
                        alt="Traditional felucca boats sailing on the Nile River at sunset with golden light"
                        className="w-full h-48 object-cover"
                        onError={(e) => {
                          e.currentTarget.src =
                            "https://images.unsplash.com/photo-1594736797933-d0501ba2fe65?w=450&h=280&fit=crop&auto=format&q=80";
                        }}
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-black/20 to-transparent"></div>
                      <div className="absolute bottom-4 left-4">
                        <p className="text-white font-medium text-lg">
                          Best Nile cruise experiences?
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Suggestion Cards - Only show if no messages */}
                  {messages.length === 0 && (
                    <div className="grid grid-cols-2 gap-4">
                      <div
                        className="bg-gray-50 rounded-xl p-4 cursor-pointer hover:bg-gray-100 transition-colors"
                        onClick={() => handleCardClick("Best shopping offers")}
                      >
                        <img
                          src="/images/shopping-bazaar.jpg"
                          alt="Vibrant Khan El Khalili bazaar with colorful spices, textiles and traditional crafts"
                          className="w-full h-24 object-cover rounded-lg mb-3"
                          onError={(e) => {
                            e.currentTarget.src =
                              "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=180&h=120&fit=crop&auto=format&q=80";
                          }}
                        />
                        <p className="text-sm font-normal text-gray-800">
                          Best Bazaars in Cairo
                        </p>
                      </div>

                      <div
                        className="bg-gray-50 rounded-xl p-4 cursor-pointer hover:bg-gray-100 transition-colors"
                        onClick={() =>
                          handleCardClick("Find family activities")
                        }
                      >
                        <img
                          src="/images/family-pyramids.jpg"
                          alt="Family with children exploring the Great Pyramids of Giza on a sunny day"
                          className="w-full h-24 object-cover rounded-lg mb-3"
                          onError={(e) => {
                            e.currentTarget.src =
                              "https://images.unsplash.com/photo-1539650116574-75c0c6d4d6d7?w=180&h=120&fit=crop&auto=format&q=80";
                          }}
                        />
                        <p className="text-sm font-normal text-gray-800">
                          The pyramid of Giza
                        </p>
                      </div>
                    </div>
                  )}

                  {/* AI Assistant Card - Only show if no messages */}
                  {messages.length === 0 && (
                    <div
                      className="relative rounded-xl overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
                      onClick={() =>
                        handleCardClick("Discover hidden gems with AI")
                      }
                    >
                      <div className="bg-gradient-to-br from-amber-400 via-orange-500 to-red-600 h-32 flex items-center justify-center relative">
                        <div className="absolute inset-0 bg-black bg-opacity-10"></div>
                        <div className="flex items-center gap-4 z-10">
                          <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center">
                            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
                              <div className="w-4 h-4 bg-gradient-to-br from-amber-500 to-red-500 rounded-full"></div>
                            </div>
                          </div>
                          <div className="w-16 h-16 bg-white/30 backdrop-blur-sm rounded-full flex items-center justify-center">
                            <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center">
                              <svg
                                className="w-5 h-5 text-orange-500"
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
                          </div>
                        </div>
                      </div>
                      <div className="absolute bottom-3 left-4">
                        <p className="text-white font-medium text-base">
                          Discover hidden gems with AI
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Chat Messages */}
                  {messages.map((message) => (
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
                            : "bg-[#DC143C] text-white"
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
                </>
              ) : (
                <>
                  {/* My Trip Content */}
                  <div className="text-center space-y-6">
                    <h2 className="text-3xl font-normal text-[#DC143C] leading-tight">
                      Plan your next
                      <br />
                      Egyptian adventure
                    </h2>

                    {/* Login Button - Properly sized */}
                    <button className="text-[#DC143C] border border-[#DC143C] hover:bg-[#DC143C] hover:text-white px-6 py-2 text-sm font-normal rounded-full transition-colors flex items-center space-x-2 mx-auto">
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
                          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                        />
                      </svg>
                      <span>Log in to view trip</span>
                    </button>
                  </div>

                  {/* Main Trip Planning Card with Egyptian Image */}
                  <div className="relative rounded-xl overflow-hidden cursor-pointer hover:shadow-md transition-shadow">
                    <img
                      src="/images/ancient_tour.jpg"
                      alt="Ancient Egypt temples and monuments including Karnak and Luxor with hieroglyphics"
                      className="w-full h-48 object-cover"
                      onError={(e) => {
                        e.currentTarget.src =
                          "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?w=450&h=280&fit=crop&auto=format&q=80";
                      }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-black/20 to-transparent"></div>
                    <div className="absolute bottom-4 left-4">
                      <p className="text-white font-medium text-base">
                        Plan an ancient Egypt tour
                      </p>
                    </div>
                  </div>

                  {/* Trip Suggestion Cards with Egyptian Images */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white rounded-xl overflow-hidden cursor-pointer hover:shadow-md transition-shadow border border-gray-100">
                      <img
                        src="/images/red-sea-diving.jpg"
                        alt="Crystal clear Red Sea waters with vibrant coral reefs and tropical fish"
                        className="w-full h-24 object-cover"
                        onError={(e) => {
                          e.currentTarget.src =
                            "https://images.unsplash.com/photo-1544551763-77ef2d0cfc6c?w=180&h=120&fit=crop&auto=format&q=80";
                        }}
                      />
                      <div className="p-3">
                        <p className="text-sm font-normal text-gray-800">
                          Plan a 5-day Red Sea diving trip
                        </p>
                      </div>
                    </div>

                    <div className="bg-white rounded-xl overflow-hidden cursor-pointer hover:shadow-md transition-shadow border border-gray-100">
                      <img
                        src="/images/cairo-food.jpg"
                        alt="Delicious traditional Egyptian dishes including koshari, falafel and fresh bread"
                        className="w-full h-24 object-cover"
                        onError={(e) => {
                          e.currentTarget.src =
                            "https://images.unsplash.com/photo-1590846406792-0adc7f938f1d?w=180&h=120&fit=crop&auto=format&q=80";
                        }}
                      />
                      <div className="p-3">
                        <p className="text-sm font-normal text-gray-800">
                          Plan a 2-day Desert Safari
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Take me to chat button */}
                  <button
                    onClick={() => setActiveTab("Chat")}
                    className="w-full bg-[#B8860B] hover:bg-[#A0750A] text-white py-4 rounded-xl font-normal text-base transition-colors"
                  >
                    Take me to the chat
                  </button>
                </>
              )}
            </div>

            {/* Input Area */}
            <div className="p-6 border-t border-gray-200">
              <div className="flex items-center gap-3 bg-gray-50 rounded-full px-5 py-3">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Start a conversation..."
                  className="flex-1 border-none bg-transparent focus:outline-none placeholder:text-gray-500 text-base font-normal"
                  disabled={isLoading}
                />
                <button className="p-2 hover:bg-gray-200 rounded-full transition-colors">
                  <svg
                    className="w-5 h-5 text-gray-500"
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
                <button
                  onClick={handleSendMessage}
                  disabled={isLoading || !inputMessage.trim()}
                  className="w-10 h-10 bg-[#DC143C] rounded-full flex items-center justify-center disabled:opacity-50"
                >
                  <div className="w-7 h-7 bg-white rounded-full flex items-center justify-center">
                    <svg
                      className="w-4 h-4 text-[#DC143C]"
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
                </button>
              </div>
              <p className="text-sm text-gray-500 text-center mt-3 font-normal">
                AI assistance in use. Check official travel sources
              </p>
            </div>
          </div>
        ) : (
          /* Collapsed widget with milky background and circular Egypt banner */
          <div
            className="bg-gray-50/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-3 cursor-pointer hover:shadow-xl transition-shadow w-64"
            onClick={() => setIsOpen(true)}
          >
            <div className="flex items-center gap-3">
              {/* Circular Egypt Banner */}
              <div className="w-12 h-12 bg-[#DC143C] rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-white font-medium text-sm">EGYPT</span>
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 mb-1">
                  Need some help?
                </p>
                <p className="text-xs text-gray-600 font-normal">Let's chat</p>
              </div>

              {/* Online indicator */}
              <div className="w-3 h-3 bg-green-400 rounded-full flex-shrink-0"></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EgyptTourismChatbot;
