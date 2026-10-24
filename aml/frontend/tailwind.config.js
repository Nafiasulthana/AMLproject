/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          950: '#0B0F14',
          900: '#111820',
          850: '#151D26',
          800: '#202A35',
          700: '#2D3A4B',
          600: '#415166',
          500: '#5E6A78',
          400: '#8995A3',
          300: '#B0BAC5',
          200: '#D1D9E0',
          100: '#E8EDF2',
        },
        workstation: {
          bg: '#0B0F14',
          surface: '#111820',
          panel: '#151D26',
          border: '#202A35',
          text: '#E8EDF2',
          muted: '#8995A3',
          dim: '#5E6A78',
          blue: '#3B82F6',
          critical: '#EF4444',
          warning: '#F59E0B',
          success: '#22C55E',
        }
      }
    },
  },
  plugins: [],
}
