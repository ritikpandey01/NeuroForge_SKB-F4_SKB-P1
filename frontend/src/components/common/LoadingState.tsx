export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center p-8 text-sm text-slate-500">
      <span className="animate-pulse">{label}</span>
    </div>
  );
}

export function ErrorState({ error }: { error: unknown }) {
  const msg = error instanceof Error ? error.message : String(error);
  return (
    <div className="rounded-md border border-danger/30 bg-red-50 p-4 text-sm text-danger">
      Failed to load data: {msg}
    </div>
  );
}

export function EmptyState({ message = "No data yet." }: { message?: string }) {
  return (
    <div className="flex items-center justify-center p-8 text-sm text-slate-400">
      {message}
    </div>
  );
}
