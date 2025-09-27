from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from prompts import RECOMMENDATION_PROMPT, QA_PROMPT

load_dotenv()


class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name="gpt-4.1-nano",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )
    async def get_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
