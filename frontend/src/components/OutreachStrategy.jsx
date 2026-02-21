import { useState } from "react";
import { ChevronDown, Copy, Check, User2, Target } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function OutreachStrategy({ data }) {
    const [emailOpen, setEmailOpen] = useState(false);
    const [copied, setCopied] = useState(false);

    const classification = data.lead_score?.classification || "";
    const isQualified =
        classification.toLowerCase().includes("strong") ||
        classification.toLowerCase().includes("medium");

    const outreach = data.personalized_outreach;
    if (!isQualified || !outreach) return null;

    const handleCopy = () => {
        navigator.clipboard.writeText(outreach.outreach_email || "");
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.25 }}
            className="glass-card p-6 space-y-5"
        >
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest">
                    Outreach Strategy
                </h3>
                <span className="text-[10px] font-semibold uppercase tracking-widest text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full">
                    Qualified Lead
                </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="flex items-start gap-3 p-3.5 rounded-xl bg-zinc-900/60 border border-zinc-800">
                    <User2 size={15} className="text-primary mt-0.5 flex-shrink-0" />
                    <div>
                        <p className="text-[10px] text-zinc-600 uppercase tracking-widest mb-0.5">Decision Maker</p>
                        <p className="text-sm text-zinc-200 font-medium">{outreach.recommended_decision_maker}</p>
                    </div>
                </div>
                <div className="flex items-start gap-3 p-3.5 rounded-xl bg-zinc-900/60 border border-zinc-800">
                    <Target size={15} className="text-accent mt-0.5 flex-shrink-0" />
                    <div>
                        <p className="text-[10px] text-zinc-600 uppercase tracking-widest mb-0.5">Strategic Angle</p>
                        <p className="text-sm text-zinc-200 font-medium leading-snug">{outreach.strategic_angle}</p>
                    </div>
                </div>
            </div>

            {outreach.outreach_email && (
                <div className="rounded-xl border border-border/60 overflow-hidden">
                    <button
                        onClick={() => setEmailOpen(!emailOpen)}
                        className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-zinc-300 hover:text-zinc-100 hover:bg-zinc-900/50 transition-colors"
                    >
                        <span>View Outreach Email</span>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={(e) => { e.stopPropagation(); handleCopy(); }}
                                className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-primary px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 transition-all"
                            >
                                {copied ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
                                {copied ? "Copied!" : "Copy"}
                            </button>
                            <ChevronDown
                                size={16}
                                className={`text-zinc-500 transition-transform duration-200 ${emailOpen ? "rotate-180" : ""}`}
                            />
                        </div>
                    </button>

                    <AnimatePresence>
                        {emailOpen && (
                            <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: "auto", opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.25 }}
                                className="overflow-hidden"
                            >
                                <pre className="px-4 pb-4 pt-3 text-xs text-zinc-400 font-mono whitespace-pre-wrap leading-relaxed border-t border-border/40 bg-zinc-950/50">
                                    {outreach.outreach_email}
                                </pre>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            )}
        </motion.div>
    );
}
