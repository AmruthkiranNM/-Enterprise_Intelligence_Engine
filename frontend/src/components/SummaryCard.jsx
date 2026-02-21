import { motion } from "framer-motion";

function classifyColor(cls) {
    if (!cls) return "zinc";
    const c = cls.toLowerCase();
    if (c.includes("strong")) return "emerald";
    if (c.includes("medium")) return "amber";
    return "red";
}

function GaugeSVG({ value = 0, max = 20, color = "#ef4444" }) {
    const pct = Math.min(value / max, 1);
    const radius = 54;
    const circumference = Math.PI * radius; // half circle
    const offset = circumference * (1 - pct);

    return (
        <div className="relative group cursor-help">
            <svg viewBox="0 0 120 70" className="w-36 h-auto">
                {/* Track */}
                <path
                    d={`M 10 60 A ${radius} ${radius} 0 0 1 110 60`}
                    fill="none"
                    stroke="#27272a"
                    strokeWidth="8"
                    strokeLinecap="round"
                />
                {/* Fill */}
                <path
                    d={`M 10 60 A ${radius} ${radius} 0 0 1 110 60`}
                    fill="none"
                    stroke={color}
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    className="transition-all duration-1000"
                    style={{ filter: `drop-shadow(0 0 6px ${color}80)` }}
                />
                <text x="60" y="58" textAnchor="middle" fill={color} fontSize="18" fontWeight="700">
                    {value}
                </text>
                <text x="60" y="72" textAnchor="middle" fill="#71717a" fontSize="8">
                    / {max}
                </text>
            </svg>

            {/* Tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-zinc-900 border border-zinc-800 rounded-lg text-[10px] text-zinc-400 leading-tight opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-xl">
                Strategic Pressure Index measures cumulative operational change signals indicating infrastructure strain and transformation urgency.
            </div>
        </div>
    );
}

export default function SummaryCard({ data }) {
    const dossier = data.company_dossier || {};
    const leadScore = data.lead_score || {};
    const classification = leadScore.classification || "Not Priority";
    const color = classifyColor(classification);

    const pressureIndex = leadScore.strategic_pressure_index ?? dossier.strategic_pressure_score ?? 0;
    const pressureTier = leadScore.tier || "Stable";
    const pressureColor = leadScore.color || "#71717a";
    const engagementWindow = leadScore.guidance || "Monitor";

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
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-6">
                {/* Left: Company info */}
                <div className="space-y-4 flex-1">
                    <div className="flex items-center gap-3 flex-wrap">
                        <h2 className="text-xl font-bold text-zinc-100 truncate">
                            {data.domain || "Company"}
                        </h2>
                        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${badgeClass}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${dotClass} animate-pulse`} />
                            {classification}
                        </span>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <Stat label="Industry" value={dossier.industry || "—"} />
                        <Stat label="Business Stage" value={dossier.business_stage || "—"} />
                        <Stat label="Engagement Window" value={engagementWindow} />
                        <Stat label="Signal Count" value={dossier.signal_count ? `${dossier.signal_count} signals` : "—"} />
                    </div>

                    {leadScore.has_trigger_event && (
                        <div className="inline-flex items-center gap-2 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
                            Trigger Event Detected — Strategic Window Open
                        </div>
                    )}
                </div>

                {/* Right: Gauge */}
                <div className="flex flex-col items-center gap-1">
                    <GaugeSVG
                        value={pressureIndex}
                        max={20}
                        color={pressureColor}
                    />
                    <div className="flex flex-col items-center">
                        <span className="text-xs text-zinc-500 font-bold tracking-widest uppercase">
                            Pressure Index
                        </span>
                        <span className="text-[10px] font-medium px-2 py-0.5 mt-1 rounded-full border"
                            style={{ borderColor: `${pressureColor}40`, backgroundColor: `${pressureColor}10`, color: pressureColor }}>
                            {pressureTier}
                        </span>
                    </div>
                </div>
            </div>

            {data.why_now && (
                <p className="mt-5 pt-5 border-t border-border/50 text-sm text-zinc-400 leading-relaxed">
                    {data.why_now}
                </p>
            )}
        </motion.div>
    );
}

function Stat({ label, value }) {
    return (
        <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-600 mb-0.5">
                {label}
            </p>
            <p className="text-sm text-zinc-200 font-medium leading-snug">{value}</p>
        </div>
    );
}
