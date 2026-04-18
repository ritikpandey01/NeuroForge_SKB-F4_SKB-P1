from pydantic import BaseModel, ConfigDict


class EmissionFactorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    subcategory: str
    factor_value: float
    unit: str
    source: str
    region: str
    year: int
