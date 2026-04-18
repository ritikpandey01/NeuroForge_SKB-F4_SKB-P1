export type AuditEntry = {
  id: number;
  user: string;
  action: string;
  entity_type: string;
  entity_id: number;
  old_value: string | null;
  new_value: string | null;
  timestamp: string;
};

export type AuditPage = {
  total: number;
  limit: number;
  offset: number;
  entries: AuditEntry[];
};

export type AuditFilterOptions = {
  entity_types: string[];
  actions: string[];
  users: string[];
};

export type AuditFilters = {
  entity_type?: string;
  action?: string;
  user?: string;
  from?: string;
  to?: string;
  q?: string;
  limit: number;
  offset: number;
};
