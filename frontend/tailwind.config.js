/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: "#1a1a1a",
          neonBlue: "#00f0ff",
          neonPurple: "#bc13fe",
          dark: "#0f0f0f",
          panel: "#2a2a2a",
        },
      },
      fontFamily: {
        orbitron: ['"Orbitron"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
