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
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-zinc-900 border border-zinc-800 rounded-lg text-[10px] text-zinc-400 leading-relaxed opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-2xl">
                <p className="font-bold text-zinc-200 mb-1">Strategic Pressure Index (SPI)</p>
                Represents weighted operational change velocity. Measures cumulative high-impact signals indicating infrastructure strain and transformation urgency.
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
    const pressureTier = leadScore.tier || "Stable Operational Velocity";
    const pressureColor = leadScore.color || "#71717a";
    const engagementMode = leadScore.engagement_mode || "Passive Monitoring";
    const operationalMeaning = leadScore.operational_meaning || "Normal operational baseline.";
    const explanation = leadScore.explanation || "Maintaining monitoring baseline.";

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
            <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-8">
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

                    <div className="grid grid-cols-2 gap-4">
                        <Stat label="Industry" value={dossier.industry || "—"} />
                        <Stat label="Business Stage" value={dossier.business_stage || "—"} />
                        <div className="group relative cursor-help">
                            <Stat label="Signal Count" value={dossier.signal_count ? `${dossier.signal_count} signals` : "—"} />
                            <div className="absolute top-full left-0 mt-2 w-48 p-2 bg-zinc-900 border border-zinc-800 rounded-lg text-[10px] text-zinc-400 opacity-0 group-hover:opacity-100 transition-opacity z-20 pointer-events-none">
                                Quantity of distinct growth and scale indicators detected.
                            </div>
                        </div>
                        <Stat label="Operational Meaning" value={operationalMeaning} />
                    </div>

                    {leadScore.has_trigger_event && (
                        <div className="inline-flex items-center gap-2 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
                            Trigger Event Detected — Strategic Window Open
                        </div>
                    )}
                </div>

                {/* Right: SPI Gauge & Strategy */}
                <div className="flex flex-col sm:flex-row items-center gap-6 p-4 rounded-xl bg-white/5 border border-white/5">
                    <div className="flex flex-col items-center">
                        <GaugeSVG
                            value={pressureIndex}
                            max={20}
                            color={pressureColor}
                        />
                        <span className="text-[10px] text-zinc-500 font-bold tracking-[0.2em] uppercase mt-1">
                            Pressure Index
                        </span>
                    </div>

                    <div className="flex-1 space-y-2 text-center sm:text-left min-w-[140px]">
                        <div>
                            <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Urgency Tier</p>
                            <p className="text-sm font-semibold transition-colors" style={{ color: pressureColor }}>
                                {pressureTier}
                            </p>
                        </div>
                        <div>
                            <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Engagement Mode</p>
                            <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold mt-0.5 border"
                                style={{ borderColor: `${pressureColor}40`, backgroundColor: `${pressureColor}10`, color: pressureColor }}>
                                {engagementMode}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {explanation && (
                <div className="mt-6 pt-5 border-t border-border/50">
                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-1.5">Strategic Analysis</p>
                    <p className="text-sm text-zinc-400 leading-relaxed italic">
                        "{explanation}"
                    </p>
                </div>
            )}
        </motion.div>
    );
}

function Stat({ label, value }) {
    return (
        <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-600 mb-1">
                {label}
            </p>
            <p className="text-sm text-zinc-200 font-medium leading-snug">{value}</p>
        </div>
    );
}
