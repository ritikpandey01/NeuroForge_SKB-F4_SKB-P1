export const fmtTonnes = (t: number) =>
  `${t.toLocaleString("en-IN", { maximumFractionDigits: 0 })} tCO₂e`;

export const fmtTonnesCompact = (t: number) => {
  if (t >= 1000) return `${(t / 1000).toFixed(1)}k tCO₂e`;
  return `${Math.round(t)} tCO₂e`;
};

export const fmtPct = (p: number, digits = 1) => `${p.toFixed(digits)}%`;

export const fmtInrCrore = (n: number) =>
  `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 1 })} Cr`;

export const fmtInr = (rupees: number) => {
  const abs = Math.abs(rupees);
  if (abs >= 1e7) return `₹${(rupees / 1e7).toFixed(2)} Cr`;
  if (abs >= 1e5) return `₹${(rupees / 1e5).toFixed(2)} L`;
  return `₹${rupees.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
};

export const fmtPeriod = (start?: string, end?: string) => {
  if (!start && !end) return "All periods";
  return `${start ?? "…"} → ${end ?? "…"}`;
};
