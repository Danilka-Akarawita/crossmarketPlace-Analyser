import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

class MongoDB:
    def __init__(self):
        self.client = None
        self.database = None

    
    async def connect(self):
        """Connect to MongoDB Atlas"""
        MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://nishandanilka_db_user:ITZ6uWjjI43UQxqw@cluster0.9mqmldc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
        DB_NAME = os.getenv("DB_NAME", "cross-marketplace")
        
        self.client = AsyncIOMotorClient(MONGODB_URL)
        self.database = self.client[DB_NAME]
        
        # Create indexes
        await self.database.products.create_index("sku", unique=True)
        await self.database.products.create_index("brand")
        await self.database.products.create_index("current_price")
        await self.database.products.create_index("average_rating")
        
        print("Connected to MongoDB successfully")
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()

# Database instance
mongodb = MongoDB()

if __name__ == "__main__":
    async def test():
        await mongodb.connect()   # connect and create indexes
        await mongodb.disconnect()  # close connection

    asyncio.run(test())