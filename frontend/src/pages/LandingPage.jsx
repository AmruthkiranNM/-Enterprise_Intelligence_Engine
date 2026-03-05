import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Zap, Target, Search, BarChart3, Mail, Brain } from "lucide-react";

const STEPS = [
    { icon: Brain, label: "Understand your company", desc: "Analyze your services & strengths" },
    { icon: Search, label: "Discover prospects", desc: "Domain or regional search" },
    { icon: BarChart3, label: "Analyze business context", desc: "External signals & triggers" },
    { icon: Target, label: "Detect strategic gaps", desc: "Gap analysis vs your catalog" },
    { icon: Mail, label: "Generate outreach", desc: "Personalized AI-crafted email" },
];

export default function LandingPage() {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-background text-zinc-100 flex flex-col">
            {/* Background orbs */}
            <div className="fixed top-[-20%] left-[-10%] w-[700px] h-[700px] rounded-full pointer-events-none" style={{ background: "radial-gradient(circle, rgba(110,231,183,0.10) 0%, transparent 70%)" }} />
            <div className="fixed bottom-[-20%] right-[-10%] w-[700px] h-[700px] rounded-full pointer-events-none" style={{ background: "radial-gradient(circle, rgba(244,114,182,0.08) 0%, transparent 70%)" }} />

            {/* Header */}
            <header className="relative z-10 flex items-center justify-between px-8 py-6 max-w-7xl mx-auto w-full">
                <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-lg shadow-primary/30">
                        <Zap size={16} className="text-white" />
                    </div>
                    <span className="font-bold text-zinc-200 tracking-tight">Lead Intelligence</span>
                </div>
                <button
                    onClick={() => navigate("/auth?mode=signin")}
                    className="text-sm font-semibold text-zinc-400 hover:text-zinc-100 transition-colors"
                >
                    Sign In
                </button>
            </header>

            {/* Hero */}
            <main className="relative z-10 flex-1 flex flex-col items-center justify-center text-center px-6 py-20 max-w-5xl mx-auto w-full gap-10">
                <motion.div
                    initial={{ opacity: 0, y: 24 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="space-y-6"
                >
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold uppercase tracking-widest mb-2">
                        <Zap size={12} /> AI-Powered Lead Discovery
                    </div>
                    <h1 className="text-5xl sm:text-6xl font-black leading-tight">
                        Autonomous Gold{" "}
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">
                            Lead Discovery
                        </span>{" "}
                        System
                    </h1>
                    <p className="text-zinc-400 text-lg max-w-2xl mx-auto leading-relaxed">
                        An AI-powered system that discovers high-value business prospects by analyzing company gaps, strategic signals, and market context — built for any company.
                    </p>

                    <div className="flex items-center justify-center gap-4 pt-2">
                        <motion.button
                            whileHover={{ scale: 1.04 }}
                            whileTap={{ scale: 0.97 }}
                            onClick={() => navigate("/auth?mode=signup")}
                            className="btn-primary flex items-center gap-2 text-base px-8 py-4"
                        >
                            Get Started <ArrowRight size={18} />
                        </motion.button>
                        <button
                            onClick={() => navigate("/auth?mode=signin")}
                            className="flex items-center gap-2 px-8 py-4 rounded-xl font-semibold text-zinc-400 border border-zinc-700/60 hover:border-zinc-500 hover:text-zinc-200 transition-all text-base"
                        >
                            Sign In
                        </button>
                    </div>
                </motion.div>

                {/* Pipeline Steps */}
                <motion.div
                    initial={{ opacity: 0, y: 32 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="w-full mt-8"
                >
                    <p className="text-zinc-500 text-sm uppercase tracking-widest font-semibold mb-8">How it works</p>
                    <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
                        {STEPS.map((step, i) => (
                            <div key={i} className="relative flex flex-col items-center gap-3 text-center">
                                {/* Connector line */}
                                {i < STEPS.length - 1 && (
                                    <div className="hidden sm:block absolute left-full top-[28px] w-full h-px bg-gradient-to-r from-primary/30 to-transparent z-0 translate-x-[-50%]" />
                                )}
                                <div className="relative z-10 w-14 h-14 rounded-2xl bg-zinc-900 border border-zinc-700/60 flex items-center justify-center shadow-lg">
                                    <step.icon size={22} className="text-primary" />
                                    <span className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-primary text-zinc-950 text-[10px] font-black flex items-center justify-center">{i + 1}</span>
                                </div>
                                <div>
                                    <p className="text-xs font-bold text-zinc-200 leading-snug">{step.label}</p>
                                    <p className="text-[11px] text-zinc-500 mt-0.5">{step.desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </motion.div>
            </main>

            {/* Footer */}
            <footer className="relative z-10 text-center py-6 text-zinc-600 text-xs">
                Lead Intelligence Platform — Autonomous AI for B2B Discovery
            </footer>
        </div>
    );
}
