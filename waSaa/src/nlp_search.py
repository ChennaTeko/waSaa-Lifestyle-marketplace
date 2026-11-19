import os
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import standalone authentication router
from .auth import auth_router
# Import your intelligent search engine from your search script
from .search import NLPSearchEngine  # Adjust path if search.py is in another folder

app = FastAPI(title="waSaa Lifestyle API")

# Enable CORS for frontend client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount standalone Auth Router (/api/auth/signup, /api/auth/login, etc.)
app.include_router(auth_router)

# ============================================================================
# Intelligent ML Engine Initialization
# ============================================================================
# Instantiating the engine loads your fine-tuned model and real yelp_services.csv
search_engine = NLPSearchEngine()

# ============================================================================
# Metadata, Search & Recommendation Endpoints
# ============================================================================

@app.get("/api/meta")
def get_metadata():
    """Returns dynamic categories and area dropdown options from the real dataset."""
    categories = sorted(search_engine.services["category"].unique().tolist())
    areas = sorted(search_engine.services["area"].unique().tolist())
    return {
        "categories": categories,
        "areas": areas
    }

@app.get("/api/recommendations")
def get_recommendations(user_id: Optional[str] = "default_user", top_k: int = 18):
    """Returns top recommendation feed items pulled directly from real data."""
    # Return head items safely converted into records from the engine's dataframe
    results = search_engine.services.head(top_k).to_dict(orient="records")
    return {"status": "success", "data": results}

@app.get("/api/search")
def search_services(
    query: str = "top services",
    category: Optional[str] = "",
    area: Optional[str] = "",
    user_id: Optional[str] = "default_user",
    top_k: int = 24
):
    """Executes search utilizing your fine-tuned intelligent sentence transformer model."""
    # Directly leverage the search function inside your NLPSearchEngine class
    search_results = search_engine.search(
        query=query,
        target_category=category or "",
        location_constraint=area or "",
        top_k=top_k
    )
    
    return {
        "status": "success",
        "data": search_results
    }

if __name__ == "__main__":
    import uvicorn
    # Move the backend API to port 8000 to keep it isolated from the frontend web server
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

