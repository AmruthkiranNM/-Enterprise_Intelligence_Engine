import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Eye, EyeOff, Zap } from "lucide-react";
import { signup, signin } from "../api";

export default function AuthPage() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [mode, setMode] = useState(searchParams.get("mode") === "signin" ? "signin" : "signup");
    const [form, setForm] = useState({ name: "", email: "", password: "" });
    const [showPwd, setShowPwd] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (token) navigate("/dashboard");
    }, []);

    const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            let data;
            if (mode === "signup") {
                data = await signup(form.name, form.email, form.password);
            } else {
                data = await signin(form.email, form.password);
            }
            localStorage.setItem("token", data.token);
            localStorage.setItem("user", JSON.stringify(data.user));

            if (data.user.is_onboarded) {
                navigate("/dashboard");
            } else {
                navigate("/onboarding");
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const switchMode = (m) => {
        setMode(m);
        setError(null);
        setForm({ name: "", email: "", password: "" });
    };

    return (
        <div className="min-h-screen bg-background flex items-center justify-center px-4 relative">
            <div className="fixed top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full pointer-events-none" style={{ background: "radial-gradient(circle, rgba(110,231,183,0.09) 0%, transparent 70%)" }} />
            <div className="fixed bottom-[-20%] right-[-10%] w-[600px] h-[600px] rounded-full pointer-events-none" style={{ background: "radial-gradient(circle, rgba(244,114,182,0.08) 0%, transparent 70%)" }} />

            <motion.div
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.45 }}
                className="relative z-10 w-full max-w-md glass-card p-8 space-y-6"
            >
                {/* Logo */}
                <div className="flex items-center gap-2 mb-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                        <Zap size={16} className="text-white" />
                    </div>
                    <span className="font-bold text-zinc-300 tracking-tight text-sm">Lead Intelligence</span>
                </div>

                {/* Mode toggle */}
                <div>
                    <h2 className="text-2xl font-black text-zinc-100">
                        {mode === "signup" ? "Create your account" : "Welcome back"}
                    </h2>
                    <p className="text-zinc-500 text-sm mt-1">
                        {mode === "signup" ? "Already have an account? " : "Don't have an account? "}
                        <button
                            onClick={() => switchMode(mode === "signup" ? "signin" : "signup")}
                            className="text-primary hover:underline font-semibold"
                        >
                            {mode === "signup" ? "Sign In" : "Sign Up"}
                        </button>
                    </p>
                </div>

                <AnimatePresence mode="wait">
                    <motion.form
                        key={mode}
                        initial={{ opacity: 0, x: 10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -10 }}
                        transition={{ duration: 0.2 }}
                        onSubmit={handleSubmit}
                        className="space-y-4"
                    >
                        {mode === "signup" && (
                            <div className="space-y-1.5">
                                <label className="text-xs font-semibold text-zinc-500 uppercase tracking-widest">Full Name</label>
                                <input
                                    name="name"
                                    type="text"
                                    required={mode === "signup"}
                                    value={form.name}
                                    onChange={handleChange}
                                    placeholder="e.g. Amruthkiran N M"
                                    className="input-field w-full"
                                />
                            </div>
                        )}

                        <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-zinc-500 uppercase tracking-widest">Email</label>
                            <input
                                name="email"
                                type="email"
                                required
                                value={form.email}
                                onChange={handleChange}
                                placeholder="you@company.com"
                                className="input-field w-full"
                            />
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-zinc-500 uppercase tracking-widest">Password</label>
                            <div className="relative">
                                <input
                                    name="password"
                                    type={showPwd ? "text" : "password"}
                                    required
                                    value={form.password}
                                    onChange={handleChange}
                                    placeholder="Min. 6 characters"
                                    minLength={6}
                                    className="input-field w-full pr-10"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPwd(!showPwd)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                                >
                                    {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                            </div>
                        </div>

                        {error && (
                            <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{error}</p>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed mt-2"
                        >
                            {loading ? <Loader2 size={16} className="animate-spin" /> : null}
                            {loading ? "Please wait..." : mode === "signup" ? "Create Account" : "Sign In"}
                        </button>
                    </motion.form>
                </AnimatePresence>
            </motion.div>
        </div>
    );
}
