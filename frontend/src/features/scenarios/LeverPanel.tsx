import { RotateCcw, Target, Zap } from "lucide-react";

import { Button } from "@/components/ui/button";

import { LEVER_LABELS, ZERO_LEVERS } from "./types";
import type { Levers, LeverName, PresetName } from "./types";

const PRESETS: Record<Exclude<PresetName, "business_as_usual">, Levers> = {
  net_zero_2050: {
    renewable_electricity_share: 100,
    energy_efficiency_pct: 80,
    fleet_electrification: 90,
    supplier_engagement: 80,
    logistics_mode_shift: 60,
  },
  sbti_1p5: {
    renewable_electricity_share: 70,
    energy_efficiency_pct: 50,
    fleet_electrification: 60,
    supplier_engagement: 50,
    logistics_mode_shift: 40,
  },
};

type Props = {
  levers: Levers;
  targetYear: number;
  carbonPrice: number;
  onLeversChange: (next: Levers) => void;
  onTargetYearChange: (y: number) => void;
  onCarbonPriceChange: (price: number) => void;
};

export function LeverPanel({
  levers,
  targetYear,
  carbonPrice,
  onLeversChange,
  onTargetYearChange,
  onCarbonPriceChange,
}: Props) {
  const setLever = (name: LeverName, value: number) =>
    onLeversChange({ ...levers, [name]: value });

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <label className="text-[11px] font-semibold uppercase tracking-widest text-slate-500">
          Target year
        </label>
        <input
          type="number"
          min={2026}
          max={2100}
          value={targetYear}
          onChange={(e) => onTargetYearChange(Number(e.target.value))}
          className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
        />
      </div>

      <div className="space-y-2">
        <label className="text-[11px] font-semibold uppercase tracking-widest text-slate-500">
          Carbon price (₹ / tCO₂e)
        </label>
        <input
          type="number"
          min={0}
          step={100}
          value={carbonPrice}
          onChange={(e) => onCarbonPriceChange(Number(e.target.value))}
          className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          title="Shadow price used for carbon exposure overlay. Default 2,000 ₹/t ≈ $24."
        />
        <div className="flex gap-1 text-[10px]">
          <button
            type="button"
            onClick={() => onCarbonPriceChange(2000)}
            className="rounded bg-slate-100 px-2 py-1 text-slate-600 hover:bg-slate-200"
          >
            India 2k
          </button>
          <button
            type="button"
            onClick={() => onCarbonPriceChange(5000)}
            className="rounded bg-slate-100 px-2 py-1 text-slate-600 hover:bg-slate-200"
          >
            CBAM 5k
          </button>
          <button
            type="button"
            onClick={() => onCarbonPriceChange(8000)}
            className="rounded bg-slate-100 px-2 py-1 text-slate-600 hover:bg-slate-200"
          >
            EU-ETS 8k
          </button>
        </div>
      </div>

      <div className="space-y-3">
        <div className="text-[11px] font-semibold uppercase tracking-widest text-slate-500">
          Decarbonization levers
        </div>
        {(Object.keys(LEVER_LABELS) as LeverName[]).map((name) => (
          <LeverSlider
            key={name}
            name={name}
            value={levers[name]}
            onChange={(v) => setLever(name, v)}
          />
        ))}
      </div>

      <div className="space-y-2">
        <div className="text-[11px] font-semibold uppercase tracking-widest text-slate-500">
          Presets
        </div>
        <div className="grid grid-cols-1 gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onLeversChange(PRESETS.net_zero_2050)}
          >
            <Target size={12} />
            Net-zero 2050
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onLeversChange(PRESETS.sbti_1p5)}
          >
            <Zap size={12} />
            SBTi 1.5°C
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onLeversChange({ ...ZERO_LEVERS })}>
            <RotateCcw size={12} />
            Reset all
          </Button>
        </div>
      </div>
    </div>
  );
}

function LeverSlider({
  name,
  value,
  onChange,
}: {
  name: LeverName;
  value: number;
  onChange: (v: number) => void;
}) {
  const meta = LEVER_LABELS[name];
  return (
    <div className="space-y-1">
      <div className="flex items-baseline justify-between">
        <div className="flex flex-col">
          <span className="text-xs font-medium text-slate-800">{meta.title}</span>
          <span className="text-[10px] uppercase tracking-wider text-slate-400">
            {meta.affects}
          </span>
        </div>
        <span className="font-mono text-xs font-semibold text-brand">{Math.round(value)}%</span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        title={meta.tooltip}
        className="w-full cursor-pointer accent-teal-600"
      />
    </div>
  );
}
