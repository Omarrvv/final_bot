# Frontend Development Guidelines

This document outlines basic guidelines for working on the `react-frontend/` part of the project, based on the current observed structure.

## 1. Technology Stack

*   **Framework:** React
*   **Language:** JavaScript
*   **Styling:** Tailwind CSS (use utility classes)
*   **HTTP Client:** Axios (via `src/services/ChatbotService.js`)

## 2. Project Structure (`react-frontend/src/`)

*   **`App.js`:** Main application component.
*   **`components/`:** Contains reusable UI components (e.g., `EgyptTourismChatbot.js`). Create new components here.
*   **`services/`:** Contains modules for interacting with the backend API (e.g., `ChatbotService.js`). All API calls should go through this layer.
*   **`utils/`:** Contains utility functions (e.g., date/text formatting).
*   **`index.css`:** Main CSS file (primarily for Tailwind base/components/utilities directives).
*   **`index.js`:** Application entry point.

## 3. API Interaction

*   Use the existing `ChatbotService.js` singleton for all backend API calls.
*   Ensure calls handle potential errors gracefully and update the UI accordingly (e.g., show error messages).
*   Respect the API endpoints defined and documented by the backend (Swagger at `/api/docs`).
*   Handle CSRF tokens as implemented in `ChatbotService.js`.

## 4. State Management

*   Current state management appears to be handled within components (`useState`, `useEffect`).
*   For more complex state, consider React Context API or a dedicated library (like Zustand or Redux Toolkit) if needed, but discuss before introducing new major dependencies.

## 5. Styling

*   Utilize **Tailwind CSS utility classes** primarily for styling.
*   Define custom base styles or reusable component styles in `index.css` only when necessary.
*   Ensure responsiveness and cross-browser compatibility.

## 6. Coding Style

*   Follow standard JavaScript/React best practices.
*   Use ESLint (config in `.eslintrc.json`) to maintain code quality. Run `npm run lint` (or configure IDE) regularly.
*   Consider adding Prettier for consistent code formatting.

## 7. Testing

*   Use Jest for testing (configured via `jest.config.js`).
*   Write unit tests for components and utility functions.
*   Write integration tests for component interactions and service calls (using mocks).
*   Aim to fix the existing `npm test` configuration warnings and improve test coverage.

## 8. Component Design

*   Favor functional components with hooks.
*   Break down large components into smaller, reusable ones.
*   Use PropTypes or TypeScript (if adopted later) for component prop validation.