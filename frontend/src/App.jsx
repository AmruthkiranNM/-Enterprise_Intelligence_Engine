import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Brain, AlertCircle, Search, Eye, Bell } from "lucide-react";
import AnalysisForm from "./components/AnalysisForm";
import SummaryCard from "./components/SummaryCard";
import LeadScoreChart from "./components/LeadScoreChart";
import SignalsPanel from "./components/SignalsPanel";
import BottleneckCards from "./components/BottleneckCards";
import OutreachStrategy from "./components/OutreachStrategy";
import ResearchTrace from "./components/ResearchTrace";
import RegionResultCards from "./components/RegionResultCards";
import WatchlistPanel from "./components/WatchlistPanel";
import AlertsPanel from "./components/AlertsPanel";
import AlertBadge from "./components/AlertBadge";
import { useWatchlist } from "./hooks/useWatchlist";
import { generateReports, getReportUrl } from "./api";
import { Download, FileText, Send } from "lucide-react";
import "./index.css";

const TABS = [
    { id: "analysis", label: "Analysis", icon: Search },
    { id: "watchlist", label: "Watchlist", icon: Eye },
    { id: "alerts", label: "Alerts", icon: Bell },
];

function LoadingOverlay() {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex flex-col items-center justify-center gap-5"
        >
            <div className="relative">
                <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/30 flex items-center justify-center">
                    <Brain size={28} className="text-primary" />
                </div>
                <div className="absolute -inset-1 rounded-[20px] border border-primary/20 animate-ping" />
            </div>
            <div className="text-center space-y-1">
                <p className="text-zinc-100 font-semibold">Running Strategic Analysis</p>
                <p className="text-zinc-500 text-sm">Researching signals, scoring leads…</p>
            </div>
            <div className="flex gap-1.5">
                {[0, 1, 2].map((i) => (
                    <motion.div
                        key={i}
                        className="w-1.5 h-1.5 rounded-full bg-primary"
                        animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1, 0.8] }}
                        transition={{ repeat: Infinity, duration: 1.2, delay: i * 0.2 }}
                    />
                ))}
            </div>
        </motion.div>
    );
}

