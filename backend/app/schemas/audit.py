from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user: str
    action: str
    entity_type: str
    entity_id: int
    old_value: str | None
    new_value: str | None
    timestamp: datetime


class AuditPage(BaseModel):
    total: int
    limit: int
    offset: int
    entries: list[AuditEntry]


class AuditFilterOptions(BaseModel):
    entity_types: list[str]
    actions: list[str]
    users: list[str]
