from datetime import datetime
import types
from google.genai.types import Content, Part
from google.adk.sessions import InMemorySessionService
import asyncio

AGENT_CALL_SEMAPHORE=asyncio.Semaphore(50)
MAX_HISTORY_ITEMS=10

async def update_interaction_history(session_service, app_name, user_id, session_id, entry: dict=None,price_range: dict = None,context: str = None):
    """Update the interaction history for a session."""
    try:
        session = await session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

        if not session:
            raise ValueError("Session not found.")

        history = session.state.get("interaction_history", [])
        entry["timestamp"] = entry.get("timestamp", datetime.utcnow().isoformat())
        history.append(entry)
        
        if len(history) > MAX_HISTORY_ITEMS:
            history = history[-MAX_HISTORY_ITEMS:]

        new_state = session.state.copy()
        new_state["interaction_history"] = history
        
        
        if price_range is not None:
            price_range_details = new_state.get("price_range", {})
            price_range_details.update(price_range)
            new_state["price_range"] = price_range_details
        
        if context is not None:
            new_state["context"] = context
            
        print(f"Updated session state: {new_state}")
        
        await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            state=new_state
        )
    except Exception as e:
        print(f"[Utils Error] update_interaction_history failed: {e}")


async def add_user_query_to_history(session_service, app_name, user_id, session_id, query):
    await update_interaction_history(
        session_service, app_name, user_id, session_id,
        {
            "role": "user",
            "message": query,
        }
    )


async def add_agent_response_to_history(session_service, app_name, user_id, session_id, agent_name, response_text):
    await update_interaction_history(
        session_service, app_name, user_id, session_id,
        {
            "role": "agent",
            "agent": agent_name,
            "message": response_text
        }
    )


async def add_tool_call_to_history(session_service, app_name, user_id, session_id, tool_name, input_data, output_data):
    await update_interaction_history(
        session_service, app_name, user_id, session_id,
        {
            "action": "tool_call",
            "tool": tool_name,
            "input": input_data,
            "output": output_data
        }
    )


async def process_agent_response(event):
    """
    Extracts and returns the final response text from an ADK agent event.

    Args:
        event: The ADK agent event object.

    Returns:
        str | None: The final text response from the agent, if available.
    """
    print(f"Event ID: {event.id}, Author: {event.author}")

    final_response = None

    # Check if the event contains parts with text
    if event.content and event.content.parts:
        for part in event.content.parts:
            if hasattr(part, "text") and part.text and not part.text.isspace():
                print(f"  Text: '{part.text.strip()}'")

    # Handle final response
    if event.is_final_response():
        if (
            event.content and
            event.content.parts and
            hasattr(event.content.parts[0], "text") and
            event.content.parts[0].text
        ):
            final_response = event.content.parts[0].text.strip()
            print(f"\nAgent Final Response: {final_response}\n")
        else:
            print("\nAgent Final Response: [No valid text content]\n")

    return final_response

async def call_agent_async(runner, user_id, session_id, query):
    """
    Asynchronously calls the ADK agent with the user query
    and updates session state with interaction history.
    """
    content = Content(role="user", parts=[Part(text=query)])
    final_response_text = None
    agent_name = None
    session = await runner.session_service.get_session(
        app_name=runner.app_name,
        user_id=user_id,
        session_id=session_id
    )
    messages = []

    history = session.state.get("interaction_history", [])
    for item in history:
        if item.get("role") in ["user", "agent"]:
            messages.append(Content(role=item["role"], parts=[Part(text=item["message"])]))

    # Add the current user query
    messages.append(Content(role="user", parts=[Part(text=query)]))


    try:
        async with AGENT_CALL_SEMAPHORE:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            ):
                if event.author:
                    agent_name = event.author

                response = await process_agent_response(event)
                if response:
                    final_response_text = response

    except Exception as e:
        print(f"Error during agent run: {e}")

    #  agent response to history
    if final_response_text and agent_name:
        await add_agent_response_to_history(
            session_service=runner.session_service,
            app_name=runner.app_name,
            user_id=user_id,
            session_id=session_id,
            agent_name=agent_name,
            response_text=final_response_text
        )


    return  final_response_text if final_response_text else "No response generated."
