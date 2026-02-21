/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "#09090b",
                card: "#18181b",
                border: "#27272a",
                primary: {
                    DEFAULT: "#6366f1",
                    hover: "#4f46e5",
                },
                accent: "#a855f7",
                muted: "#71717a",
            },
        },
    },
    plugins: [],
};
