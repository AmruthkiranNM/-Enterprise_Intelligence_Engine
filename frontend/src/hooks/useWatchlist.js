/**
 * useWatchlist.js — Custom hook for watchlist and alert state
 * Polls /alerts/unread-count every 30 seconds for real-time notifications.
 */

import { useState, useEffect, useCallback, useRef } from "react";

const API = "http://localhost:8000";

export function useWatchlist() {
    const [watchlist, setWatchlist] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [loadingWL, setLoadingWL] = useState(false);
    const [loadingAL, setLoadingAL] = useState(false);
    const pollRef = useRef(null);

    // ── fetch helpers ────────────────────────────────────────────────────────
    const fetchWatchlist = useCallback(async () => {
        setLoadingWL(true);
        try {
            const res = await fetch(`${API}/watchlist`);
            if (res.ok) setWatchlist(await res.json());
        } catch { /* offline — ignore */ }
        finally { setLoadingWL(false); }
    }, []);

    const fetchAlerts = useCallback(async () => {
        setLoadingAL(true);
        try {
            const res = await fetch(`${API}/alerts`);
            if (res.ok) setAlerts(await res.json());
        } catch { /* offline */ }
        finally { setLoadingAL(false); }
    }, []);

    const fetchUnreadCount = useCallback(async () => {
        try {
            const res = await fetch(`${API}/alerts/unread-count`);
            if (res.ok) {
                const data = await res.json();
                setUnreadCount(data.count ?? 0);
            }
        } catch { /* offline */ }
    }, []);

    // ── watchlist actions ────────────────────────────────────────────────────
    const addToWatchlist = useCallback(async (company) => {
        try {
            const res = await fetch(`${API}/watchlist`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(company),
            });
            if (res.ok || res.status === 409) {
                await fetchWatchlist();
                return true;
            }
        } catch { /* offline */ }
        return false;
    }, [fetchWatchlist]);

    const removeFromWatchlist = useCallback(async (id) => {
        try {
            await fetch(`${API}/watchlist/${id}`, { method: "DELETE" });
            setWatchlist(prev => prev.filter(e => e.id !== id));
        } catch { /* offline */ }
    }, []);

    const scanNow = useCallback(async (id) => {
        try {
            await fetch(`${API}/watchlist/${id}/scan`, { method: "POST" });
        } catch { /* offline */ }
    }, []);

    const isWatched = useCallback((domain) => {
        return watchlist.some(e => e.domain === domain && e.is_active);
    }, [watchlist]);

    const watchlistIdFor = useCallback((domain) => {
        return watchlist.find(e => e.domain === domain)?.id ?? null;
    }, [watchlist]);

    // ── alert actions ────────────────────────────────────────────────────────
    const markRead = useCallback(async (alertId) => {
        try {
            await fetch(`${API}/alerts/${alertId}/read`, { method: "POST" });
            setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, is_read: true } : a));
            setUnreadCount(prev => Math.max(0, prev - 1));
        } catch { /* offline */ }
    }, []);

    const markAllRead = useCallback(async () => {
        try {
            await fetch(`${API}/alerts/read-all`, { method: "POST" });
            setAlerts(prev => prev.map(a => ({ ...a, is_read: true })));
            setUnreadCount(0);
        } catch { /* offline */ }
    }, []);

    const deleteAlert = useCallback(async (alertId) => {
        try {
            await fetch(`${API}/alerts/${alertId}`, { method: "DELETE" });
            setAlerts(prev => prev.filter(a => a.id !== alertId));
            setUnreadCount(prev => Math.max(0, prev - 1));
        } catch { /* offline */ }
    }, []);

    const scanWatchlist = useCallback(async () => {
        const activeEntries = watchlist.filter(e => e.is_active);
        for (const entry of activeEntries) {
            await scanNow(entry.id);
        }
    }, [watchlist, scanNow]);

    // ── initialization + polling ─────────────────────────────────────────────
    useEffect(() => {
        const init = async () => {
            await fetchWatchlist();
            await fetchAlerts();
            await fetchUnreadCount();
        };
        init();

        // Poll unread count every 30s
        pollRef.current = setInterval(fetchUnreadCount, 30_000);
        return () => clearInterval(pollRef.current);
    }, [fetchWatchlist, fetchAlerts, fetchUnreadCount]);

    return {
        watchlist, loadingWL, fetchWatchlist,
        addToWatchlist, removeFromWatchlist, scanNow, isWatched, watchlistIdFor,
        alerts, loadingAL, fetchAlerts,
        unreadCount,
        markRead, markAllRead, deleteAlert,
    };
}
