import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Brain, AlertCircle } from "lucide-react";
import AnalysisForm from "./components/AnalysisForm";
import SummaryCard from "./components/SummaryCard";
import LeadScoreChart from "./components/LeadScoreChart";
import SignalsPanel from "./components/SignalsPanel";
import BottleneckCards from "./components/BottleneckCards";
import OutreachStrategy from "./components/OutreachStrategy";
import ResearchTrace from "./components/ResearchTrace";
import RegionResultCards from "./components/RegionResultCards";
import "./index.css";

function LoadingOverlay() {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex flex-col items-center justify-center gap-5"
        >
            <div className="relative">
                <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/30 flex items-center justify-center">
                    <Brain size={28} className="text-primary" />
                </div>
                <div className="absolute -inset-1 rounded-[20px] border border-primary/20 animate-ping" />
            </div>
            <div className="text-center space-y-1">
                <p className="text-zinc-100 font-semibold">Running Strategic Analysis</p>
                <p className="text-zinc-500 text-sm">Researching signals, scoring leads…</p>
            </div>
            <div className="flex gap-1.5">
                {[0, 1, 2].map((i) => (
                    <motion.div
                        key={i}
                        className="w-1.5 h-1.5 rounded-full bg-primary"
                        animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1, 0.8] }}
                        transition={{ repeat: Infinity, duration: 1.2, delay: i * 0.2 }}
                    />
                ))}
            </div>
        </motion.div>
    );
}

export default function App() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [mode, setMode] = useState(null);
    const [error, setError] = useState(null);

    const handleResult = ({ data, mode: m }) => {
        setResult(data);
        setMode(m);
        setError(null);
        // Scroll to results
        setTimeout(() => {
            document.getElementById("results")?.scrollIntoView({ behavior: "smooth" });
        }, 200);
    };

    const handleError = (msg) => {
        setError(msg);
        setResult(null);
    };

    const isDomain = mode === "domain";
    const domainData = isDomain ? result : null;
    const regionData = !isDomain && Array.isArray(result) ? result : null;

    return (
        <div className="min-h-screen bg-background text-zinc-100">
            {/* Noise texture overlay */}
            <div
                className="fixed inset-0 opacity-[0.015] pointer-events-none z-0"
                style={{
                    backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
                }}
            />

            {/* Gradient orbs */}
            <div className="fixed top-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-primary/5 blur-[120px] pointer-events-none z-0" />
            <div className="fixed bottom-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-accent/5 blur-[120px] pointer-events-none z-0" />

            <AnimatePresence>{loading && <LoadingOverlay />}</AnimatePresence>

            <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-10">
                {/* Header */}
                <motion.header
                    initial={{ opacity: 0, y: -16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="space-y-2"
                >
                    <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-lg shadow-primary/30">
                            <Brain size={16} className="text-white" />
                        </div>
                        <span className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-500">
                            DataVex
                        </span>
                    </div>
                    <h1 className="text-3xl sm:text-4xl font-black text-zinc-100 leading-tight">
                        Strategic Enterprise{" "}
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">
                            Intelligence
                        </span>
                    </h1>
                    <p className="text-zinc-500 text-sm max-w-lg">
                        AI-powered market intelligence engine. Surface high-value accounts, detect bottlenecks, and generate precision outreach.
                    </p>
                </motion.header>

                {/* Input Card */}
                <motion.section
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.1 }}
                    className="glass-card p-6 sm:p-8"
                >
                    <AnalysisForm
                        onResult={handleResult}
                        onError={handleError}
                        onLoading={setLoading}
                    />
                </motion.section>

                {/* Error */}
                <AnimatePresence>
                    {error && (
                        <motion.div
                            initial={{ opacity: 0, y: -8 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0 }}
                            className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/25 text-red-400 text-sm"
                        >
                            <AlertCircle size={16} className="flex-shrink-0 mt-0.5" />
                            <span>{error}</span>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Results */}
                <AnimatePresence>
                    {result && (
                        <motion.section
                            id="results"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="space-y-4"
                        >
                            <div className="flex items-center gap-3 pb-2">
                                <div className="h-px flex-1 bg-gradient-to-r from-transparent via-border to-transparent" />
                                <span className="text-xs font-semibold uppercase tracking-widest text-zinc-600">
                                    {isDomain ? "Domain Intelligence Report" : "Region Discovery Results"}
                                </span>
                                <div className="h-px flex-1 bg-gradient-to-r from-transparent via-border to-transparent" />
                            </div>

                            {isDomain && domainData && (
                                <>
                                    <SummaryCard data={domainData} />
                                    <div className="grid grid-cols-1 gap-4">
                                        <LeadScoreChart data={domainData} />
                                        <SignalsPanel data={domainData} />
                                        <BottleneckCards data={domainData} />
                                        <OutreachStrategy data={domainData} />
                                        <ResearchTrace data={domainData} />
                                    </div>
                                </>
                            )}

                            {!isDomain && regionData && (
                                <RegionResultCards results={regionData} />
                            )}
                        </motion.section>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
