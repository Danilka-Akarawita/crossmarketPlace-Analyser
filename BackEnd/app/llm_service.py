from langchain_openai import ChatOpenAI
from typing import List
import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner

load_dotenv()


class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name="gpt-4.1-nano",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

    async def get_embedding(self, text: str) -> List[float]:
        """Generate vector embeddings for given text."""
        response = self.llm.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def create_base_agent(self, app_name: str, session_service):
        """Create the base LLM agent wrapped in a Runner."""
        model = LiteLlm(
            model_name="gpt-4.1-nano",
            temperature=0.3,
            openai_api_key="",
        )

        base_agent = LlmAgent(
            model=model,
            name="base_agent",
            description=(
                "Central coordinator that interprets user queries and manages "
                "the conversation flow across the session."
            ),
            instruction="You are a helpful assistant. Answer user queries clearly and concisely.",
        )

        runner = Runner(
            agent=base_agent,
            app_name=app_name,
            session_service=session_service,
        )

        return runner
