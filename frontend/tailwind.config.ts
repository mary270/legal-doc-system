import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#0a0f1e',
          sidebar: '#0d1426',
          card: '#111827',
          'card-hover': '#1a2235',
        },
        border: {
          DEFAULT: '#1e2d47',
          subtle: '#162038',
        },
        primary: {
          DEFAULT: '#2563eb',
          hover: '#3b82f6',
        },
        accent: {
          gold: '#d97706',
          'gold-light': '#f59e0b',
        },
        text: {
          primary: '#f1f5f9',
          secondary: '#94a3b8',
          muted: '#4b5563',
        },
        success: {
          DEFAULT: '#16a34a',
          light: '#22c55e',
        },
        error: {
          DEFAULT: '#dc2626',
          light: '#ef4444',
        },
        warning: {
          DEFAULT: '#ca8a04',
          light: '#eab308',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
