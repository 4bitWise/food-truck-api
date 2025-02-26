import os
from dotenv import load_dotenv

load_dotenv()


PROJECT_NAME: str = "Food Truck API"
VERSION: str = "0.1.0"
PORT = int(os.getenv("PORT", 8000))
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
