import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        accent: "hsl(var(--accent))",
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Landed brand blues, light to dark. 400 is the plane, 600 is the logo's deep blue.
        brand: {
          50: "#EEF8FC",
          100: "#D6EFF9",
          200: "#BFEAF8",
          300: "#8EDDF7",
          400: "#5CC6EA",
          500: "#1FA3D6",
          600: "#007CAC",
          700: "#00668F",
          800: "#004E73",
          900: "#06364A",
          950: "#062431", // "night": sidebar and landing page
        },
      },
      boxShadow: {
        soft: "0 1px 2px rgba(6, 54, 74, 0.05), 0 8px 24px rgba(6, 54, 74, 0.05)",
        lift: "0 2px 4px rgba(6, 54, 74, 0.06), 0 16px 36px rgba(0, 124, 172, 0.10)",
      },
    },
  },
  plugins: [],
};

export default config;
