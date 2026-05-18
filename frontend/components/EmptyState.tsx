"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

export function EmptyState({
  title,
  description,
  icon,
}: {
  title: string;
  description: string;
  icon?: ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className="nx-card flex flex-col items-center text-center gap-3 py-12"
    >
      {icon && <div className="opacity-60">{icon}</div>}
      <h3 className="font-display text-xl">{title}</h3>
      <p className="text-sm opacity-70 max-w-md">{description}</p>
    </motion.div>
  );
}
