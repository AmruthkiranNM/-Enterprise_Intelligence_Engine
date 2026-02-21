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
    Funding: { icon: TrendingUp, color: "text-emerald-400", bg: "bg-emerald-400/10", border: "border-emerald-400/30", label: "💰 Funding" },
    Acquisition: { icon: Zap, color: "text-violet-400", bg: "bg-violet-400/10", border: "border-violet-400/30", label: "🤝 Acquisition" },
    IPO: { icon: TrendingUp, color: "text-amber-400", bg: "bg-amber-400/10", border: "border-amber-400/30", label: "📈 IPO" },
    Leadership: { icon: Users, color: "text-blue-400", bg: "bg-blue-400/10", border: "border-blue-400/30", label: "👤 Leadership" },
    Hiring: { icon: Users, color: "text-cyan-400", bg: "bg-cyan-400/10", border: "border-cyan-400/30", label: "🚀 Hiring" },
    Product: { icon: Package, color: "text-indigo-400", bg: "bg-indigo-400/10", border: "border-indigo-400/30", label: "📦 Product" },
    Expansion: { icon: Globe, color: "text-rose-400", bg: "bg-rose-400/10", border: "border-rose-400/30", label: "🌍 Expansion" },
};

const SEVERITY_CONFIG = {
    High: { color: "text-red-400", bg: "bg-red-400/10", border: "border-red-400/30", dot: "bg-red-400" },
    Medium: { color: "text-amber-400", bg: "bg-amber-400/10", border: "border-amber-400/30", dot: "bg-amber-400" },
    Low: { color: "text-emerald-400", bg: "bg-emerald-400/10", border: "border-emerald-400/30", dot: "bg-emerald-400" },
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
                {/* Top row */}
                <div className="flex items-start gap-3 mb-3">
                    <div className={`flex-none flex items-center justify-center w-9 h-9 rounded-xl ${ev.bg} border ${ev.border}`}>
                        <Icon size={15} className={ev.color} />
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center flex-wrap gap-2 mb-1">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${ev.bg} ${ev.color} ${ev.border}`}>
                                {ev.label}
                            </span>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${sv.bg} ${sv.color} ${sv.border}`}>
                                {alert.severity} Severity
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

                {/* Impact row */}
                <div className="flex items-center gap-6 mb-3">
                    <div>
                        <div className="text-[9px] uppercase tracking-widest text-zinc-600 mb-0.5 font-semibold">Impact Score</div>
                        <div className="text-xl font-black text-primary">{Math.round(alert.impact_score)}<span className="text-zinc-600 text-xs">/100</span></div>
                    </div>
                    <div>
                        <div className="text-[9px] uppercase tracking-widest text-zinc-600 mb-0.5 font-semibold">Confidence</div>
                        <div className="text-sm font-bold text-zinc-300">{alert.confidence}</div>
                    </div>
                </div>

                {/* Summary */}
                <p className="text-xs text-zinc-400 leading-relaxed line-clamp-2">{alert.event_summary}</p>
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
                        <div className="px-5 pb-5 space-y-4">
                            {alert.suggested_action && (
                                <div className="rounded-xl bg-primary/5 border border-primary/15 p-4">
                                    <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest font-bold text-primary mb-2">
                                        <ArrowRight size={10} />
                                        Suggested Action
                                    </div>
                                    <p className="text-xs text-zinc-300 leading-relaxed">{alert.suggested_action}</p>
                                </div>
                            )}

                            {/* Action buttons */}
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
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
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
