import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        /* Emerald — primary brand */
        brand: {
          50:  "#ecfdf5",
          100: "#d1fae5",
          200: "#a7f3d0",
          300: "#6ee7b7",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
          800: "#065f46",
          900: "#064e3b",
          950: "#022c22",
        },
        /* Teal — secondary accent (charts, highlights) */
        accent: {
          50:  "#f0fdfa",
          100: "#ccfbf1",
          200: "#99f6e4",
          300: "#5eead4",
          400: "#2dd4bf",
          500: "#14b8a6",
          600: "#0d9488",
          700: "#0f766e",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      /* Fixed type scale — no arbitrary sizes anywhere in the app.
         11 / 12 / 14 / 15 / 16 / 18 / 20 / 24 / 30 / 36+ (display is fluid). */
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem" }],         // 11px — micro labels, badges
        md:    ["0.9375rem", { lineHeight: "1.5rem" }],       // 15px — emphasized body / buttons
      },
      boxShadow: {
        card:  "0 1px 2px 0 rgba(15,23,42,0.04), 0 1px 3px 0 rgba(15,23,42,0.03)",
        lift:  "0 4px 12px -2px rgba(15,23,42,0.08), 0 2px 4px -1px rgba(15,23,42,0.04)",
        glow:  "0 0 0 3px rgba(5,150,105,0.14)",
        green: "0 8px 24px -6px rgba(5,150,105,0.28)",
        pop:   "0 12px 32px -8px rgba(15,23,42,0.14), 0 4px 12px -4px rgba(15,23,42,0.06)",
      },
      animation: {
        "fade-in":        "fadeIn 0.4s ease-out forwards",
        "slide-up":       "slideUp 0.4s cubic-bezier(0.16,1,0.3,1) forwards",
        "slide-in-right": "slideInRight 0.3s cubic-bezier(0.16,1,0.3,1) forwards",
        "float":          "float 6s ease-in-out infinite",
        "float-slow":     "float 9s ease-in-out infinite",
        "pulse-soft":     "pulseSoft 2.5s ease-in-out infinite",
        "spin-slow":      "spin 3s linear infinite",
        "shimmer":        "shimmer 1.6s linear infinite",
      },
      keyframes: {
        fadeIn:       { from: { opacity: "0" },                                to: { opacity: "1" } },
        slideUp:      { from: { opacity: "0", transform: "translateY(14px)" }, to: { opacity: "1", transform: "translateY(0)" } },
        slideInRight: { from: { opacity: "0", transform: "translateX(24px)" }, to: { opacity: "1", transform: "translateX(0)" } },
        float:        { "0%,100%": { transform: "translateY(0px)" },           "50%": { transform: "translateY(-10px)" } },
        pulseSoft:    { "0%,100%": { opacity: "1" },                           "50%": { opacity: "0.55" } },
        shimmer:      { from: { backgroundPosition: "200% 0" },                to: { backgroundPosition: "-200% 0" } },
      },
      backgroundImage: {
        "gradient-brand":  "linear-gradient(135deg, #047857 0%, #059669 55%, #0d9488 100%)",
        "gradient-hero":   "linear-gradient(160deg, #ecfdf5 0%, #f0fdfa 55%, #ffffff 100%)",
        "gradient-card":   "linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)",
        "gradient-aurora": "linear-gradient(135deg, #064e3b 0%, #047857 40%, #0f766e 75%, #134e4a 100%)",
        "gradient-subtle": "linear-gradient(180deg, #f8fafc 0%, #ffffff 100%)",
        "gradient-gold":   "linear-gradient(135deg, #d97706 0%, #f59e0b 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
