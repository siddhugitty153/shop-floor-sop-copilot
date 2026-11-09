/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        industrial: {
          bg: "#090D16",
          card: "#111827",
          border: "#1F2937",
          accent: "#F59E0B",
          emergency: "#EF4444",
          verified: "#10B981"
        }
      }
    },
  },
  plugins: [],
}

