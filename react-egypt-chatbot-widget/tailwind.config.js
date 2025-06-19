/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        "egypt-gold": "#d4a574",
        "egypt-blue": "#1e40af",
        "egypt-sand": "#f5deb3",
        "pyramid-brown": "#8b4513",
      },
      animation: {
        "slide-in-from-bottom": "slideInFromBottom 0.3s ease-out",
        "slide-in-from-right": "slideInFromRight 0.3s ease-out",
        "scale-up": "scaleUp 0.3s ease-out",
      },
      keyframes: {
        slideInFromBottom: {
          "0%": { transform: "translateY(100%)" },
          "100%": { transform: "translateY(0)" },
        },
        slideInFromRight: {
          "0%": { transform: "translateX(100%)" },
          "100%": { transform: "translateX(0)" },
        },
        scaleUp: {
          "0%": { transform: "scale(0.95)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
