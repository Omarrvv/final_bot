import React, { useState, useEffect, useRef } from "react";
import {
  Send,
  Map,
  Info,
  Calendar,
  Hotel,
  Camera,
  Menu,
  Loader,
  Globe,
  ChevronDown,
  X,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
} from "lucide-react";
import ChatbotService from "../services/ChatbotService";
import { formatTime } from "../utils/dateUtils";
import {
  processMarkdown,
  getTextDirection,
  getLocaleCode,
} from "../utils/textUtils";

const EgyptTourismChatbot = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [language, setLanguage] = useState("en");
  const [suggestions, setSuggestions] = useState([]);
  const [isOpen, setIsOpen] = useState(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    async function initializeChat() {
      try {
        setIsLoading(true);

        const sessionData = await ChatbotService.createSession();
        setSessionId(sessionData.session_id);

        await ChatbotService.getLanguages();

        const initialMessage = {
          role: "assistant",
          content:
            language === "en"
              ? "Hello! I'm your Egyptian tourism guide. How can I help with your travel plans today?"
              : "مرحبًا! أنا دليل السياحة المصري. كيف يمكنني مساعدتك في خطط سفرك اليوم؟",
          timestamp: new Date(),
        };

        setMessages([initialMessage]);

        const suggestionsData = await ChatbotService.getSuggestions(
          sessionData.session_id,
          language
        );

        setSuggestions(suggestionsData.suggestions || []);
      } catch {
        // Handle error without logging
      } finally {
        setIsLoading(false);
      }
    }

    initializeChat();
  }, [language]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = {
      id: new Date().getTime().toString(),
      text: inputValue,
      sender: "user",
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await ChatbotService.sendMessage(
        inputValue,
        sessionId,
        language
      );

      if (!sessionId && response.session_id) {
        setSessionId(response.session_id);
      }

      const botMessage = {
        id: response.message_id || new Date().getTime().toString() + "-bot",
        text: response.message || "Sorry, I couldn't process your request.",
        sender: "bot",
        timestamp: response.timestamp || new Date().toISOString(),
        feedback: response.allow_feedback,
        suggestions: response.suggestions || [],
        isError: !response.success,
      };

      setMessages((prev) => [...prev, botMessage]);

      if (response.suggestions && response.suggestions.length > 0) {
        setSuggestions(response.suggestions);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: new Date().getTime().toString() + "-error",
          text: "I apologize, but I experienced an error. Please try again later.",
          sender: "bot",
          isError: true,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInputValue(suggestion.text || suggestion);

    setTimeout(() => {
      const event = { preventDefault: () => {} };
      handleSubmit(event);
    }, 100);
  };

  const toggleLanguage = () => {
    const newLanguage = language === "en" ? "ar" : "en";
    setLanguage(newLanguage);
  };

  const clearConversation = async () => {
    try {
      setIsLoading(true);

      const sessionData = await ChatbotService.createSession();
      setSessionId(sessionData.session_id);

      const initialMessage = {
        role: "assistant",
        content:
          language === "en"
            ? "Hello! I'm your Egyptian tourism guide. How can I help with your travel plans today?"
            : "مرحبًا! أنا دليل السياحة المصري. كيف يمكنني مساعدتك في خطط سفرك اليوم؟",
        timestamp: new Date(),
      };

      setMessages([initialMessage]);
      setSuggestions([]);
    } catch {
      // Handle error without logging
    } finally {
      setIsLoading(false);
    }
  };

  const toggleChatWindow = () => {
    setIsOpen((prev) => !prev);
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen((prev) => !prev);
  };

  const direction = getTextDirection(language);

  const locale = getLocaleCode(language);

  const uiText = {
    placeholder: language === "en" ? "Type your message..." : "اكتب رسالتك...",
    send: language === "en" ? "Send" : "إرسال",
    suggestionsLabel: language === "en" ? "Suggestions:" : "اقتراحات:",
    minimize: language === "en" ? "Minimize" : "تصغير",
    maximize: language === "en" ? "Maximize" : "تكبير",
    menuTitle: language === "en" ? "Menu" : "القائمة",
    clearChat: language === "en" ? "Clear Chat" : "مسح المحادثة",
    language: language === "en" ? "اللغة العربية" : "English",
    destinations: language === "en" ? "Destinations" : "الوجهات",
    attractions: language === "en" ? "Attractions" : "المعالم السياحية",
    planning: language === "en" ? "Trip Planning" : "تخطيط الرحلة",
    accommodation: language === "en" ? "Accommodation" : "الإقامة",
    about: language === "en" ? "About Egypt" : "عن مصر",
    thinking: language === "en" ? "Thinking..." : "جاري التفكير...",
    error:
      language === "en"
        ? "Something went wrong. Please try again."
        : "حدث خطأ ما. يرجى المحاولة مرة أخرى.",
  };

  return (
    <div
      className={`fixed bottom-4 ${
        language === "ar" ? "left-4" : "right-4"
      } max-w-lg w-full md:w-96 
                  shadow-lg rounded-lg overflow-hidden ${
                    isOpen ? "h-[500px]" : "h-14"
                  } flex flex-col
                  transition-all duration-300 ease-in-out bg-white shadow-chatbox z-50`}
      style={{ direction }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-blue-700 to-blue-900 text-white">
        <div className="flex items-center gap-2">
          {isOpen && (
            <button
              onClick={toggleMobileMenu}
              className="md:hidden p-1 rounded-full hover:bg-blue-800 transition"
              aria-label={uiText.menuTitle}
            >
              <Menu size={18} />
            </button>
          )}
          <h3 className="font-bold text-sm">
            {language === "en" ? "Egypt Tourism Guide" : "دليل السياحة المصرية"}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={toggleLanguage}
            className="p-1 rounded-full hover:bg-blue-800 transition"
            aria-label={
              language === "en" ? "Switch to Arabic" : "Switch to English"
            }
          >
            <Globe size={18} />
          </button>
          <button
            onClick={toggleChatWindow}
            className="p-1 rounded-full hover:bg-blue-800 transition"
            aria-label={isOpen ? uiText.minimize : uiText.maximize}
          >
            {isOpen ? <ChevronDown size={18} /> : <MessageSquare size={18} />}
          </button>
        </div>
      </div>

      {isOpen && (
        <>
          {/* Mobile Menu Overlay */}
          {isMobileMenuOpen && (
            <div
              className="absolute inset-0 bg-white z-10 p-4"
              style={{ top: "50px", height: "calc(100% - 50px)" }}
            >
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold">{uiText.menuTitle}</h3>
                <button
                  onClick={toggleMobileMenu}
                  className="p-1 rounded-full hover:bg-gray-100"
                >
                  <X size={18} />
                </button>
              </div>
              <div className="space-y-4">
                <button className="block w-full text-left p-2 rounded hover:bg-gray-100">
                  <div className="flex items-center gap-2">
                    <Map size={18} />
                    <span>{uiText.destinations}</span>
                  </div>
                </button>
                <button className="block w-full text-left p-2 rounded hover:bg-gray-100">
                  <div className="flex items-center gap-2">
                    <Camera size={18} />
                    <span>{uiText.attractions}</span>
                  </div>
                </button>
                <button className="block w-full text-left p-2 rounded hover:bg-gray-100">
                  <div className="flex items-center gap-2">
                    <Calendar size={18} />
                    <span>{uiText.planning}</span>
                  </div>
                </button>
                <button className="block w-full text-left p-2 rounded hover:bg-gray-100">
                  <div className="flex items-center gap-2">
                    <Hotel size={18} />
                    <span>{uiText.accommodation}</span>
                  </div>
                </button>
                <button className="block w-full text-left p-2 rounded hover:bg-gray-100">
                  <div className="flex items-center gap-2">
                    <Info size={18} />
                    <span>{uiText.about}</span>
                  </div>
                </button>
                <hr />
                <button
                  onClick={clearConversation}
                  className="block w-full text-left p-2 rounded hover:bg-gray-100 text-red-600"
                >
                  {uiText.clearChat}
                </button>
              </div>
            </div>
          )}

          {/* Main Chat Area */}
          <div className="flex flex-col flex-grow overflow-hidden">
            {/* Messages container */}
            <div className="flex-grow overflow-y-auto bg-gray-50 p-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`mb-4 max-w-[85%] ${
                    message.role === "user"
                      ? `${
                          language === "ar" ? "ml-auto" : "mr-auto"
                        } bg-blue-100 rounded-tr-lg rounded-tl-lg ${
                          language === "ar" ? "rounded-bl-lg" : "rounded-br-lg"
                        }`
                      : `${
                          language === "ar" ? "mr-auto" : "ml-auto"
                        } bg-white border border-gray-200 rounded-tr-lg rounded-tl-lg ${
                          language === "ar" ? "rounded-br-lg" : "rounded-bl-lg"
                        } shadow-sm`
                  } ${message.isError ? "bg-red-50 border-red-100" : ""}`}
                >
                  <div className="p-3">
                    <div
                      className="text-sm"
                      dangerouslySetInnerHTML={{
                        __html: processMarkdown(message.content),
                      }}
                    />

                    {/* Display media if available */}
                    {message.media && message.media.length > 0 && (
                      <div className="mt-2 space-y-2">
                        {message.media.map((item, mediaIndex) => (
                          <div key={mediaIndex}>
                            {item.type === "image" && (
                              <img
                                src={item.url}
                                alt={item.alt_text || "Image"}
                                className="rounded-md max-w-full"
                              />
                            )}
                            {item.type === "map" && (
                              <iframe
                                src={item.url}
                                title="Map"
                                className="rounded-md w-full h-32"
                                frameBorder="0"
                                allowFullScreen
                              />
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Feedback buttons for bot messages */}
                    {message.role === "assistant" &&
                      message.messageId &&
                      !message.isError && (
                        <div className="mt-2 flex gap-2">
                          <button
                            onClick={() =>
                              ChatbotService.submitFeedback(message.id, 1)
                            }
                            className={`text-xs p-1 rounded-full ${
                              message.feedbackGiven === 1
                                ? "bg-green-100 text-green-600"
                                : "text-gray-400 hover:text-gray-600"
                            }`}
                            aria-label="Thumbs up"
                          >
                            <ThumbsUp size={12} />
                          </button>
                          <button
                            onClick={() =>
                              ChatbotService.submitFeedback(message.id, 0)
                            }
                            className={`text-xs p-1 rounded-full ${
                              message.feedbackGiven === 0
                                ? "bg-red-100 text-red-600"
                                : "text-gray-400 hover:text-gray-600"
                            }`}
                            aria-label="Thumbs down"
                          >
                            <ThumbsDown size={12} />
                          </button>
                        </div>
                      )}
                  </div>
                  <div
                    className={`text-xs text-gray-500 px-3 pb-1 ${
                      language === "ar" ? "text-left" : "text-right"
                    }`}
                  >
                    {formatTime(message.timestamp, locale)}
                  </div>
                </div>
              ))}

              {/* Loading indicator */}
              {isLoading && (
                <div
                  className={`mb-4 max-w-[85%] ${
                    language === "ar" ? "mr-auto" : "ml-auto"
                  } bg-white border border-gray-200 rounded-lg shadow-sm p-3`}
                >
                  <div className="flex items-center gap-2">
                    <Loader size={14} className="animate-spin" />
                    <p className="text-sm text-gray-500">{uiText.thinking}</p>
                  </div>
                </div>
              )}

              {/* Auto-scroll anchor */}
              <div ref={messagesEndRef} />
            </div>

            {/* Suggestions */}
            {suggestions.length > 0 && (
              <div className="px-4 py-2 bg-white border-t border-gray-200 flex-shrink-0">
                <p className="text-xs text-gray-500 mb-2">
                  {uiText.suggestionsLabel}
                </p>
                <div className="flex flex-wrap gap-2">
                  {suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="text-xs bg-gray-100 hover:bg-gray-200 rounded-full px-3 py-1 transition-colors"
                    >
                      {suggestion.text || suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input area */}
            <div className="p-2 bg-white border-t border-gray-200 flex-shrink-0">
              <form onSubmit={handleSubmit} className="flex items-center gap-2">
                <input
                  type="text"
                  value={inputValue}
                  onChange={handleInputChange}
                  placeholder={uiText.placeholder}
                  className="flex-grow p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isLoading}
                  ref={inputRef}
                />
                <button
                  type="submit"
                  className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 transition-colors"
                  disabled={isLoading || !inputValue.trim()}
                >
                  <Send size={18} />
                </button>
              </form>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default EgyptTourismChatbot;
