import { CheckCircle2, AlertTriangle, Info } from "lucide-react";

export default function GapAnalysisPanel({ gaps }) {
    if (!gaps || gaps.length === 0) return null;

    return (
        <div className="glass-card p-6 space-y-4">
            <h3 className="text-lg font-bold text-zinc-100 mb-2">Operational Gap Analysis</h3>

            <div className="space-y-4">
                {gaps.map((gap, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800 flex flex-col gap-3">
                        <div className="flex items-start justify-between">
                            <div className="flex items-center gap-2 text-primary">
                                <AlertTriangle size={16} />
                                <span className="font-semibold text-sm">Identified Gap</span>
                            </div>
                        </div>
                        <p className="text-sm text-zinc-300 font-medium">{gap.gap}</p>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
                            <div className="bg-zinc-950 p-3 rounded-lg border border-zinc-800/80">
                                <span className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider mb-1 block">Contextual Evidence</span>
                                <p className="text-xs text-zinc-400">{gap.evidence}</p>
                            </div>
                            <div className="bg-emerald-500/10 p-3 rounded-lg border border-emerald-500/20">
                                <span className="text-[10px] text-emerald-500/70 uppercase font-bold tracking-wider mb-1 block">Matched Solution</span>
                                <p className="text-xs text-emerald-400 font-medium capitalize">{gap.matched_service}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
