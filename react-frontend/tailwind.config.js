/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#1a56db",
          50: "#f0f6ff",
          100: "#e0ecff",
          200: "#c7d7fe",
          300: "#a4bcfd",
          400: "#8098fa",
          500: "#6576f5",
          600: "#4e56e8",
          700: "#4340cf",
          800: "#3835a6",
          900: "#303184",
        },
        secondary: {
          DEFAULT: "#14b8a6",
          50: "#effcf9",
          100: "#c7f7ef",
          200: "#95ece1",
          300: "#62dace",
          400: "#34c5b8",
          500: "#14b8a6",
          600: "#0c9588",
          700: "#0d756c",
          800: "#0f5c55",
          900: "#124a46",
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
      boxShadow: {
        chatbox:
          "0 0 25px -5px rgba(0, 0, 0, 0.1), 0 0 10px -5px rgba(0, 0, 0, 0.04)",
      },
    },
  },
  plugins: [],
};
