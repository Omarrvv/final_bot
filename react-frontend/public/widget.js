/**
 * Egypt Tourism Chatbot - Embed Widget
 * This script can be added to any website to embed the chatbot.
 */
(function () {
  // Configuration
  const config = {
    serverUrl: window.egyptChatbotConfig?.serverUrl || "http://localhost:5000",
    chatbotSelector: window.egyptChatbotConfig?.selector || "#egypt-chatbot",
    autoOpen: window.egyptChatbotConfig?.autoOpen || false,
    language: window.egyptChatbotConfig?.language || "en",
  };

  // Create the iframe element
  function createChatbotIframe() {
    const iframe = document.createElement("iframe");
    iframe.src = config.serverUrl;
    iframe.style.border = "none";
    iframe.style.width = "100%";
    iframe.style.height = "500px";
    iframe.style.maxWidth = "400px";
    iframe.style.position = "fixed";
    iframe.style.bottom = "20px";
    iframe.style.right = "20px";
    iframe.style.zIndex = "9999";
    iframe.style.boxShadow = "0 0 20px rgba(0, 0, 0, 0.1)";
    iframe.style.borderRadius = "10px";
    iframe.style.overflow = "hidden";

    // Pass configuration to the iframe
    iframe.onload = function () {
      iframe.contentWindow.postMessage(
        {
          type: "EGYPT_CHATBOT_CONFIG",
          config: {
            language: config.language,
            autoOpen: config.autoOpen,
          },
        },
        config.serverUrl
      );
    };

    return iframe;
  }

  // Initialize when the page is loaded
  window.addEventListener("DOMContentLoaded", function () {
    const containerElement = document.querySelector(config.chatbotSelector);

    if (containerElement) {
      // If a container is specified, embed in that element
      containerElement.appendChild(createChatbotIframe());
    } else {
      // Otherwise, append directly to the body
      document.body.appendChild(createChatbotIframe());
    }

    // Listen for messages from the iframe
    window.addEventListener("message", function (event) {
      if (event.origin !== config.serverUrl) return;

      // Handle events from the chatbot iframe if needed
      if (event.data && event.data.type === "EGYPT_CHATBOT_EVENT") {
        console.log("Egypt Chatbot Event:", event.data.event);

        // Dispatch a custom event that websites can listen for
        const customEvent = new CustomEvent("egyptChatbotEvent", {
          detail: event.data.event,
        });
        window.dispatchEvent(customEvent);
      }
    });
  });
})();
