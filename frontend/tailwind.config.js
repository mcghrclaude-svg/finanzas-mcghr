/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Paleta institucional MCGHR
        primary: {
          50:  '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a8a',
        },
        danger:  { 500: '#ef4444', 100: '#fee2e2' },
        warning: { 500: '#f59e0b', 100: '#fef3c7' },
        success: { 500: '#22c55e', 100: '#dcfce7' },
      },
    },
  },
  plugins: [],
}
