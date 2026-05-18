import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Marcus Reed design system tokens
        nx: {
          primary: "#1A3B5C",
          secondary: "#EA4313",
          tertiary: "#0B3B8C",
          neutral: "#1A1A1A",
          background: "#F4F1EB",
          surface: "#1A3B5C",
          ink: "#1A1A1A",
          ink2: "#1A3B5C",
          line: "#1A1A1A",
          // dark-mode counterparts
          "dark-bg": "#0B0F1A",
          "dark-surface": "#10172A",
          "dark-ink": "#E7EAF0",
          "dark-line": "#243047",
        },
      },
      fontFamily: {
        display: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "ui-monospace", "monospace"],
      },
      letterSpacing: {
        tightest: "-0.05em",
      },
      borderRadius: {
        pill: "9999px",
      },
      boxShadow: {
        "nx-hard": "4px 4px 0 0 #1A1A1A",
        "nx-glass": "0 1px 1px rgba(255,255,255,0.5) inset, 0 8px 32px rgba(26,59,92,0.08)",
        "nx-glass-dark": "0 1px 1px rgba(255,255,255,0.06) inset, 0 8px 32px rgba(0,0,0,0.45)",
      },
      backdropBlur: {
        xs: "2px",
      },
      transitionTimingFunction: {
        "nx-ease": "cubic-bezier(0.22, 1, 0.36, 1)",
      },
      transitionDuration: {
        "nx-fast": "150ms",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "0% 0%" },
          "100%": { backgroundPosition: "200% 0%" },
        },
        pulseGlow: {
          "0%, 100%": { opacity: "0.6" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        shimmer: "shimmer 2.4s linear infinite",
        "pulse-glow": "pulseGlow 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
