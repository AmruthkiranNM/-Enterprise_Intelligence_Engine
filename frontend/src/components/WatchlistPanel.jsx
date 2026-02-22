/**
 * WatchlistPanel.jsx — Strategic Command Center
 * Lists all monitored companies with scan status and controls.
 */
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Eye, Trash2, RefreshCw, Clock, Activity,
    Building2, TrendingUp, Shield, ChevronRight,
} from "lucide-react";

const CLASSIFICATION_COLORS = {
    "Strong Lead": "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
    "Qualified Lead": "text-blue-400   bg-blue-400/10   border-blue-400/30",
    "Warm Lead": "text-amber-400  bg-amber-400/10  border-amber-400/30",
    "Not Priority": "text-zinc-500   bg-zinc-500/10   border-zinc-500/30",
};

function ClassBadge({ cls }) {
    const color = CLASSIFICATION_COLORS[cls] || CLASSIFICATION_COLORS["Not Priority"];
    return (
        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${color}`}>
            {cls}
        </span>
    );
}

function formatDate(dt) {
    if (!dt) return "Never scanned";
    const d = new Date(dt);
    const now = new Date();
    const diffMs = now - d;
    const diffH = Math.floor(diffMs / 3_600_000);
    const diffM = Math.floor(diffMs / 60_000);
    if (diffM < 1) return "Just now";
    if (diffM < 60) return `${diffM}m ago`;
    if (diffH < 24) return `${diffH}h ago`;
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default function WatchlistPanel({ watchlist, onRemove, onScanNow, loading }) {
    const [scanningId, setScanningId] = useState(null);

    const handleScan = async (id) => {
        setScanningId(id);
        await onScanNow(id);
        // show spinner briefly
        setTimeout(() => setScanningId(null), 3000);
    };

    return (
        <section className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-primary/10 border border-primary/20">
                        <Shield size={16} className="text-primary" />
                    </div>
                    <div>
                        <h2 className="text-base font-bold text-zinc-100 tracking-tight">
                            Strategic Command Center
                        </h2>
                        <p className="text-xs text-zinc-500">Autonomous monitoring active</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                    </span>
                    <span className="text-xs font-medium text-emerald-400">Live</span>
                </div>
            </div>

            {/* Empty state */}
            {watchlist.length === 0 && !loading && (
                <div className="flex flex-col items-center justify-center py-16 rounded-2xl border border-dashed border-zinc-700/50 bg-zinc-900/30">
                    <Eye size={32} className="text-zinc-600 mb-3" />
                    <p className="text-sm font-medium text-zinc-400">No companies monitored yet</p>
                    <p className="text-xs text-zinc-600 mt-1 text-center max-w-xs">
                        Analyze a company and click "Add to Watchlist" to begin autonomous monitoring.
                    </p>
                </div>
            )}

            {/* Companies grid */}
            <div className="space-y-3">
                <AnimatePresence mode="popLayout">
                    {watchlist.map((entry, i) => (
                        <motion.div
                            key={entry.id}
                            layout
                            initial={{ opacity: 0, y: 16 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            transition={{ delay: i * 0.04 }}
                            className="group relative glass-card p-5 hover:border-primary/30 transition-all duration-300"
                        >
                            {/* left accent bar */}
                            <div className="absolute left-0 top-4 bottom-4 w-[3px] rounded-r-full bg-gradient-to-b from-primary to-accent opacity-60" />

                            <div className="flex items-start gap-4">
                                {/* Icon */}
                                <div className="flex-none flex items-center justify-center w-10 h-10 rounded-xl bg-zinc-800 border border-zinc-700/50">
                                    <Building2 size={16} className="text-zinc-400" />
                                </div>

                                {/* Info */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex flex-wrap items-center gap-2 mb-1">
                                        <h3 className="text-sm font-bold text-zinc-100">{entry.company_name}</h3>
                                        <ClassBadge cls={entry.classification} />
                                    </div>
                                    <p className="text-xs text-zinc-500 mb-3">{entry.domain} · {entry.industry}</p>

                                    {/* Metrics row */}
                                    <div className="flex flex-wrap gap-5">
                                        <div>
                                            <div className="text-[9px] uppercase tracking-widest text-zinc-600 mb-0.5 font-semibold">Lead Score</div>
                                            <div className="text-sm font-bold text-primary">{Math.round(entry.lead_score)}<span className="text-zinc-600 text-xs">/100</span></div>
                                        </div>
                                        <div>
                                            <div className="text-[9px] uppercase tracking-widest text-zinc-600 mb-0.5 font-semibold">Last Scan</div>
                                            <div className="flex items-center gap-1 text-xs text-zinc-400">
                                                <Clock size={10} />
                                                {formatDate(entry.last_scan_at)}
                                            </div>
                                        </div>
                                        <div>
                                            <div className="text-[9px] uppercase tracking-widest text-zinc-600 mb-0.5 font-semibold">Status</div>
                                            <div className="flex items-center gap-1.5">
                                                <span className="relative flex h-1.5 w-1.5">
                                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                                                    <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
                                                </span>
                                                <span className="text-xs text-emerald-400 font-medium">Monitoring Active</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="flex-none flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                        onClick={() => handleScan(entry.id)}
                                        disabled={scanningId === entry.id}
                                        title="Scan now"
                                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary text-xs font-semibold border border-primary/20 transition-all disabled:opacity-60"
                                    >
                                        <RefreshCw size={11} className={scanningId === entry.id ? "animate-spin" : ""} />
                                        {scanningId === entry.id ? "Scanning…" : "Scan Now"}
                                    </button>
                                    <button
                                        onClick={() => onRemove(entry.id)}
                                        title="Remove from watchlist"
                                        className="flex items-center justify-center w-7 h-7 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 transition-all"
                                    >
                                        <Trash2 size={11} />
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </section>
    );
}
