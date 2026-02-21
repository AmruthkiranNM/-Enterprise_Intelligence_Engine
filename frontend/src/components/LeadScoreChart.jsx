import {
    Radar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    ResponsiveContainer,
    Tooltip,
} from "recharts";
import { motion } from "framer-motion";

const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-zinc-900 border border-border rounded-lg px-3 py-2 text-sm shadow-xl">
                <p className="text-zinc-300 font-semibold">{payload[0].payload.axis}</p>
                <p className="text-primary font-bold">{payload[0].value}/100</p>
            </div>
        );
    }
    return null;
};

export default function LeadScoreChart({ data }) {
    const scores = data.lead_score?.scores || {};
    const total = data.lead_score?.total || 0;

    const chartData = Object.entries(scores).map(([axis, value]) => ({
        axis,
        value,
        fullMark: 100,
    }));

    if (chartData.length === 0) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="glass-card p-6"
        >
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest mb-1">
                        Lead Score Breakdown
                    </h3>
                    <p className="text-xs text-zinc-600">Multi-axis intelligence assessment</p>
                </div>
                <div className="text-right">
                    <div className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-br from-primary to-accent">
                        {total}
                    </div>
                    <div className="text-xs text-zinc-500 font-medium">/ 100</div>
                </div>
            </div>

            <ResponsiveContainer width="100%" height={260}>
                <RadarChart data={chartData} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
                    <PolarGrid stroke="#27272a" />
                    <PolarAngleAxis
                        dataKey="axis"
                        tick={{ fill: "#71717a", fontSize: 11, fontWeight: 500 }}
                    />
                    <Radar
                        name="Score"
                        dataKey="value"
                        stroke="#6366f1"
                        fill="#6366f1"
                        fillOpacity={0.2}
                        strokeWidth={2}
                        dot={{ fill: "#6366f1", r: 4 }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                </RadarChart>
            </ResponsiveContainer>

            {/* Legend */}
            <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-2">
                {chartData.map(({ axis, value }) => (
                    <div key={axis} className="flex items-center justify-between bg-zinc-900/50 rounded-lg px-3 py-2">
                        <span className="text-xs text-zinc-400">{axis}</span>
                        <span className="text-xs font-bold text-zinc-200">{value}</span>
                    </div>
                ))}
            </div>
        </motion.div>
    );
}
