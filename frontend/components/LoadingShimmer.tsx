"use client";

import { motion } from "framer-motion";

export function LoadingShimmer({ lines = 6 }: { lines?: number }) {
  return (
    <div className="nx-card space-y-3">
      <div className="flex items-center gap-2">
        <span className="nx-pill nx-mono bg-nx-secondary/10 text-nx-secondary border border-nx-secondary/30">
          generating
        </span>
        <motion.span
          className="h-1.5 w-1.5 rounded-full bg-nx-secondary"
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{ duration: 1.2, repeat: Infinity }}
        />
      </div>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-3 rounded-pill nx-shimmer animate-shimmer"
          style={{ width: `${85 - i * 7}%` }}
        />
      ))}
    </div>
  );
}
