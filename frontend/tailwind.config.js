/** @type {import('tailwindcss').Config} */

function withOpacity(variableName) {
  return ({ opacityValue }) => {
    if (opacityValue !== undefined) {
      return `rgba(var(${variableName}), ${opacityValue})`;
    }
    return `rgb(var(${variableName}))`;
  };
}

export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: withOpacity('--background-rgb'),
        surface: withOpacity('--surface-rgb'),
        'surface-muted': withOpacity('--surface-muted-rgb'),
        border: withOpacity('--border-rgb'),
        'border-subtle': withOpacity('--border-subtle-rgb'),
        'text-primary': withOpacity('--text-primary-rgb'),
        'text-secondary': withOpacity('--text-secondary-rgb'),
        accent: withOpacity('--accent-rgb'),
        'accent-soft': withOpacity('--accent-soft-rgb'),
        success: withOpacity('--success-rgb'),
        warning: withOpacity('--warning-rgb'),
        danger: withOpacity('--danger-rgb'),

        // Forest, teal & mint color palette
        forest: {
          50: '#f2f8f5',
          100: '#e1efe8',
          200: '#c5dfd3',
          300: '#9ec7b5',
          400: '#6fa891',
          500: '#43836d',
          600: '#2b6552',
          700: '#1d4f40',
          800: '#13392e',
          900: '#0e2921',
          950: '#071612',
        },
        teal: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },
        mint: {
          DEFAULT: '#d9f3e9',
          light: '#eef9f4',
          dark: '#65c7a6',
        },
        coral: {
          DEFAULT: '#ef7777',
          light: '#fdf2f2',
          dark: '#c94b4b',
        },

        // Backwards-compatible aliases
        dark: '#101714',
        'dark-bg': '#101714',
        'dark-sidebar': '#0d1310',
        'dark-surface': '#17211c',
        'dark-card': '#17211c',
        'dark-border': '#304138',
        'dark-border-subtle': '#22332a',
        'dark-input': '#131c17',
        navy: '#101714',
        'navy-light': '#17211c',
        offwhite: '#F4F4F5',
        signal: '#0f766e',
        slate: '#a5b5aa',
      },
      fontFamily: {
        heading: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        body:    ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '8px',
        md: '10px',
        lg: '12px',
        xl: '16px',
        '2xl': '20px',
      },
      boxShadow: {
        soft: '0 2px 16px 0 rgba(0,0,0,0.08)',
        'soft-dark': '0 2px 16px 0 rgba(0,0,0,0.4)',
        glow: '0 0 20px -3px rgba(15, 118, 110, 0.25)',
      },
    },
  },
  plugins: [],
}
