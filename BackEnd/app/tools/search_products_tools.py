from typing import Optional
import json
from google.adk.tools import FunctionTool
from utils import update_interaction_history
from services import MongoSessionService


from database import mongodb


def get_llm_service():
    from llm_service import LLMService

    return LLMService()


def replace_none_with_missing(data: dict) -> dict:
    """Replace None values with 'Value is Missing' ONLY for brand-new fields."""
    print("Original data:", data)
    processed_data = {}
    for k, v in data.items():
        if v is None:
            continue
        processed_data[k] = v if v is not None else "Value is Missing"
    print("Processed data:", processed_data)
    return processed_data


async def search_products_tool_function(
    query: str,
    app_name: str,
    user_id: str,
    session_id: str,
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
        app_name: Identifier of the calling application (required).
        user_id: User identifier for session tracking (required).
        session_id: Current chat session identifier (required).

    Returns:
        success message
    """
    try:
        required_fields = {
            "app_name": app_name,
            "user_id": user_id,
            "session_id": session_id,
        }
        db = mongodb.database
        session_collection = db["ChatSessions"]
        session_service = MongoSessionService(collection=session_collection)
        print("session id ,", session_id, user_id, app_name)
        current_session = await session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )
        if current_session is None:
            print("session not found error")
            return "Session not found."

        missing = [
            name for name, value in required_fields.items() if value in (None, "")
        ]
        if missing:
            raise ValueError(f"Missing required parameter(s): {', '.join(missing)}")

        print(
            f"[Utils] Searching products with query: {query}, min_price: {min_price}, max_price: {max_price}"
        )
        pipeline = [
            # {
            #     "$search": {
            #         "index": "default",
            #         "text": {"query": query, "path": {"wildcard": "*"}},
            #     }
            # }
        ]
        print("price arnge ", min_price, max_price)

        price_filter = {}
        if min_price is not None:
            price_filter["$gte"] = float(min_price)
        if max_price is not None:
            price_filter["$lte"] = float(max_price)

        if price_filter:
            pipeline.append({"$match": {"current_price": price_filter}})

        pipeline.append({"$project": {"_id": 0, "embedding": 0}})
        pipeline.append({"$limit": 10})

        cursor = mongodb.database.products.aggregate(pipeline)
        results = await cursor.to_list(length=10)

        for doc in results:
            specs = doc.get("technical_specs", {})
            for field in ["weight", "memory", "processor"]:
                if field in specs and isinstance(specs[field], list):
                    specs[field] = specs[field][0]
            doc["technical_specs"] = specs

        llm_service = get_llm_service()
        raw_data = json.dumps(results, indent=2)
        print("raw data", raw_data)
        summary = await llm_service.summarize_text(raw_data)

        print("summary:", summary)
        print("Updating price range in session state for user_id:")

        current_price_range_details = current_session.state.get("price_range", {})
        print("Current price_range details:", current_price_range_details)

        updates_dict = replace_none_with_missing(
            {"min_price": min_price, "max_price": max_price}
        )

        merged_price_details = {**current_price_range_details, **updates_dict}

        print("Merged price_range details:", merged_price_details)

        await update_interaction_history(
            session_service=session_service,
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            price_range=merged_price_details,
            context=summary,
        )

        print("Interaction history updated successfully.")

        return summary

    except Exception as e:
        print(f"[Utils Error] Failed to search products: {e}")
        return {"error": f"[Utils Error] Failed to search products: {e}"}


search_products_tool = FunctionTool(func=search_products_tool_function)
