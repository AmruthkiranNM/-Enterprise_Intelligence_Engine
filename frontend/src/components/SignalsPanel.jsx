import { TrendingUp, BarChart2, Flame } from "lucide-react";
import { motion } from "framer-motion";

function SignalPill({ label, isHighlight }) {
    return (
        <div
            className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 ${isHighlight
                    ? "bg-amber-500/15 text-amber-300 border border-amber-500/25"
                    : "bg-zinc-900 text-zinc-300 border border-zinc-800"
                }`}
        >
            {isHighlight && <Flame size={11} className="text-amber-400" />}
            {label}
        </div>
    );
}

export default function SignalsPanel({ data }) {
    const dossier = data.company_dossier || {};
    const growth = dossier.growth_signals || [];
    const scale = dossier.scale_signals || [];
    const triggers = dossier.trigger_events || [];

    if (growth.length === 0 && scale.length === 0 && triggers.length === 0) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.15 }}
            className="glass-card p-6 space-y-5"
        >
            <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest">
                Growth & Scale Signals
            </h3>

            {triggers.length > 0 && (
                <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs font-semibold text-amber-400 uppercase tracking-widest">
                        <Flame size={12} />
                        Trigger Events
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {triggers.map((t, i) => (
                            <SignalPill key={i} label={t} isHighlight />
                        ))}
                    </div>
                </div>
            )}

            {growth.length > 0 && (
                <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 uppercase tracking-widest">
                        <TrendingUp size={12} />
                        Growth Signals
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {growth.map((s, i) => (
                            <SignalPill key={i} label={s} />
                        ))}
                    </div>
                </div>
            )}

            {scale.length > 0 && (
                <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400 uppercase tracking-widest">
                        <BarChart2 size={12} />
                        Scale Signals
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {scale.map((s, i) => (
                            <SignalPill key={i} label={s} />
                        ))}
                    </div>
                </div>
            )}
        </motion.div>
    );
}
