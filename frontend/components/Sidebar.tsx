"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  Activity,
  Boxes,
  GitBranch,
  Gauge,
  Library,
  Sparkles,
  ShieldCheck,
  Brain,
  Database,
  Settings,
} from "lucide-react";
import { useTheme } from "./ThemeProvider";
import { cn } from "@/lib/cn";

const NAV = [
  { href: "/", label: "Dashboard", icon: Activity },
  { href: "/generate", label: "Generator", icon: Sparkles },
  { href: "/analyze", label: "Analyzer", icon: Gauge },
  { href: "/chains", label: "Chain Builder", icon: GitBranch },
  { href: "/agents", label: "Multi-Agent", icon: Brain },
  { href: "/library", label: "Templates", icon: Library },
  { href: "/training", label: "Training", icon: Boxes },
  { href: "/safety", label: "Safety", icon: ShieldCheck },
  { href: "/memory", label: "Memory", icon: Database },
];

export function Sidebar() {
  const pathname = usePathname();
  const { theme, toggle } = useTheme();

  return (
    <aside className="hidden md:flex md:w-64 lg:w-72 shrink-0 flex-col gap-3 p-4 sticky top-0 h-screen">
      <Link href="/" className="nx-card flex items-center gap-3">
        <div className="relative h-9 w-9 rounded-pill bg-nx-primary text-white grid place-items-center">
          <span className="font-display font-bold text-lg leading-none">N</span>
          <motion.span
            className="absolute inset-0 rounded-pill"
            style={{ boxShadow: "0 0 0 2px rgba(234,67,19,0.4)" }}
            animate={{ scale: [1, 1.06, 1], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
          />
        </div>
        <div className="leading-tight">
          <div className="font-display text-base font-semibold tracking-tightest">NEXUSAI</div>
          <div className="nx-mono text-[10px] uppercase tracking-widest opacity-60">
            autonomous prompt OS
          </div>
        </div>
      </Link>

      <nav className="nx-card flex-1 overflow-y-auto">
        <div className="nx-section-title mb-3">Navigate</div>
        <ul className="flex flex-col gap-1">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <li key={href}>
                <Link
                  href={href}
                  className={cn(
                    "group flex items-center gap-3 rounded-pill px-3 py-2 text-sm transition-colors duration-nx-fast",
                    active
                      ? "bg-nx-primary text-white shadow-nx-glass"
                      : "hover:bg-black/5 dark:hover:bg-white/5"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span className="font-medium">{label}</span>
                  {active && (
                    <motion.span
                      layoutId="nav-dot"
                      className="ml-auto h-1.5 w-1.5 rounded-full bg-nx-secondary"
                    />
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <button
        onClick={toggle}
        className="nx-card flex items-center justify-between text-sm font-medium hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
      >
        <span className="flex items-center gap-2">
          <Settings className="h-4 w-4" />
          Theme
        </span>
        <span className="nx-mono text-[11px] uppercase tracking-wider opacity-70">
          {theme}
        </span>
      </button>
    </aside>
  );
}
