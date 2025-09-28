from datetime import datetime
import types
from google.genai.types import Content, Part
from google.adk.sessions import InMemorySessionService
import asyncio
import traceback

AGENT_CALL_SEMAPHORE = asyncio.Semaphore(50)
MAX_HISTORY_ITEMS = 10


async def update_interaction_history(
    session_service,
    app_name,
    user_id,
    session_id,
    entry: dict = None,
    reservation_updates: dict = None,
):
    try:
        session = await session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )
        # print("reservation_updates:", reservation_updates)
        # print("event_updates:", event_updates)
        # print("photography_updates:", photography_updates)

        if not session:
            raise ValueError("Session not found.")

        history = session.state.get("interaction_history", {})
        print("Current interaction history:", history)
        if entry:
            agent_name = entry.pop("agent") or entry.pop("agent", None)
            print("agent_name:", agent_name)
            if agent_name:
                if agent_name not in history:
                    history[agent_name] = []
                history[agent_name].append(entry)

        # Get current state
        new_state = session.state.copy()
        # print("Current session state before update:", new_state)
        new_state["interaction_history"] = history
        print("Updated interaction history:", new_state["interaction_history"])

        # --- Reservation details ---
        if reservation_updates is not None:
            reservation_details = new_state.get("reservation_details", {})
            reservation_details.update(reservation_updates)
            new_state["reservation_details"] = reservation_details

        print(f"Updated session state: {new_state}")

        await session_service.create_session(
            app_name=app_name, user_id=user_id, session_id=session_id, state=new_state
        )

    except Exception as e:
        # Print the error message along with the traceback (including line number)
        print(f"[Utils Error] update_interaction_history failed: {e}")
        traceback.print_exc()


async def add_user_query_to_history(
    session_service,
    app_name,
    user_id,
    session_id,
    query,
    agent_name,
):
    await update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {
            "role": "user",
            "message": query,
            "agent": agent_name,
        },
    )


async def add_agent_response_to_history(
    session_service, app_name, user_id, session_id, agent_name, response_text
):
    await update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {"role": "agent", "agent": agent_name, "message": response_text},
    )


async def add_tool_call_to_history(
    session_service, app_name, user_id, session_id, tool_name, input_data, output_data
):
    await update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {
            "action": "tool_call",
            "tool": tool_name,
            "input": input_data,
            "output": output_data,
        },
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
            event.content
            and event.content.parts
            and hasattr(event.content.parts[0], "text")
            and event.content.parts[0].text
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
        app_name=runner.app_name, user_id=user_id, session_id=session_id
    )
    messages = []

    history = session.state.get("interaction_history", {})
    for agent, entries in history.items():
        for item in entries:
            if item.get("role") in ["user", "agent"]:
                messages.append(
                    Content(role=item["role"], parts=[Part(text=item["message"])])
                )

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
            response_text=final_response_text,
        )

    return final_response_text if final_response_text else "No response generated."
