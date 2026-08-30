/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // PathMind brand palette
        brand: {
          50:  "#f0f4ff",
          100: "#dde5ff",
          200: "#c3cffe",
          300: "#9baff9",
          400: "#7284f4",
          500: "#5261ea",
          600: "#3d46d9",
          700: "#3237bc",
          800: "#2c3098",
          900: "#292e78",
          950: "#1b1d49",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["Fira Code", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s ease-in-out infinite",
        "glow": "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        glow: {
          from: { boxShadow: "0 0 5px #5261ea, 0 0 10px #5261ea" },
          to:   { boxShadow: "0 0 15px #5261ea, 0 0 30px #5261ea" },
        },
      },
    },
  },
  plugins: [],
};
