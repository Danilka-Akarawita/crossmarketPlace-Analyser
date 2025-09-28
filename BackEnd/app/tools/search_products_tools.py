from typing import Optional
import json
from google.adk.tools import FunctionTool
from services import MongoSessionService

# Assuming mongodb and get_llm_service are already imported in your app
# from your existing search endpoint file
from database import mongodb


def get_llm_service():
    # Import inside the function to avoid a circular import with llm_service.
    from llm_service import LLMService

    return LLMService()
    
async def search_products_tool_function(
    query: str,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> dict:
    """
    Search products using MongoDB Atlas Search index and optional price filtering.
    Also summarize the results using the LLM service.

    Args:
        query: Search text from the user.
        min_price: Minimum product price to filter.
        max_price: Maximum product price to filter.

    Returns:
        dict with two keys:
        - "products": list of matched product docs (excluding _id and embedding)
        - "summary": concise natural-language summary of those products
    """
    try:
        print(f"[Utils] Searching products with query: {query}, min_price: {min_price}, max_price: {max_price}")
        pipeline = [
            {
                "$search": {
                    "index": "default",
                    "text": {"query": query, "path": {"wildcard": "*"}},
                }
            }
        ]

        # price filtering if provided
        price_filter = {}
        if min_price is not None:
            price_filter["$gte"] = min_price
        if max_price is not None:
            price_filter["$lte"] = max_price
        if price_filter:
            pipeline.append({"$match": {"current_price": price_filter}})

        # project and limit
        pipeline.append({"$project": {"_id": 0, "embedding": 0}})
        pipeline.append({"$limit":  10})

        # run aggregation
        cursor = mongodb.database.products.aggregate(pipeline)
        results = await cursor.to_list(length= 10)

        # normalize specs (same logic as before)
        for doc in results:
            specs = doc.get("technical_specs", {})
            for field in ["weight", "memory", "processor"]:
                if field in specs and isinstance(specs[field], list):
                    specs[field] = specs[field][0]
            doc["technical_specs"] = specs

        # get summary from LLM
        llm_service = get_llm_service()
        raw_data = json.dumps(results, indent=2)
        summary = await llm_service.summarize_text(raw_data)
        
        print(f"[Utils] Search results: {len(results)} products found")

        return {"products": results, "summary": summary}

    except Exception as e:
        print(f"[Utils Error] Failed to search products: {e}")
        return {"error": f"[Utils Error] Failed to search products: {e}"}

search_products_tool = FunctionTool(func=search_products_tool_function)
