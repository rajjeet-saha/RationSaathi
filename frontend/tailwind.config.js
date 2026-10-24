/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f7f2",
          100: "#dcefdf",
          200: "#b9dfc0",
          300: "#8cc99a",
          400: "#5aac70",
          500: "#378d51",
          600: "#27743f",
          700: "#1f5d34",
          800: "#14532d",
          900: "#0f3f23",
          950: "#072815"
        },
        canvas: "#fbf8f1",
        ink: "#1f2933",
        muted: "#52606d",
        line: "#d9d2c4",
        warning: "#92400e",
        warningBg: "#fef3c7",
        danger: "#991b1b",
        dangerBg: "#fee2e2",
        infoBg: "#eef2f7",
        unknownBg: "#eceff1"
      },
      fontFamily: {
        sans: ["Inter", "Noto Sans", "Noto Sans Devanagari", "Noto Sans Bengali", "Noto Sans Telugu", "system-ui", "sans-serif"]
      },
      boxShadow: {
        card: "0 1px 2px rgba(31, 41, 51, 0.06), 0 8px 24px rgba(31, 41, 51, 0.05)"
      },
      borderRadius: {
        xl: "0.9rem",
        "2xl": "1.25rem"
      }
    }
  },
  plugins: []
};
