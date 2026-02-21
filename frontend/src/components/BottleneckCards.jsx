import { Cpu, Layers, Zap, AlertTriangle, Bot, Database } from "lucide-react";
import { motion } from "framer-motion";

const ICON_MAP = {
    Cpu,
    Layers,
    Zap,
    AlertTriangle,
    Bot,
    Database,
};

function SeverityBadge({ severity }) {
    const cfg = {
        High: "bg-red-500/15 text-red-400 border border-red-500/25",
        Medium: "bg-amber-500/15 text-amber-400 border border-amber-500/25",
        Low: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/25",
    };
    return (
        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${cfg[severity] || cfg.Low}`}>
            {severity}
        </span>
    );
}

export default function BottleneckCards({ data }) {
    const bottlenecks = data.strategic_bottlenecks || [];
    if (bottlenecks.length === 0) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="glass-card p-6 space-y-4"
        >
            <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest">
                Strategic Bottlenecks
            </h3>

            <div className="space-y-3">
                {bottlenecks.map((b, i) => {
                    const Icon = ICON_MAP[b.icon] || AlertTriangle;
                    return (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, x: -12 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.25 + i * 0.08 }}
                            className="flex gap-4 p-4 rounded-xl bg-zinc-900/60 border border-zinc-800/80 hover:border-zinc-700/80 transition-all"
                        >
                            <div className="mt-0.5 flex-shrink-0 w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center">
                                <Icon size={16} className="text-primary" />
                            </div>
                            <div className="flex-1 min-w-0 space-y-1.5">
                                <div className="flex flex-wrap items-center gap-2">
                                    <h4 className="text-sm font-semibold text-zinc-100">{b.title}</h4>
                                    <SeverityBadge severity={b.severity} />
                                </div>
                                <p className="text-xs text-zinc-500 leading-relaxed">{b.evidence}</p>
                                <div className="flex items-center gap-1.5 pt-0.5">
                                    <span className="text-[10px] text-zinc-600 uppercase tracking-wider">Mapped to</span>
                                    <span className="text-[10px] font-semibold text-accent bg-accent/10 px-2 py-0.5 rounded-full border border-accent/20">
                                        {b.mapped_service}
                                    </span>
                                </div>
                            </div>
                        </motion.div>
                    );
                })}
            </div>
        </motion.div>
    );
}
