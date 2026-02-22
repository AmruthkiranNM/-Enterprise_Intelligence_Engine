/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "#0d1117",       // deep navy-black (easier on eyes than pure #09090b)
                card: "#161b27",        // rich dark blue-grey card surface
                border: "#2d3a52",        // visible blue-tinted border
                primary: {
                    DEFAULT: "#6ee7b7",       // bright emerald-cyan — stands out clearly
                    hover: "#34d399",
                },
                accent: "#f472b6",          // hot pink accent — vibrant, no contrast issues
                muted: "#94a3b8",          // slate-400 — much more legible than zinc-500
            },
        },
    },
    plugins: [],
};
