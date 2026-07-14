/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        "ink-navy": "#17264D",
        "ink-navy-deep": "#0E1730",
        parchment: "#F6EFDD",
        "parchment-dim": "#D8B978",
        kraft: "#FBF3E1",
        "kraft-shadow": "#E3CD98",
        "ink-text": "#1E2440",
        "ink-text-soft": "#565C7C",
        "seal-green": "#146B42",
        "seal-red": "#C13B2A",
        "gazette-gold": "#D4941A",
        "archive-plum": "#5A3E8C",
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        body: ["Newsreader", "serif"],
        mono: ["IBM Plex Mono", "monospace"],
        ui: ["Space Grotesk", "sans-serif"],
        scrawl: ["Caveat", "cursive"],
      },
    },
  },
  plugins: [],
}
