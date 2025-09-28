from langchain_openai import ChatOpenAI, OpenAIEmbeddings
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
            openai_api_key="",
        )
        self.embedding_model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key="",
        )

    async def get_embedding(self, text: str) -> List[float]:
        """Generate vector embeddings for given text."""
        # langchain embeddings return a list directly
        return await self.embedding_model.aembed_query(text)

    async def summarize_text(self, text: str, max_tokens: int = 200) -> str:
        """
        Generate a concise summary of the given text using the LLM.

        Args:
            text: The input string to summarize.
            max_tokens: Approximate maximum length of the summary.
        Returns:
            A string containing the summary.
        """

        # If text is very long, you might want to truncate or chunk it
        prompt = (
            "Please provide a concise summary of the following content:\n\n"
            f"{text}\n\nSummary:"
        )
        print(f"prompt is {prompt}")
        response = self.llm.invoke(prompt)
        # agenerate returns a list of generations, pick the first one
        summary = response.content
        return summary

    def create_base_agent(self, app_name: str, session_service):
        """Create the base LLM agent wrapped in a Runner."""
        try:
            model = LiteLlm(
                model="gpt-4.1-nano",
                temperature=0.3,
                api_key="",
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
            print("Base agent created successfully.")

            return runner
        except Exception as e:
            print(f"Error creating base agent: {e}")
            return None
