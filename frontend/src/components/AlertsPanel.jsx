/**
 * AlertsPanel.jsx — Strategic alert cards with event type, impact, and suggested action
 */
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Zap, TrendingUp, Users, Package, Globe,
    ChevronDown, Check, Trash2, Bell, BellOff,
    AlertTriangle, ArrowRight,
} from "lucide-react";

const EVENT_CONFIG = {
    "Funding Round": { icon: TrendingUp, color: "text-emerald-400", bg: "bg-emerald-400/10", border: "border-emerald-400/30", label: "💰 Funding" },
    "M&A": { icon: Zap, color: "text-violet-400", bg: "bg-violet-400/10", border: "border-violet-400/30", label: "🤝 Acquisition" },
    "IPO": { icon: TrendingUp, color: "text-amber-400", bg: "bg-amber-400/10", border: "border-amber-400/30", label: "📈 IPO" },
    "Leadership Change": { icon: Users, color: "text-blue-400", bg: "bg-blue-400/10", border: "border-blue-400/30", label: "👤 Leadership" },
    "Hiring": { icon: Users, color: "text-cyan-400", bg: "bg-cyan-400/10", border: "border-cyan-400/30", label: "🚀 Hiring" },
    "Product Launch": { icon: Package, color: "text-indigo-400", bg: "bg-indigo-400/10", border: "border-indigo-400/30", label: "📦 Product" },
    "Expansion": { icon: Globe, color: "text-rose-400", bg: "bg-rose-400/10", border: "border-rose-400/30", label: "🌍 Expansion" },
    "Regulatory Issue": { icon: AlertTriangle, color: "text-amber-500", bg: "bg-amber-500/10", border: "border-amber-500/30", label: "⚖️ Regulatory" },
    "Layoffs": { icon: Users, color: "text-red-400", bg: "bg-red-400/10", border: "border-red-400/30", label: "📉 Layoffs" },
    "Major Partnership": { icon: Globe, color: "text-blue-400", bg: "bg-blue-400/10", border: "border-blue-400/30", label: "🤝 Partnership" },
};

const SEVERITY_CONFIG = {
    "Critical Executive Event": { color: "text-red-400", bg: "bg-red-400/10", border: "border-red-400/30", dot: "bg-red-400" },
    "Strategic Trigger": { color: "text-amber-400", bg: "bg-amber-400/10", border: "border-amber-400/30", dot: "bg-amber-400" },
    "Growth Indicator": { color: "text-emerald-400", bg: "bg-emerald-400/10", border: "border-emerald-400/30", dot: "bg-emerald-400" },
    "Informational": { color: "text-zinc-400", bg: "bg-zinc-400/10", border: "border-zinc-400/30", dot: "bg-zinc-400" },
};

