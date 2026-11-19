from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient

app = FastAPI()

# Allow your HTML pages (Live Server, etc.) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. PASTE YOUR MONGODB CONNECTION STRING HERE
MONGO_URI = "mongodb+srv://wasaa_admin:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["wasaa_db"]
favorites_collection = db["favorites"]

# 2. Data format expected from the frontend
class FavoriteItem(BaseModel):
    userId: str
    itemId: str
    service_name: str = ""
    category: str = ""
    area: str = ""
    image: str = ""

# 3. Route to Add or Remove a favorite (called when clicking the heart)
@app.post("/api/favorites/toggle")
def toggle_favorite(item: FavoriteItem):
    existing = favorites_collection.find_one({
        "userId": item.userId,
        "itemId": item.itemId
    })

    if existing:
        favorites_collection.delete_one({"_id": existing["_id"]})
        return {"status": "removed", "itemId": item.itemId}
    else:
        favorites_collection.insert_one(item.dict())
        return {"status": "added", "itemId": item.itemId}

# 4. Route to Get all favorites for a user (called on favorites.html)
@app.get("/api/favorites/{user_id}")
def get_favorites(user_id: str):
    saved_items = list(favorites_collection.find({"userId": user_id}, {"_id": 0}))
    return saved_items