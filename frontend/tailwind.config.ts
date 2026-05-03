import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        surface: "var(--surface)",
        page: "var(--page)",
        text: "var(--text)",
        muted: "var(--muted)",
        line: "var(--line)",
        accent: "var(--accent)"
      },
      boxShadow: {
        quiet: "0 18px 48px rgba(30, 24, 18, 0.08)"
      },
      maxWidth: {
        reader: "46rem"
      }
    }
  },
  plugins: []
};

export default config;
