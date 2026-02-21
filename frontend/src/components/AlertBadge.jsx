/**
 * AlertBadge.jsx — Global unread alert badge with red pulse animation
 */
import { motion, AnimatePresence } from "framer-motion";
import { Bell } from "lucide-react";

export default function AlertBadge({ count, onClick }) {
    return (
        <button
            onClick={onClick}
            className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-zinc-800/60 hover:bg-zinc-700/60 border border-zinc-700/50 transition-all duration-200"
            aria-label={`${count} unread alerts`}
        >
            <Bell size={16} className="text-zinc-400" />
            <AnimatePresence>
                {count > 0 && (
                    <motion.span
                        key="badge"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        exit={{ scale: 0 }}
                        className="absolute -top-1 -right-1 flex items-center justify-center"
                    >
                        {/* pulse ring */}
                        <span className="absolute inline-flex h-4 w-4 rounded-full bg-red-500 opacity-75 animate-ping" />
                        <span className="relative flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full bg-red-500 text-white text-[9px] font-bold leading-none">
                            {count > 99 ? "99+" : count}
                        </span>
                    </motion.span>
                )}
            </AnimatePresence>
        </button>
    );
}
