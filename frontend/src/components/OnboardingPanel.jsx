import { useState } from "react";
import { Loader2, Globe, CheckCircle } from "lucide-react";

export default function OnboardingPanel({ onComplete }) {
    const [url, setUrl] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const { onboardCompany } = await import("../api");
            const catalog = await onboardCompany(url);
            onComplete(catalog);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="glass-card p-6 sm:p-8 space-y-6">
            <div>
                <h3 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
                    <Globe size={20} className="text-primary" />
                    Self-Awareness Onboarding
                </h3>
                <p className="text-zinc-400 text-sm mt-1">
                    Enter your company's website to begin. The system will crawl your site to understand your services and capabilities, which will be used to identify operational gaps in prospects.
                </p>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-4">
                <input
                    type="text"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="e.g. yourcompany.com"
                    required
                    className="input-field flex-1"
                />
                <button type="submit" disabled={loading} className="btn-primary whitespace-nowrap">
                    {loading ? <Loader2 size={16} className="animate-spin inline mr-2" /> : null}
                    {loading ? "Crawling Site..." : "Analyze My Company"}
                </button>
            </form>

            {error && <div className="text-red-400 text-sm">{error}</div>}
        </div>
    );
}

export function ServiceCatalogCard({ catalog }) {
    if (!catalog) return null;
    return (
        <div className="glass-card p-6 border-emerald-500/20 bg-emerald-500/5 space-y-4">
            <div className="flex items-center gap-2 text-emerald-400 mb-2">
                <CheckCircle size={18} />
                <h3 className="font-bold">Active Service Catalog: {catalog.company_name}</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
                <div>
                    <span className="text-zinc-500 uppercase tracking-wider text-xs font-bold block mb-1">Services</span>
                    <ul className="list-disc pl-4 text-zinc-300 space-y-1">
                        {catalog.services.map(s => <li key={s} className="capitalize">{s}</li>)}
                    </ul>
                </div>
                <div>
                    <span className="text-zinc-500 uppercase tracking-wider text-xs font-bold block mb-1">Tech Expertise</span>
                    <ul className="list-disc pl-4 text-zinc-300 space-y-1">
                        {catalog.tech_expertise.map(s => <li key={s} className="capitalize">{s}</li>)}
                    </ul>
                </div>
                <div>
                    <span className="text-zinc-500 uppercase tracking-wider text-xs font-bold block mb-1">Target Industries</span>
                    <ul className="list-disc pl-4 text-zinc-300 space-y-1">
                        {catalog.target_industries.map(s => <li key={s} className="capitalize">{s}</li>)}
                    </ul>
                </div>
            </div>
        </div>
    );
}
