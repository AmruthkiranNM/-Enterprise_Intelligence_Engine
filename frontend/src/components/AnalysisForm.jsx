import { useState } from "react";
import { Globe, MapPin, Loader2, Zap } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function AnalysisForm({ onResult, onError, onLoading }) {
    const [mode, setMode] = useState("domain");
    const [domain, setDomain] = useState("");
    const [region, setRegion] = useState("");
    const [threshold, setThreshold] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        onLoading(true);

        try {
            const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000";
            const endpoint = mode === "domain" ? "/analyze-domain" : "/analyze-region";
            const body =
                mode === "domain"
                    ? { domain, threshold: threshold || null }
                    : { region, threshold };

            const res = await fetch(`${apiBase}${endpoint}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: "Request failed" }));
                throw new Error(err.detail || "Analysis failed");
            }

            const data = await res.json();
            onResult({ data, mode });
        } catch (err) {
            onError(err.message);
        } finally {
            setLoading(false);
            onLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            {/* Mode Toggle */}
            <div className="flex items-center gap-1 bg-zinc-900 border border-border rounded-xl p-1 w-fit">
                <button
                    type="button"
                    onClick={() => setMode("domain")}
                    className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${mode === "domain"
                            ? "bg-primary text-white shadow-lg shadow-primary/25"
                            : "text-zinc-400 hover:text-zinc-200"
                        }`}
                >
                    <Globe size={15} />
                    Analyze Domain
                </button>
                <button
                    type="button"
                    onClick={() => setMode("region")}
                    className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${mode === "region"
                            ? "bg-primary text-white shadow-lg shadow-primary/25"
                            : "text-zinc-400 hover:text-zinc-200"
                        }`}
                >
                    <MapPin size={15} />
                    Discover Region
                </button>
            </div>

            {/* Inputs */}
            <AnimatePresence mode="wait">
                <motion.div
                    key={mode}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.2 }}
                    className="grid grid-cols-1 sm:grid-cols-2 gap-4"
                >
                    {mode === "domain" ? (
                        <>
                            <div className="space-y-1.5">
                                <label className="text-xs font-medium text-zinc-400 uppercase tracking-widest">
                                    Company Domain
                                </label>
                                <input
                                    type="text"
                                    value={domain}
                                    onChange={(e) => setDomain(e.target.value)}
                                    placeholder="e.g. druva.com"
                                    required
                                    className="input-field w-full"
                                />
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-xs font-medium text-zinc-400 uppercase tracking-widest">
                                    Revenue Threshold{" "}
                                    <span className="normal-case text-zinc-600">(optional)</span>
                                </label>
                                <input
                                    type="text"
                                    value={threshold}
                                    onChange={(e) => setThreshold(e.target.value)}
                                    placeholder="e.g. 10Cr+, 100Cr+"
                                    className="input-field w-full"
                                />
                            </div>
                        </>
                    ) : (
                        <>
                            <div className="space-y-1.5">
                                <label className="text-xs font-medium text-zinc-400 uppercase tracking-widest">
                                    Region
                                </label>
                                <input
                                    type="text"
                                    value={region}
                                    onChange={(e) => setRegion(e.target.value)}
                                    placeholder="e.g. Pune, Mumbai, Bangalore"
                                    required
                                    className="input-field w-full"
                                />
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-xs font-medium text-zinc-400 uppercase tracking-widest">
                                    Revenue Threshold
                                </label>
                                <input
                                    type="text"
                                    value={threshold}
                                    onChange={(e) => setThreshold(e.target.value)}
                                    placeholder="e.g. 1Cr+, 10Cr+"
                                    required
                                    className="input-field w-full"
                                />
                            </div>
                        </>
                    )}
                </motion.div>
            </AnimatePresence>

            {/* Submit */}
            <button
                type="submit"
                disabled={loading}
                className="btn-primary flex items-center gap-2.5 disabled:opacity-60 disabled:cursor-not-allowed disabled:scale-100"
            >
                {loading ? (
                    <>
                        <Loader2 size={16} className="animate-spin" />
                        Running Analysis…
                    </>
                ) : (
                    <>
                        <Zap size={16} />
                        Run Strategic Analysis
                    </>
                )}
            </button>
        </form>
    );
}
