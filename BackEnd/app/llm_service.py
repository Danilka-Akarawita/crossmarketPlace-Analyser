from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from typing import List
import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from tools.search_products_tools import search_products_tool
from langchain.output_parsers import PydanticOutputParser
load_dotenv()
from typing import List, Optional
from pydantic import BaseModel

class ProductSearchResult(BaseModel):
    answer: str
    quick_questions: List[str]
    products: Optional[List[dict]] = None  

parser= PydanticOutputParser(pydantic_object=ProductSearchResult)


prompttt="""

query: {user_query}

You are a helpful shopping assistant.

When the user asks about buying or comparing products,
-extract query, min_price, max_price from the user query if available.
- call the tool `search_products_tool` with query, min_price, max_price} to get product data.
- use the tool's "products" list to give product recommendations.
- use the tool's response  string to give a concise natural-language answer.
Always respond as :
{
  "answer": "<your helpful explanation>",
  "quick_questions": ["<next thing they might ask>", "..."],
  "products": [ ... ]  // from the tool when relevant
}


"""
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
            print("Creating base agent...", app_name)
            print(f"Session service: {session_service}")
            
            
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
                instruction=prompttt,
                tools=[search_products_tool],
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
