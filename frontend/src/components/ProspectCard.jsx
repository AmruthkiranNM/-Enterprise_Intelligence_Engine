import { Building, BarChart3, Target, Mail } from "lucide-react";
import GapAnalysisPanel from "./GapAnalysisPanel";
import ResearchTrace from "./ResearchTrace";

export default function ProspectCard({ data }) {
    if (!data || !data.prospect_profile) return null;

    return (
        <div className="space-y-8">
            {/* Profile Overview */}
            <div className="glass-card p-6 border-zinc-700/50 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[80px] rounded-full" />
                <div className="flex flex-col sm:flex-row items-start justify-between gap-4">
                    <div>
                        <h2 className="text-2xl font-bold font-display text-zinc-100 flex items-center gap-2">
                            <Building size={24} className="text-primary" />
                            {data.prospect_profile.domain || "Prospect Domain"}
                        </h2>
                        <div className="flex flex-wrap items-center gap-2 mt-3 text-xs font-semibold text-zinc-400">
                            <span className="px-2.5 py-1 bg-zinc-800/80 rounded-md border border-zinc-700/80 uppercase tracking-widest">{data.prospect_profile.industry || "Unknown Industry"}</span>
                            <span className="px-2.5 py-1 bg-zinc-800/80 rounded-md border border-zinc-700/80 uppercase tracking-widest">{data.prospect_profile.business_stage || "Unknown Stage"}</span>
                        </div>
                    </div>

                    <div className="text-left sm:text-right">
                        <span className={`inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl text-sm font-bold border ${data.lead_verdict === "Strong Lead" ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400" : data.lead_verdict === "Medium Lead" ? "bg-amber-500/10 border-amber-500/30 text-amber-400" : "bg-zinc-800 border-zinc-700 text-zinc-400"}`}>
                            {data.lead_verdict === "Strong Lead" && <Target size={15} className="text-emerald-400" />}
                            {data.lead_verdict}
                        </span>
                        {data.justification && <p className="text-xs text-zinc-500 mt-2 max-w-[240px] leading-relaxed">{data.justification}</p>}
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Context Signals */}
                <div className="glass-card p-6">
                    <h3 className="text-lg font-bold text-zinc-100 mb-5 flex items-center gap-2">
                        <BarChart3 size={18} className="text-primary" />
                        External Context Signals
                    </h3>
                    {data.context_signals && data.context_signals.length > 0 ? (
                        <ul className="space-y-4">
                            {data.context_signals.map((sig, idx) => (
                                <li key={idx} className="flex gap-3 text-sm text-zinc-300 bg-zinc-900/40 p-3 rounded-lg border border-zinc-800/50">
                                    <div className="mt-1.5 min-w-[6px] h-[6px] rounded-full bg-primary" />
                                    <span className="leading-relaxed">{sig}</span>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-zinc-500 text-sm italic">No acute external signals detected.</p>
                    )}
                </div>

                {/* Gap Analysis */}
                <div className="col-span-1 lg:col-span-1">
                    <GapAnalysisPanel gaps={data.gap_analysis} />
                </div>
            </div>

            {/* Outreach */}
            {data.lead_verdict !== "Weak Lead" && data.outreach_email && data.outreach_email !== "Not generated (Weak Lead)" && (
                <div className="glass-card p-6 bg-gradient-to-br from-zinc-900/90 to-zinc-950/90 border border-primary/20 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-full h-1 bg-gradient-to-r from-transparent via-primary/50 to-transparent" />
                    <h3 className="text-lg font-bold text-zinc-100 mb-4 flex items-center gap-2">
                        <Mail size={18} className="text-primary" />
                        Personalized Outreach Strategy
                    </h3>
                    <div className="p-5 rounded-xl bg-black/50 border border-zinc-800/80 text-sm text-zinc-300 whitespace-pre-wrap font-mono leading-relaxed shadow-inner">
                        {data.outreach_email}
                    </div>
                </div>
            )}

            {/* Agent Trace */}
            <ResearchTrace data={data} />
        </div>
    );
}
