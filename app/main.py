from fastapi import FastAPI
import uvicorn
import config
from database import get_database
from routes import menu
from routes import options

app = FastAPI()

# app.include_router(menu_routes.router, prefix="/api")

app.include_router(menu.router, prefix="/menu", tags=["Menu"])
app.include_router(options.router, prefix="/options", tags=["Options"])

# Test de connexion à MongoDB
@app.get("/db-status")
async def db_status():
    db = get_database()
    try:
        # Vérifie la connexion en listant les collections
        collections = db.list_collection_names()
        return {"status": "Connected", "collections": collections}
    except Exception as e:
        return {"status": "Error", "message": str(e)}


@app.get("/")
async def root():
    return {"message": "Bienvenue sur l'API du Food Truck!"}

if __name__ == "__main__":
    uvicorn.run("main:app", port=config.PORT, reload=True)
