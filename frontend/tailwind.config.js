/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        kalpa: {
          paper: {
            DEFAULT: '#F3E8D2',
            light: '#F8F0E1',
            deep: '#E8D6B7',
            panel: '#F1E4CC',
            card: '#FAF2E3',
          },
          brown: {
            DEFAULT: '#79563F',
            dark: '#4A3427',
            muted: '#92745A',
            light: '#BFA47D',
          },
          ink: {
            DEFAULT: '#28231F',
            muted: '#62584F',
          },
          orange: {
            DEFAULT: '#C96A3A',
            dark: '#A9552F',
            soft: '#E8B79A',
          },
          green: {
            DEFAULT: '#006F5F',
            dark: '#075648',
          },
          border: 'rgba(104, 76, 53, 0.18)',
          ivory: {
            50: '#FAF8F5',
            100: '#F5EFEB',
            200: '#EFE8DE',
            300: '#E4DACB',
            400: '#D5C7B2',
          },
          saffron: {
            50: '#FFF7ED',
            100: '#FFEDD5',
            200: '#FED7AA',
            300: '#E8B79A',
            400: '#D98254',
            500: '#C96A3A',
            600: '#C96A3A',
            700: '#A9552F',
            800: '#8A4222',
            900: '#683119',
          },
          charcoal: {
            50: '#F5F5F4',
            100: '#E7E5E4',
            200: '#D6D3D1',
            300: '#A8A29E',
            400: '#78716C',
            500: '#62584F',
            600: '#4A3427',
            700: '#28231F',
            800: '#28231F',
            900: '#1A1614',
          },
          gold: {
            100: '#FEF3C7',
            300: '#FCD34D',
            500: '#92745A',
            600: '#79563F',
            700: '#4A3427',
          }
        }
      },
      fontFamily: {
        sans: ['Inter', 'Outfit', 'system-ui', 'sans-serif'],
      },
      animation: {
        'spin-slow': 'spin 15s linear infinite',
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float-slow': 'float 20s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px) scale(1)' },
          '50%': { transform: 'translateY(-12px) scale(1.02)' },
        }
      }
    },
  },
  plugins: [],
}
