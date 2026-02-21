import { motion } from "framer-motion";

const TYPE_COLORS = {
    "Data Acquisition": "bg-blue-500",
    "Signal Extraction": "bg-violet-500",
    "Strategic Inference": "bg-indigo-500",
    "Bottleneck Detection": "bg-red-500",
    "Scoring Engine": "bg-emerald-500",
};

export default function ResearchTrace({ data }) {
    const trace = data.agent_research_trace || [];
    if (trace.length === 0) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.3 }}
            className="glass-card p-6 space-y-4"
        >
            <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest">
                Agent Research Trace
            </h3>

            <div
                className="space-y-0 max-h-72 overflow-y-auto custom-scrollbar pr-1"
                role="list"
            >
                {trace.map((item, i) => {
                    const dotColor = TYPE_COLORS[item.type] || "bg-zinc-500";
                    const isLast = i === trace.length - 1;
                    return (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.35 + i * 0.06 }}
                            className="relative flex gap-4"
                            role="listitem"
                        >
                            {/* Timeline line */}
                            {!isLast && (
                                <div className="absolute left-[9px] top-5 bottom-0 w-px bg-gradient-to-b from-zinc-700 to-transparent" />
                            )}

                            {/* Dot */}
                            <div className="flex-shrink-0 mt-1.5">
                                <div className={`w-[18px] h-[18px] rounded-full ${dotColor} flex items-center justify-center text-[9px] font-bold text-white shadow-lg`}>
                                    {item.step}
                                </div>
                            </div>

                            {/* Content */}
                            <div className="pb-5 flex-1 min-w-0">
                                <div className="flex flex-wrap items-center gap-2 mb-0.5">
                                    <span className="text-xs font-semibold text-zinc-200">{item.type}</span>
                                    {item.timestamp && (
                                        <span className="text-[10px] text-zinc-600 font-mono">{item.timestamp}</span>
                                    )}
                                </div>
                                <p className="text-xs text-zinc-500 leading-relaxed">{item.detail}</p>
                            </div>
                        </motion.div>
                    );
                })}
            </div>
        </motion.div>
    );
}
