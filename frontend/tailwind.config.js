/** @type {import('tailwindcss').Config} */
// Components use hand-written semantic CSS classes (src/index.css), not
// Tailwind utilities — this config exists so the @tailwind directives don't
// error, and so these tokens are available if a component ever needs one.
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        "ink-base": "#131515",
        panel: "#1C1F1E",
        "panel-2": "#262A28",
        "text-primary": "#EDEFEC",
        "text-soft": "#8A9088",
        "jurisdiction-1": "#C97D4A",
        "jurisdiction-2": "#4A8FA3",
        "jurisdiction-3": "#8C6FB0",
        "jurisdiction-4": "#7FA36E",
        "status-green": "#5CA97E",
        "status-red": "#C4634F",
        "status-amber": "#C4954A",
        "status-violet": "#B0709E",
      },
      fontFamily: {
        sans: ["Sora", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
    },
  },
  plugins: [],
}
