import { motion } from "framer-motion";

/*
This component now supports BOTH:
1. Backend returning simple strings
2. Backend returning structured objects

It normalizes the data before rendering.
*/

const TYPE_COLORS = {
    "Data Acquisition": "bg-blue-500",
    "Signal Extraction": "bg-violet-500",
    "Strategic Inference": "bg-indigo-500",
    "Bottleneck Detection": "bg-red-500",
    "Scoring Engine": "bg-emerald-500",
};

/* 
Intelligent auto-classification for string-based traces.
You can refine these rules later.
*/
function inferTypeFromDetail(detail) {
    const text = detail.toLowerCase();

    if (text.includes("scraped") || text.includes("fetched"))
        return "Data Acquisition";

    if (text.includes("detected") || text.includes("found"))
        return "Signal Extraction";

    if (text.includes("pressure") || text.includes("score"))
        return "Scoring Engine";

    if (text.includes("bottleneck"))
        return "Bottleneck Detection";

    return "Strategic Inference";
}

export default function ResearchTrace({ data }) {
    const rawTrace = data?.agent_research_trace || [];

    if (!rawTrace || rawTrace.length === 0) return null;

    // Normalize trace format
    const trace = rawTrace.map((item, index) => {
        if (typeof item === "string") {
            return {
                step: index + 1,
                type: inferTypeFromDetail(item),
                detail: item,
                timestamp: null,
            };
        }

        // Already structured object
        return {
            step: item.step ?? index + 1,
            type: item.type ?? inferTypeFromDetail(item.detail || ""),
            detail: item.detail ?? "",
            timestamp: item.timestamp ?? null,
        };
    });

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.3 }}
            className="glass-card p-6 space-y-6"
        >
            <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest">
                Agent Research Trace
            </h3>

            <div
                className="space-y-0 max-h-80 overflow-y-auto custom-scrollbar pr-2"
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
                                <div
                                    className={`w-[20px] h-[20px] rounded-full ${dotColor} flex items-center justify-center text-[10px] font-bold text-white shadow-md`}
                                >
                                    {item.step}
                                </div>
                            </div>

                            {/* Content */}
                            <div className="pb-6 flex-1 min-w-0">
                                <div className="flex flex-wrap items-center gap-2 mb-1">
                                    <span className="text-xs font-semibold text-zinc-200">
                                        {item.type}
                                    </span>

                                    {item.timestamp && (
                                        <span className="text-[10px] text-zinc-500 font-mono">
                                            {item.timestamp}
                                        </span>
                                    )}
                                </div>

                                <p className="text-xs text-zinc-300 leading-relaxed">
                                    {item.detail}
                                </p>
                            </div>
                        </motion.div>
                    );
                })}
            </div>
        </motion.div>
    );
}