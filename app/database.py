from fastapi import Depends
from pymongo import MongoClient
from pymongo.database import Database
import config

def get_database() -> Database:
    client = MongoClient(config.MONGO_URI)
    return client[config.MONGO_DB_NAME]

def get_collections(db: Database = Depends(get_database)) -> dict:
    """Get all required database collections."""
    return {
        "menu": db["menu"],
        "options": db["options"],
        "carts": db["carts"],
        "orders": db["orders"]
    }

# Create indexes for unique fields
def create_indexes(db: Database):
    db["menu"].create_index("name", unique=True)
    db["options"].create_index("name", unique=True)