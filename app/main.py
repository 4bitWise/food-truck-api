import uvicorn
import routes.menu as menu

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import AtlasClient
from config import Settings

global app

# Creating a little mongo atlas client and testing the connection
atlas_client = AtlasClient.get_instance(
    atlas_uri=Settings.ATLAS_URI,
    dbname=Settings.DB_NAME
)
atlas_client.ping()
print('Connected to Atlas instance! We are good to go!')

def create_app():
    app = FastAPI(title="Food Truck API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(menu.router, prefix="/menu", tags=["Menu"])

    @app.get("/")
    async def root():
        return {"message": "Bienvenue sur l'API du Food Truck!"}

    return app

app = create_app()

if __name__ == "__main__":
   
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
