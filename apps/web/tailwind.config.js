// FILE LOCATION: quantai/apps/web/tailwind.config.js

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // QuantAI design system, carried forward from V1 (ink/paper/brass palette)
        ink: "#0B0F14",
        paper: "#F7F6F3",
        slate: "#3B4252",
        brass: "#C9A961",
        gain: "#4A7C6F",
        risk: "#A8554A",
      },
      fontFamily: {
        serif: ["Georgia", "Cambria", "serif"], // headlines, narration text
        mono: ["JetBrains Mono", "Consolas", "monospace"], // all numeric figures
        sans: ["Inter", "sans-serif"], // UI chrome/labels
      },
    },
  },
  plugins: [],
};
