import { Globe, BarChart2, TrendingUp, Star } from "lucide-react";
import { motion } from "framer-motion";

function confidenceBadge(level) {
    const cfg = {
        High: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/25",
        Medium: "bg-amber-500/15 text-amber-400 border border-amber-500/25",
        Low: "bg-red-500/15 text-red-400 border border-red-500/25",
    };
    return cfg[level] || cfg.Low;
}

function likelihoodColor(likelihood) {
    if (!likelihood) return "text-zinc-400";
    const l = likelihood.toLowerCase();
    if (l.startsWith("likely")) return "text-emerald-400";
    if (l.startsWith("possibly")) return "text-amber-400";
    return "text-red-400";
}

export default function RegionResultCards({ results }) {
    if (!results || results.length === 0) {
        return (
            <div className="glass-card p-10 text-center text-zinc-500 text-sm">
                No companies found matching the criteria.
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest px-1">
                {results.length} Candidate{results.length !== 1 ? "s" : ""} Found
            </h3>

            {results.map((company, i) => (
                <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.08 }}
                    className="glass-card p-5 space-y-3 hover:border-zinc-600/50 transition-colors"
                >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                            <h4 className="text-base font-bold text-zinc-100">{company.company_name}</h4>
                            <div className="flex items-center gap-1.5 mt-0.5">
                                <Globe size={11} className="text-zinc-500" />
                                <span className="text-xs text-zinc-500">{company.website}</span>
                            </div>
                        </div>
                        <div className="flex items-center flex-wrap gap-2">
                            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${confidenceBadge(company.confidence_level)}`}>
                                Confidence: {company.confidence_level}
                            </span>
                        </div>
                    </div>

                    <div className="flex flex-wrap gap-3">
                        <div className="flex items-center gap-1.5">
                            <BarChart2 size={12} className="text-zinc-500" />
                            <span className="text-xs text-zinc-400">{company.industry}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <TrendingUp size={12} className="text-zinc-500" />
                            <span className="text-xs text-zinc-400">{company.business_stage}</span>
                        </div>
                    </div>

                    {company.revenue_likelihood && (
                        <div className="flex items-center gap-2">
                            <Star size={12} className="text-amber-400" />
                            <span className={`text-xs font-semibold ${likelihoodColor(company.revenue_likelihood)}`}>
                                {company.revenue_likelihood}
                            </span>
                        </div>
                    )}

                    {company.supporting_signals?.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 pt-1">
                            {company.supporting_signals.map((sig, j) => (
                                <span
                                    key={j}
                                    className="text-[10px] px-2 py-0.5 bg-zinc-900 border border-zinc-800 text-zinc-400 rounded-md"
                                >
                                    {sig}
                                </span>
                            ))}
                        </div>
                    )}
                </motion.div>
            ))}
        </div>
    );
}
