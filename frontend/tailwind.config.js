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
            300: '#FDBA74',
            400: '#FB923C',
            500: '#F97316',
            600: '#EA580C',
            700: '#C2410C',
            800: '#9A3412',
            900: '#7C2D12',
          },
          charcoal: {
            50: '#F5F5F4',
            100: '#E7E5E4',
            200: '#D6D3D1',
            300: '#A8A29E',
            400: '#78716C',
            500: '#57534E',
            600: '#44403C',
            700: '#292524',
            800: '#1C1917',
            900: '#0C0A09',
          },
          gold: {
            100: '#FEF3C7',
            300: '#FCD34D',
            500: '#F59E0B',
            600: '#D97706',
            700: '#B45309',
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
