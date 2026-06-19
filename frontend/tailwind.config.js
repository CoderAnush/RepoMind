/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: {
          light: '#f8fafc',
          dark: '#0f172a'
        },
        primary: {
          light: '#6366f1',
          dark: '#818cf8'
        },
        secondary: {
          light: '#475569',
          dark: '#cbd5e1'
        },
        card: {
          light: '#ffffff',
          dark: '#1e293b'
        },
        border: {
          light: '#e2e8f0',
          dark: '#334155'
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
