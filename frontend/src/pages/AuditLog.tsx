import { useState } from "react";

import { AuditFilters } from "@/features/audit/AuditFilters";
import { AuditTable } from "@/features/audit/AuditTable";
import type { AuditFilters as AuditFiltersT } from "@/features/audit/types";

const DEFAULT: AuditFiltersT = { limit: 25, offset: 0 };

export default function AuditLog() {
  const [filters, setFilters] = useState<AuditFiltersT>(DEFAULT);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Audit Log
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Every data mutation with before/after diff — filter by entity, action,
          user, or date range. Click a row to expand the diff.
        </p>
      </div>

      <AuditFilters value={filters} onChange={setFilters} />
      <AuditTable filters={filters} onChangeFilters={setFilters} />
    </div>
  );
}
