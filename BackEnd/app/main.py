import re
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from llm_service import LLMService
from pdf_parser import CANONICAL_PDFS, PDFParser
import asyncio
# from llm_service import LLMService
from models import Product, RecommendationRequest, Brand
from database import mongodb
from scraperAbans import LenovoScraper


app = FastAPI(
    title="Laptop Intelligence API",
    description="Cross-marketplace laptop and review intelligence platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection
def get_llm_service():
    return LLMService()

@app.on_event("startup")
async def startup_event():
    await mongodb.connect()
    # Initialize with canonical data
    await initialize_canonical_data()

@app.on_event("shutdown")
async def shutdown_event():
    await mongodb.disconnect()


async def save_product_with_embedding(product_data: dict, llm_service: LLMService):
    text_to_embed = f"{product_data['canonical_name']} {product_data['technical_specs']}"
    embedding = await llm_service.get_embedding(text_to_embed)
    product_data["embedding"] = embedding
    await mongodb.database.products.insert_one(product_data)


async def initialize_canonical_data():
    """Initialize database with canonical PDF specs and scrape live data"""
    pdf_parser = PDFParser()
    scraper = None

    try:
        
        scraper = LenovoScraper()
        scraper.setup_driver()

        for product_key, pdf_url in CANONICAL_PDFS.items():
            # Skip if already exists
            existing = await mongodb.database.products.find_one({"sku": product_key})
            if existing:
                continue

            try:
                # Download & parse PDF
                pdf_content = pdf_parser.download_pdf(pdf_url)
                if "lenovo" in product_key:
                    specs = pdf_parser.parse_lenovo_specs(pdf_content)
                else:
                    specs = pdf_parser.parse_hp_specs(pdf_content)

                # Default product data
                product_data = {
                    "brand": "lenovo" if "lenovo" in product_key else "hp",
                    "model": product_key,
                    "sku": product_key,
                    "canonical_name": product_key.replace("_", " ").title(),
                    "technical_specs": specs,
                    "current_price": 0.0,
                    "currency": "USD",
                    "availability": "out_of_stock",
                    "review_count": 0,
                    "average_rating": 0.0,
                    "source_urls": [pdf_url],
                }

                # Scrape live data from Lenovo site (only if Lenovo product)
                if "lenovo" in product_key:
                    print(f"Scraping live data for {product_key}...")
                    scraped = scraper.search_and_scrape(product_key)
                    print(f"Scraped data: {scraped}")
                    review_count_raw = scraped.get("review_count", "0")  # e.g. "(1)"
                    review_count_clean = int(re.sub(r"[^\d]", "", review_count_raw))  # removes parentheses or other chars

                    if scraped:
                        product_data.update({
                            "current_price": scraped.get("price") or 0.0,
                            "availability": scraped.get("in_stock"),
                            "review_count": review_count_clean,
                            "average_rating": float(scraped.get("rating") or 0.0),
                            "specs_live": scraped.get("specs"),
                        })
                        print(f"Scraped live data for {product_key}: {scraped}")
                else:
                    print(f"Skipping live scrape for {product_key} (not Lenovo)")

                # Embed text with LLM if needed
                # llm_service = get_llm_service()
                # await save_product_with_embedding(product_data, llm_service)

                await mongodb.database.products.insert_one(product_data)

            except Exception as e:
                print(f"Failed to initialize {product_key}: {e}")

    finally:
        if scraper:
            scraper.close_driver()


# API Endpoints

@app.get("/")
async def root():
    return {"message": "Laptop Intelligence API v1.0"}

@app.get("/products", response_model=List[Product])
async def get_products(
    brand: Optional[Brand] = None,
    min_price: Optional[str] = None,
    max_price: Optional[str] = None,
    min_rating: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """Get products with filtering and pagination"""
    query = {}

    # Safe conversions
    def to_float(value: Optional[str], field_name: str) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value.strip())
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid value for {field_name}: {value}"
            )

    min_price = to_float(min_price, "min_price")
    max_price = to_float(max_price, "max_price")
    min_rating = to_float(min_rating, "min_rating")

    if brand:
        query["brand"] = brand
    if min_price is not None or max_price is not None:
        query["current_price"] = {}
        if min_price is not None:
            query["current_price"]["$gte"] = min_price
        if max_price is not None:
            query["current_price"]["$lte"] = max_price
    if min_rating is not None:
        query["average_rating"] = {"$gte": min_rating}

    cursor = mongodb.database.products.find(query).skip(skip).limit(limit)
    products = await cursor.to_list(length=limit)
    return products


@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get specific product by ID"""
    product = await mongodb.database.products.find_one({"_id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}