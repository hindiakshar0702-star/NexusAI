"use client";

import { DOMAINS, PLATFORMS, SKILLS, type Domain, type Platform, type SkillLevel } from "@/lib/api";

export function DomainSelect({
  value, onChange, includeAuto = true,
}: {
  value: Domain | "auto";
  onChange: (v: Domain | "auto") => void;
  includeAuto?: boolean;
}) {
  return (
    <select className="nx-input" value={value} onChange={(e) => onChange(e.target.value as Domain | "auto")}>
      {includeAuto && <option value="auto">domain · auto-detect</option>}
      {DOMAINS.map((d) => <option key={d} value={d}>{d}</option>)}
    </select>
  );
}

export function PlatformSelect({
  value, onChange, includeAuto = true,
}: {
  value: Platform | "auto";
  onChange: (v: Platform | "auto") => void;
  includeAuto?: boolean;
}) {
  return (
    <select className="nx-input" value={value} onChange={(e) => onChange(e.target.value as Platform | "auto")}>
      {includeAuto && <option value="auto">platform · auto-detect</option>}
      {PLATFORMS.map((p) => <option key={p} value={p}>{p}</option>)}
    </select>
  );
}

export function SkillSelect({
  value, onChange,
}: { value: SkillLevel; onChange: (v: SkillLevel) => void }) {
  return (
    <select className="nx-input" value={value} onChange={(e) => onChange(e.target.value as SkillLevel)}>
      {SKILLS.map((s) => <option key={s} value={s}>{s}</option>)}
    </select>
  );
}
