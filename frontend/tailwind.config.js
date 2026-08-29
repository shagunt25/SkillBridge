/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: '#0F1729',
        'navy-light': '#1A2642',
        offwhite: '#F7F8FA',
        signal: '#3B5BFF',
        amber: '#FFB648',
        green: '#22C58B',
        slate: '#6B7280',
      },
      fontFamily: {
        heading: ['"Space Grotesk"', 'Sora', 'sans-serif'],
        body:    ['"Inter"', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '10px',
        lg: '12px',
        xl: '16px',
      },
      boxShadow: {
        soft: '0 2px 16px 0 rgba(15,23,41,0.18)',
      },
    },
  },
  plugins: [],
}
