import { motion } from "framer-motion";
import { Zap, TrendingUp } from "lucide-react";

function classifyColor(cls) {
    if (!cls) return "zinc";
    const c = cls.toLowerCase();
    if (c.includes("strong")) return "emerald";
    if (c.includes("medium")) return "amber";
    return "red";
}

function LeadScoreBadge({ score }) {
    const color =
        score >= 75 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444";
    const ringClass =
        score >= 75
            ? "ring-emerald-500/40"
            : score >= 50
                ? "ring-amber-500/40"
                : "ring-red-500/40";
    const textClass =
        score >= 75
            ? "text-emerald-400"
            : score >= 50
                ? "text-amber-400"
                : "text-red-400";
    const bgClass =
        score >= 75
            ? "bg-emerald-500/10"
            : score >= 50
                ? "bg-amber-500/10"
                : "bg-red-500/10";

    return (
        <div
            className={`flex flex-col items-center justify-center w-24 h-24 rounded-2xl ${bgClass} ring-2 ${ringClass} relative`}
            style={{ boxShadow: `0 0 24px ${color}20` }}
        >
            <span className={`text-3xl font-black ${textClass} leading-none`}>
                {score}
            </span>
            <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500 mt-1">
                Lead Score
            </span>
            <div
                className="absolute -inset-px rounded-2xl border opacity-40"
                style={{ borderColor: color }}
            />
        </div>
    );
}

export default function SummaryCard({ data }) {
    const dossier = data.company_dossier || {};
    const leadScore = data.lead_score || {};
    const classification = leadScore.classification || "Not Priority";
    const color = classifyColor(classification);
    const total = leadScore.total || 0;

    const badgeClass = {
        emerald: "bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/30",
        amber: "bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/30",
        red: "bg-red-500/15 text-red-400 ring-1 ring-red-500/30",
    }[color];

    const dotClass = {
        emerald: "bg-emerald-400",
        amber: "bg-amber-400",
        red: "bg-red-400",
    }[color];

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="glass-card p-6"
        >
            <div className="flex flex-col sm:flex-row sm:items-start gap-6">
                {/* Left: Company info */}
                <div className="space-y-4 flex-1 min-w-0">
                    <div className="flex items-center gap-3 flex-wrap">
                        <h2 className="text-xl font-bold text-zinc-100 truncate">
                            {data.domain || "Company"}
                        </h2>
                        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${badgeClass}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${dotClass} animate-pulse`} />
                            {classification}
                        </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <Stat label="Industry" value={dossier.industry || "—"} />
                        <Stat label="Business Stage" value={dossier.business_stage || "—"} />
                        <Stat label="Hiring" value={dossier.hiring_intensity || "—"} />
                        <Stat
                            label="Growth Signals"
                            value={dossier.signal_count ? `${dossier.signal_count} signals` : "—"}
                            highlight
                        />
                    </div>

                    {leadScore.has_trigger_event && (
                        <div className="inline-flex items-center gap-2 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-1.5">
                            <Zap size={11} className="flex-shrink-0" />
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
                            Trigger Event Detected — Strategic Window Open
                        </div>
                    )}
                </div>

                {/* Right: Lead Score (replaces gauge) */}
                <div className="flex flex-col items-center gap-2 sm:pl-4 sm:border-l sm:border-white/5">
                    <LeadScoreBadge score={total} />
                    <div className="flex items-center gap-1 text-[10px] text-zinc-500 font-medium">
                        <TrendingUp size={10} />
                        <span>Engagement Signal</span>
                    </div>
                </div>
            </div>

            {data.why_now && (
                <div className="mt-6 pt-6 border-t border-white/5">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                        <span className="text-[10px] font-bold uppercase tracking-widest text-primary/80">
                            Strategic Justification (Why Now?)
                        </span>
                    </div>
                    <p className="text-sm text-zinc-300 leading-relaxed italic">
                        "{data.why_now}"
                    </p>
                </div>
            )}
        </motion.div>
    );
}

function Stat({ label, value, highlight }) {
    return (
        <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-600 mb-0.5">
                {label}
            </p>
            <p className={`text-sm font-medium leading-snug ${highlight ? "text-accent" : "text-zinc-200"}`}>
                {value}
            </p>
        </div>
    );
}
