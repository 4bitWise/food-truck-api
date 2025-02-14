import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Food Truck API"
    VERSION: str = "0.1.0"
    ATLAS_URI: str = os.getenv("ATLAS_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "food_truck")