function formatDate(dt) {
    if (!dt) return "";
    const d = new Date(dt);
    const now = new Date();
    const diffMs = now - d;
    const diffM = Math.floor(diffMs / 60_000);
    const diffH = Math.floor(diffMs / 3_600_000);
    if (diffM < 1) return "Just now";
    if (diffM < 60) return `${diffM}m ago`;
    if (diffH < 24) return `${diffH}h ago`;
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function AlertCard({ alert, onMarkRead, onDelete }) {
    const [expanded, setExpanded] = useState(false);
    const ev = EVENT_CONFIG[alert.event_type] || EVENT_CONFIG.Product;
    const sv = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.Medium;
    const Icon = ev.icon;

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className={`relative glass-card overflow-hidden transition-all duration-300 ${!alert.is_read ? "border-l-2 border-l-primary" : ""
                }`}
        >
            {/* unread pulse dot */}
            {!alert.is_read && (
                <span className="absolute top-4 right-4 flex h-2 w-2">
                    <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${sv.dot} opacity-75`} />
                    <span className={`relative inline-flex rounded-full h-2 w-2 ${sv.dot}`} />
                </span>
            )}

            <button className="w-full text-left p-5" onClick={() => setExpanded(e => !e)}>
                <div className="flex items-start gap-4 mb-4">
                    <div className={`flex-none flex items-center justify-center w-10 h-10 rounded-xl ${ev.bg} border ${ev.border}`}>
                        <Icon size={18} className={ev.color} />
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center flex-wrap gap-2 mb-1.5">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${ev.bg} ${ev.color} ${ev.border}`}>
                                {ev.label}
                            </span>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${sv.bg} ${sv.color} ${sv.border}`}>
                                {alert.severity_label}
                            </span>
                        </div>
                        <h3 className="text-sm font-bold text-zinc-100">{alert.company_name}</h3>
                        <p className="text-xs text-zinc-500 mt-0.5">{alert.domain} · {formatDate(alert.detected_at)}</p>
                    </div>
                    <ChevronDown
                        size={14}
                        className={`text-zinc-500 transition-transform mt-1 ${expanded ? "rotate-180" : ""}`}
                    />
                </div>

                <div className="mb-4">
                    <h4 className="text-sm font-semibold text-zinc-100 leading-snug line-clamp-2 mb-1">
                        {alert.headline}
                    </h4>
                    <p className="text-[10px] text-zinc-500 italic">Source: {alert.source || "Web Intel"}</p>
                </div>

                {/* Impact visualization */}
                <div className="flex items-center gap-10">
                    <div>
                        <div className="text-[9px] uppercase tracking-widest text-zinc-600 mb-1 font-bold">Strategic Impact</div>
                        <div className="flex items-baseline gap-1">
                            <div className="text-2xl font-black text-primary">{Math.round(alert.impact_index)}</div>
                            <div className="text-zinc-600 text-[10px] font-bold uppercase tracking-tighter">Index</div>
                        </div>
                    </div>
                    <div className="flex gap-4 border-l border-zinc-800/80 pl-6">
                        {Object.entries({
                            MV: alert.market_visibility,
                            FP: alert.financial_pressure,
                            OS: alert.operational_strain,
                            SA: alert.service_alignment
                        }).map(([label, val]) => (
                            <div key={label} className="text-center">
                                <div className="text-[8px] font-black text-zinc-700 mb-1">{label}</div>
                                <div className="text-xs font-bold text-zinc-400">{Math.round(val || 0)}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </button>

            {/* Expanded: suggested action */}
            <AnimatePresence>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25 }}
                        className="overflow-hidden"
                    >
                        <div className="px-5 pb-5 space-y-5">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-3">
                                    <div className="text-[9px] uppercase tracking-widest font-bold text-zinc-500 mb-2">Impact Drivers</div>
                                    <div className="flex flex-wrap gap-1.5">
                                        {JSON.parse(alert.impact_drivers || "[]").map(d => (
                                            <span key={d} className="text-[9px] bg-zinc-800 text-zinc-300 px-1.5 py-0.5 rounded border border-zinc-700/50">
                                                {d}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                                <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-3">
                                    <div className="text-[9px] uppercase tracking-widest font-bold text-zinc-500 mb-2">Recommended Action</div>
                                    <div className="text-[11px] font-bold text-primary italic uppercase tracking-wider">
                                        {alert.action_level}
                                    </div>
                                </div>
                            </div>

                            <div className="rounded-xl bg-primary/5 border border-primary/15 p-4">
                                <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest font-bold text-primary mb-2">
                                    <TrendingUp size={10} />
                                    Strategic Relevance
                                </div>
                                <p className="text-xs text-zinc-300 leading-relaxed italic">
                                    "{alert.strategic_relevance}"
                                </p>
                            </div>

                            {/* Action buttons */}
                            <div className="flex items-center justify-between pt-1">
                                <div className="flex items-center gap-2">
                                    {!alert.is_read && (
                                        <button
                                            onClick={(e) => { e.stopPropagation(); onMarkRead(alert.id); }}
                                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-semibold border border-zinc-700/50 transition-all"
                                        >
                                            <Check size={11} className="text-emerald-400" />
                                            Mark Read
                                        </button>
                                    )}
                                    <button
                                        onClick={(e) => { e.stopPropagation(); onDelete(alert.id); }}
                                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-semibold border border-red-500/20 transition-all"
                                    >
                                        <Trash2 size={11} />
                                        Dismiss
                                    </button>
                                </div>

                                {alert.url && (
                                    <a
                                        href={alert.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        onClick={(e) => e.stopPropagation()}
                                        className="flex items-center gap-1.5 text-xs font-semibold text-primary hover:text-primary-hover transition-colors"
                                    >
                                        View Source
                                        <ArrowRight size={12} />
                                    </a>
                                )}
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div >
    );
}

export default function AlertsPanel({ alerts, onMarkRead, onMarkAllRead, onDelete, loading }) {
    const unread = alerts.filter(a => !a.is_read);
    const read = alerts.filter(a => a.is_read);

    return (
        <section className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-red-500/10 border border-red-500/20">
                        <AlertTriangle size={16} className="text-red-400" />
                    </div>
                    <div>
                        <h2 className="text-base font-bold text-zinc-100 tracking-tight">Strategic Alerts</h2>
                        <p className="text-xs text-zinc-500">
                            {unread.length > 0 ? `${unread.length} new trigger event${unread.length > 1 ? "s" : ""}` : "All alerts reviewed"}
                        </p>
                    </div>
                </div>
                {unread.length > 0 && (
                    <button
                        onClick={onMarkAllRead}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 text-xs font-semibold border border-zinc-700/50 transition-all"
                    >
                        <BellOff size={11} />
                        Mark All Read
                    </button>
                )}
            </div>

            {/* Empty state */}
            {alerts.length === 0 && !loading && (
                <div className="flex flex-col items-center justify-center py-16 rounded-2xl border border-dashed border-zinc-700/50 bg-zinc-900/30">
                    <Bell size={32} className="text-zinc-600 mb-3" />
                    <p className="text-sm font-medium text-zinc-400">No strategic alerts yet</p>
                    <p className="text-xs text-zinc-600 mt-1 text-center max-w-xs">
                        The monitoring agent will notify you when trigger events are detected.
                    </p>
                </div>
            )}

            {/* Unread alerts */}
            {unread.length > 0 && (
                <div className="space-y-3">
                    <div className="text-[10px] uppercase tracking-widest font-bold text-zinc-600 flex items-center gap-2">
                        <span className="relative flex h-1.5 w-1.5">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-red-500" />
                        </span>
                        New ({unread.length})
                    </div>
                    <AnimatePresence mode="popLayout">
                        {unread.map(a => (
                            <AlertCard key={a.id} alert={a} onMarkRead={onMarkRead} onDelete={onDelete} />
                        ))}
                    </AnimatePresence>
                </div>
            )}

            {/* Read alerts */}
            {read.length > 0 && (
                <div className="space-y-3">
                    <div className="text-[10px] uppercase tracking-widest font-bold text-zinc-600">
                        Reviewed ({read.length})
                    </div>
                    <AnimatePresence mode="popLayout">
                        {read.map(a => (
                            <AlertCard key={a.id} alert={a} onMarkRead={onMarkRead} onDelete={onDelete} />
                        ))}
                    </AnimatePresence>
                </div>
            )}
        </section>
    );
}