/* ── Watchlist checkbox for domain results ─────────────────────────── */
function WatchlistToggle({ data, isWatched, onAdd, onRemove, watchlistId }) {
    const [busy, setBusy] = useState(false);

    const handleToggle = async () => {
        setBusy(true);
        if (isWatched) {
            await onRemove(watchlistId);
        } else {
            await onAdd({
                company_name: data?.dossier?.company_name || data?.domain || "Unknown",
                domain: data?.domain || "",
                industry: data?.dossier?.industry || "Unknown",
                classification: data?.classification || "Not Priority",
                lead_score: data?.lead_score?.total || 0,
                strategic_pressure: data?.dossier?.strategic_pressure_score || 0,
            });
        }
        setBusy(false);
    };

    return (
        <button
            onClick={handleToggle}
            disabled={busy}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold border transition-all ${isWatched
                ? "bg-primary/15 border-primary/30 text-primary hover:bg-red-500/10 hover:border-red-500/30 hover:text-red-400"
                : "bg-zinc-800/60 border-zinc-700/50 text-zinc-400 hover:bg-primary/10 hover:border-primary/30 hover:text-primary"
                }`}
        >
            <Eye size={13} />
            {busy ? "…" : isWatched ? "Watching" : "Add to Watchlist"}
        </button>
    );
}

export default function App() {
    const [activeTab, setActiveTab] = useState("analysis");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [mode, setMode] = useState(null);
    const [error, setError] = useState(null);
    const [generatingReports, setGeneratingReports] = useState(false);
    const [reportUrls, setReportUrls] = useState(null);

    const {
        watchlist, addToWatchlist, removeFromWatchlist, scanNow,
        isWatched, watchlistIdFor,
        alerts, fetchAlerts,
        unreadCount, markRead, markAllRead, deleteAlert,
    } = useWatchlist();

    const handleResult = ({ data, mode: m }) => {
        setResult(data);
        setMode(m);
        setError(null);
        setReportUrls(null); // Reset reports for new result
        setTimeout(() => {
            document.getElementById("results")?.scrollIntoView({ behavior: "smooth" });
        }, 200);
    };

    const handleDownloadReports = async () => {
        if (!result) return;
        setGeneratingReports(true);
        try {
            const urls = await generateReports(result);
            setReportUrls(urls);
        } catch (err) {
            console.error(err);
            setError("Failed to generate strategic reports.");
        } finally {
            setGeneratingReports(false);
        }
    };

    const handleError = (msg) => {
        setError(msg);
        setResult(null);
    };

    const isDomain = mode === "domain";
    const domainData = isDomain ? result : null;
    const regionData = !isDomain && Array.isArray(result) ? result : null;

    // For watchlist toggle on domain result
    const domainStr = domainData?.domain || "";
    const watched = isWatched(domainStr);
    const wlId = watchlistIdFor(domainStr);

    const handleAlertTab = () => {
        setActiveTab("alerts");
        fetchAlerts();
    };

    return (
        <div className="min-h-screen bg-background text-zinc-100">
            {/* Noise texture */}
            <div
                className="fixed inset-0 opacity-[0.015] pointer-events-none z-0"
                style={{
                    backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
                }}
            />
            {/* Gradient orbs */}
            <div className="fixed top-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-primary/5 blur-[120px] pointer-events-none z-0" />
            <div className="fixed bottom-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-accent/5 blur-[120px] pointer-events-none z-0" />

            <AnimatePresence>{loading && <LoadingOverlay />}</AnimatePresence>

            <div className="relative z-10 max-w-[1600px] mx-auto px-6 py-10 space-y-10">

                {/* ── Header ─────────────────────────────────────────────── */}
                <motion.header
                    initial={{ opacity: 0, y: -16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="flex items-start justify-between gap-4"
                >
                    <div className="space-y-2">
                        <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-lg shadow-primary/30">
                                <Brain size={16} className="text-white" />
                            </div>
                            <span className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-500">
                                DataVex
                            </span>
                        </div>
                        <h1 className="text-3xl sm:text-4xl font-black text-zinc-100 leading-tight">
                            Strategic Enterprise{" "}
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">
                                Intelligence
                            </span>
                        </h1>
                        <p className="text-zinc-500 text-sm max-w-lg">
                            AI-powered market intelligence with continuous lead monitoring.
                        </p>
                    </div>
                    {/* Alert badge */}
                    <div className="pt-1">
                        <AlertBadge count={unreadCount} onClick={handleAlertTab} />
                    </div>
                </motion.header>

                {/* ── Tab nav ─────────────────────────────────────────────── */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 }}
                    className="flex items-center gap-1 p-1 rounded-2xl bg-zinc-900/60 border border-zinc-800/60 w-fit"
                >
                    {TABS.map(({ id, label, icon: Icon }) => (
                        <button
                            key={id}
                            onClick={() => { setActiveTab(id); if (id === "alerts") fetchAlerts(); }}
                            className={`relative flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${activeTab === id
                                ? "bg-zinc-800 text-zinc-100 shadow-sm"
                                : "text-zinc-500 hover:text-zinc-300"
                                }`}
                        >
                            <Icon size={13} />
                            {label}
                            {id === "alerts" && unreadCount > 0 && (
                                <span className="flex items-center justify-center min-w-[16px] h-[16px] px-1 rounded-full bg-red-500 text-white text-[9px] font-bold">
                                    {unreadCount > 9 ? "9+" : unreadCount}
                                </span>
                            )}
                            {id === "watchlist" && watchlist.length > 0 && (
                                <span className="flex items-center justify-center min-w-[16px] h-[16px] px-1 rounded-full bg-primary text-white text-[9px] font-bold">
                                    {watchlist.length}
                                </span>
                            )}
                        </button>
                    ))}
                </motion.div>

                {/* ══════════ TAB: ANALYSIS ══════════════════════════════════ */}
                <AnimatePresence mode="wait">
                    {activeTab === "analysis" && (
                        <motion.div
                            key="analysis"
                            initial={{ opacity: 0, y: 12 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -12 }}
                            className="space-y-6"
                        >
                            {/* Input card */}
                            <div className="glass-card p-6 sm:p-8">
                                <AnalysisForm
                                    onResult={handleResult}
                                    onError={handleError}
                                    onLoading={setLoading}
                                />
                            </div>

                            {/* Error */}
                            <AnimatePresence>
                                {error && (
                                    <motion.div
                                        initial={{ opacity: 0, y: -8 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0 }}
                                        className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/25 text-red-400 text-sm"
                                    >
                                        <AlertCircle size={16} className="flex-shrink-0 mt-0.5" />
                                        <span>{error}</span>
                                    </motion.div>
                                )}
                            </AnimatePresence>

                            {/* Results */}
                            <AnimatePresence>
                                {result && (
                                    <motion.section
                                        id="results"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        className="space-y-4"
                                    >
                                        <div className="flex items-center gap-3 pb-2">
                                            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-border to-transparent" />
                                            <span className="text-xs font-semibold uppercase tracking-widest text-zinc-600">
                                                {isDomain ? "Domain Intelligence Report" : "Region Discovery Results"}
                                            </span>
                                            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-border to-transparent" />
                                        </div>

                                        {/* Domain results */}
                                        {isDomain && domainData && (
                                            <>
                                                {/* Actions Bar */}
                                                <div className="flex flex-wrap items-center justify-between gap-4 py-2">
                                                    <div className="flex items-center gap-2">
                                                        {!reportUrls ? (
                                                            <button
                                                                onClick={handleDownloadReports}
                                                                disabled={generatingReports}
                                                                className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-primary/10 border border-primary/20 text-primary hover:bg-primary hover:text-white transition-all disabled:opacity-50"
                                                            >
                                                                {generatingReports ? (
                                                                    <>
                                                                        <Loader2 size={14} className="animate-spin" />
                                                                        Generating Reports...
                                                                    </>
                                                                ) : (
                                                                    <>
                                                                        <Download size={14} />
                                                                        Generate Strategic PDFs
                                                                    </>
                                                                )}
                                                            </button>
                                                        ) : (
                                                            <div className="flex items-center gap-2">
                                                                <a
                                                                    href={getReportUrl(reportUrls.enterprise_pdf_url)}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500 hover:text-white transition-all"
                                                                >
                                                                    <FileText size={14} />
                                                                    Download Intelligence Report
                                                                </a>
                                                                <a
                                                                    href={getReportUrl(reportUrls.outreach_pdf_url)}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-violet-500/10 border border-violet-500/20 text-violet-400 hover:bg-violet-500 hover:text-white transition-all"
                                                                >
                                                                    <Send size={14} />
                                                                    Download Outreach Blueprint
                                                                </a>
                                                            </div>
                                                        )}
                                                    </div>

                                                    <WatchlistToggle
                                                        data={domainData}
                                                        isWatched={watched}
                                                        onAdd={addToWatchlist}
                                                        onRemove={removeFromWatchlist}
                                                        watchlistId={wlId}
                                                    />
                                                </div>
                                                <SummaryCard data={domainData} />
                                                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                                                    <div className="lg:col-span-8 space-y-8">
                                                        <LeadScoreChart data={domainData} />
                                                        <OutreachStrategy data={domainData} />
                                                    </div>
                                                    <div className="lg:col-span-4 space-y-8">
                                                        <SignalsPanel data={domainData} />
                                                        <BottleneckCards data={domainData} />
                                                    </div>
                                                    <div className="lg:col-span-12">
                                                        <ResearchTrace data={domainData} />
                                                    </div>
                                                </div>
                                            </>
                                        )}

                                        {/* Region results */}
                                        {!isDomain && regionData && (
                                            <RegionResultCards
                                                results={regionData}
                                                watchlist={watchlist}
                                                onAddToWatchlist={addToWatchlist}
                                                onRemoveFromWatchlist={removeFromWatchlist}
                                                isWatched={isWatched}
                                                watchlistIdFor={watchlistIdFor}
                                            />
                                        )}
                                    </motion.section>
                                )}
                            </AnimatePresence>
                        </motion.div>
                    )}

                    {/* ══════════ TAB: WATCHLIST ════════════════════════════ */}
                    {activeTab === "watchlist" && (
                        <motion.div
                            key="watchlist"
                            initial={{ opacity: 0, y: 12 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -12 }}
                        >
                            <WatchlistPanel
                                watchlist={watchlist}
                                onRemove={removeFromWatchlist}
                                onScanNow={scanNow}
                            />
                        </motion.div>
                    )}

                    {/* ══════════ TAB: ALERTS ═══════════════════════════════ */}
                    {activeTab === "alerts" && (
                        <motion.div
                            key="alerts"
                            initial={{ opacity: 0, y: 12 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -12 }}
                        >
                            <AlertsPanel
                                alerts={alerts}
                                onMarkRead={markRead}
                                onMarkAllRead={markAllRead}
                                onDelete={deleteAlert}
                            />
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
