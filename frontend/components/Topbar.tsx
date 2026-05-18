"use client";

import { motion } from "framer-motion";
import { Wand2 } from "lucide-react";
import { ReactNode } from "react";

export function Topbar({
  title,
  subtitle,
  right,
}: {
  title: string;
  subtitle?: string;
  right?: ReactNode;
}) {
  return (
    <header className="flex flex-col gap-1 md:flex-row md:items-end md:justify-between mb-6">
      <div>
        <motion.h1
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
          className="font-display text-3xl md:text-4xl font-semibold tracking-tightest"
        >
          {title}
        </motion.h1>
        {subtitle && (
          <p className="nx-mono text-xs uppercase tracking-widest opacity-60 mt-1">{subtitle}</p>
        )}
      </div>
      <div className="flex items-center gap-2">
        {right}
        <span className="nx-pill nx-mono bg-nx-secondary/10 text-nx-secondary border border-nx-secondary/30">
          <Wand2 className="h-3 w-3" /> live
        </span>
      </div>
    </header>
  );
}
