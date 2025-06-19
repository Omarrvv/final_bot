import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import EgyptTourismChatbot from "./components/EgyptTourismChatbot";
import "./widget.css";

declare global {
  interface Window {
    EgyptChatbot: {
      init: (config?: any) => void;
    };
  }
}

const initializeWidget = (config?: any) => {
  // Create widget container
  const containerId = "egypt-tourism-chatbot-widget";
  let container = document.getElementById(containerId);

  if (!container) {
    container = document.createElement("div");
    container.id = containerId;
    document.body.appendChild(container);
  }

  // Pass config to the widget
  const widgetConfig = {
    apiUrl: config?.apiUrl || "http://localhost:5050",
    theme: config?.theme || "light",
    position: config?.position || "bottom-right",
    language: config?.language || "en",
    ...config,
  };

  // Create React root and render the chatbot
  const root = createRoot(container);
  root.render(
    <StrictMode>
      <EgyptTourismChatbot config={widgetConfig} />
    </StrictMode>
  );
};

// Auto-initialize if script is loaded with data-auto-init OR if auto-init config is set
const shouldAutoInit =
  document.currentScript?.getAttribute("data-auto-init") === "true" ||
  (typeof window !== "undefined" &&
    window.EgyptChatbotConfig?.autoInit === true);

if (shouldAutoInit) {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => initializeWidget());
  } else {
    initializeWidget();
  }
}

// Also auto-initialize after a short delay to ensure everything is ready
if (typeof window !== "undefined") {
  setTimeout(() => {
    const container = document.getElementById("egypt-tourism-chatbot-widget");
    // Auto-initialize if no container exists and either autoInit is true OR no explicit config is set
    const shouldAutoInit =
      !container &&
      (window.EgyptChatbotConfig?.autoInit === true ||
        typeof window.EgyptChatbotConfig === "undefined");

    if (shouldAutoInit) {
      console.log("🚀 Auto-initializing Egypt Tourism Chatbot widget");
      initializeWidget(window.EgyptChatbotConfig || {});
    }
  }, 100);
}

// Export for manual initialization
const EgyptChatbot = {
  init: initializeWidget,
};

// Attach to window
if (typeof window !== "undefined") {
  window.EgyptChatbot = EgyptChatbot;
}

// Export for webpack
export default EgyptChatbot;
