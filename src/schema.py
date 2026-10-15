from typing import Literal, Optional
from pydantic import BaseModel, Field

class ProductAttributes(BaseModel):
    water: Literal["waterproof", "water_resistant", "none"] = "none"
    lightweight: bool = False
    weight_oz: Optional[float] = None
    materials: list[str] = Field(default_factory=list)
    intended_use: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    review_waterproof_contradiction: bool = False
    review_durability_issue: bool = False
    review_summary: str = ""

class Product(ProductAttributes):
    id: int
    title: str
    category: str
    price: float
    rating: float

class Query(BaseModel):
    category: Optional[str] = None
    max_price: Optional[float] = None
    needs: list[str] = Field(default_factory=list)   # e.g. ["waterproof", "lightweight"]
    wants_basic: bool = False
    vague: bool = False
    raw: str = ""