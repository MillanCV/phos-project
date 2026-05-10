import type { Config } from 'tailwindcss'

export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: '#070b14',
        foreground: '#e8edf7',
        muted: '#111a2c',
        mutedForeground: '#94a3b8',
        card: '#0b1221',
        cardForeground: '#e8edf7',
        border: '#1f2a44',
        input: '#131f36',
        primary: '#22d3ee',
        primaryForeground: '#06212a',
        warning: '#f59e0b',
        danger: '#ef4444',
        success: '#10b981',
      },
      borderRadius: {
        lg: '0.9rem',
        md: '0.7rem',
        sm: '0.55rem',
      },
      boxShadow: {
        panel: '0 10px 30px rgba(2, 6, 23, 0.45)',
      },
    },
  },
  plugins: [],
} satisfies Config
