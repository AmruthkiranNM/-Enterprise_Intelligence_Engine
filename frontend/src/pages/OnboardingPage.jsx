import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Loader2, Globe, Zap, CheckCircle } from "lucide-react";
import { onboardCompany } from "../api";

export default function OnboardingPage() {
    const navigate = useNavigate();
    const user = JSON.parse(localStorage.getItem("user") || "{}");
    const [url, setUrl] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const token = localStorage.getItem("token");
            const catalog = await onboardCompany(url, token);
            // Store catalog locally so Dashboard can access it immediately
            localStorage.setItem("serviceCatalog", JSON.stringify(catalog));
            // Update user onboarded status
            const updatedUser = { ...user, is_onboarded: true };
            localStorage.setItem("user", JSON.stringify(updatedUser));
            navigate("/dashboard");
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background flex items-center justify-center px-4 relative">
            <div className="fixed top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full pointer-events-none" style={{ background: "radial-gradient(circle, rgba(110,231,183,0.09) 0%, transparent 70%)" }} />

            <motion.div
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="relative z-10 w-full max-w-lg glass-card p-8 sm:p-10 space-y-8"
            >
                {/* Header */}
                <div className="space-y-2">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                            <Zap size={16} className="text-white" />
                        </div>
                        <span className="font-bold text-zinc-400 text-sm tracking-tight">Lead Intelligence</span>
                    </div>
                    <h2 className="text-2xl font-black text-zinc-100">
                        Welcome{user.name ? `, ${user.name.split(" ")[0]}` : ""}! 👋
                    </h2>
                    <p className="text-zinc-400 text-sm leading-relaxed">
                        To personalize prospect analysis and gap detection, we first need to understand <strong className="text-zinc-200">your company</strong>. Enter your website below and our AI will build your Service Catalog.
                    </p>
                </div>

                {/* Steps mini-preview */}
                <div className="grid grid-cols-3 gap-3">
                    {[
                        { icon: Globe, label: "Crawl Website" },
                        { icon: CheckCircle, label: "Extract Services" },
                        { icon: Zap, label: "Build Catalog" }
                    ].map(({ icon: Icon, label }, i) => (
                        <div key={i} className="flex flex-col items-center gap-2 p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/60 text-center">
                            <Icon size={18} className="text-primary" />
                            <span className="text-[11px] font-semibold text-zinc-400">{label}</span>
                        </div>
                    ))}
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-1.5">
                        <label className="text-xs font-semibold text-zinc-500 uppercase tracking-widest">Your Company Website</label>
                        <input
                            type="text"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            placeholder="e.g. https://yourcompany.com"
                            required
                            className="input-field w-full"
                        />
                    </div>

                    {error && (
                        <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{error}</p>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-60"
                    >
                        {loading ? <Loader2 size={16} className="animate-spin" /> : <Globe size={16} />}
                        {loading ? "Crawling and analyzing site..." : "Analyze My Company"}
                    </button>
                </form>
            </motion.div>
        </div>
    );
}
