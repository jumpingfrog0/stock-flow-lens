import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "#d8dde6",
        panel: "#ffffff",
        ink: "#111827",
        muted: "#65758b",
        positive: "#178f5d",
        negative: "#c2413b",
        accent: "#2563eb",
      },
      boxShadow: {
        surface: "0 1px 2px rgba(15, 23, 42, 0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
