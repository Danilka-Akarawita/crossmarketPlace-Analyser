from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"

class AvailabilityStatus(str, Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    PRE_ORDER = "pre_order"
    LIMITED = "limited"

class Brand(str, Enum):
    LENOVO = "lenovo"
    HP = "hp"

class TechnicalSpecs(BaseModel):
    processor: Optional[str] = None
    memory: Optional[str] = None
    storage: Optional[str] = None
    display: Optional[str] = None
    graphics: Optional[str] = None
    operating_system: Optional[str] = None
    battery: Optional[str] = None
    weight: Optional[str] = None
    dimensions: Optional[str] = None
    ports: Optional[List[str]] = None
    wireless: Optional[List[str]] = None

class PriceHistory(BaseModel):
    price: float
    currency: Currency
    date: datetime
    promo_applied: bool = False

class Review(BaseModel):
    rating: float = Field(ge=1, le=5)
    title: str
    content: str
    author: Optional[str] = None
    date: datetime
    verified_purchase: bool = False
    helpful_votes: int = 0

class Product(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    brand: Brand
    model: str
    sku: str
    canonical_name: str
    technical_specs: TechnicalSpecs
    
    # Marketplace data
    current_price: float
    currency: Currency
    availability: AvailabilityStatus
    shipping_eta: Optional[str] = None
    promo_badges: List[str] = []
    seller: Optional[str] = None
    
    # Reviews & ratings
    review_count: int = 0
    average_rating: float = Field(ge=0, le=5)
    reviews: List[Review] = []
    qa_excerpts: List[str] = []
    
    # Metadata
    source_urls: List[str] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    price_history: List[PriceHistory] = []

class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RecommendationRequest(BaseModel):
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    preferred_brands: List[Brand] = []
    must_have_specs: Dict[str, Any] = {}
    preferred_use_case: str  # business, programming, design, etc.
    min_rating: float = Field(ge=0, le=5, default=3.0)

class RecommendationResponse(BaseModel):
    recommended_products: List[Product]
    rationale: str
    citations: List[str]