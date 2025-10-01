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


parser = PydanticOutputParser(pydantic_object=ProductSearchResult)


base_agent_instruction = """
Role: You are a helpful assistant provide accurate answers for laptop-related queries.

query: {user_query}
context: {context}
price_range: {price_range}
interaction_history: {interaction_history}
session_id:{session_id}
user_id:{user_id}
app_name:{app_name}

Instructions:
1.context contains tec spec summarization of laptops within the given price_range
2.If the context is not empty, use it to answer the user's query.
3.If the query mentioned about any price range, update the price_range using `search_products_tool`
4.Tailor the response based on the interaction_history, which includes previous user queries and agent responses.
5.Provide a concise answer to the user's query based on the context and interaction history.

step:
1. Analyze the user query and context.
2.If the price_range is an empty dict, it means the user has not specified any price range,strctly ask the user to specify a price range.
3.Invoke the `search_products_tool` to search for laptops within the specified price range and get the detailed laptop summary
4.Provide suitable recommendations or answers based on the context and interaction_history.

End Goal:
Provide a good customer care experience by understanding the user's needs and providing accurate, helpful responses.

Narrow:
1.Do not invoke the `search_products_tool` if the price_range is not empty or query does not mention about price range.
2.do not use any tone or style that is not professional and helpful.
3.Do not provide any information that is not related to the user's query or context.
4.Do not provide any answer if the query is not realted to laptops or any laptop accessories.
"""


class LLMService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        chat_model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-nano")
        embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

        self.llm = ChatOpenAI(
            model_name=chat_model,
            temperature=0.3,
            openai_api_key=api_key,
        )
        self.embedding_model = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=api_key,
        )
        self._api_key = api_key
        self._chat_model = chat_model

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

        prompt = f"""
        
        context: {text}
        Instructions
        Usually a laptop can be categorized as their intended purpose as bellow
        1. General/Everyday Laptop - Uses for basic computing tasks (web browsing, email, word processing, video streaming, and light multitasking). features a mid-range processor (e.g., Intel Core i3/i5 or equivalent AMD Ryzen), 8GB, and SSD storage.
        2. Office/Business Laptops - Professional work, presentations, data management, and secure remote access. Prioritizes reliability, robust security features (e.g., fingerprint readers, TPM chips), durable build quality, and often long battery life. features a mid-range to high-end processor (e.g., Intel Core i5/i7 or equivalent AMD Ryzen), 8GB or 16GB, and SSD storage.
        3. Gaming Laptops - Performance for gaming is the focus. Built for the latest, most graphically intensive titles. features a high-end processor (e.g., Intel Core i5/i7 or equivalent AMD Ryzen), 16GB or more ram, dedicated GPU (eg. GeForce RTX 3050 Laptop GPU, AMD Radeon RX 7000M Laptop GPU) and NvMe or SSD storage.

        Steps:
        1. Identify  the context given
        2. use the information in instruction to identify correct category/categories of the laptop
        3. provide a summarize based on the category and the context provided

        """
        print(f"prompt is {prompt}")
        response = self.llm.invoke(prompt)

        summary = response.content
        return summary

    def create_base_agent(self, app_name: str, session_service):
        """Create the base LLM agent wrapped in a Runner."""
        try:
            print("Creating base agent...", app_name)
            print(f"Session service: {session_service}")

            model = LiteLlm(
                model=self._chat_model,
                temperature=0.3,
                api_key=self._api_key,
            )

            base_agent = LlmAgent(
                model=model,
                name="base_agent",
                description=(
                    "Central coordinator that interprets user queries and manages "
                    "the conversation flow across the session."
                ),
                instruction=base_agent_instruction,
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
