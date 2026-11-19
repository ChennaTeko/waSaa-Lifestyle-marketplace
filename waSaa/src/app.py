
from pathlib import Path
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Import the class directly from personalisation.py
from src.personalisation import PersonalisedEngine

ROOT = Path(__file__).resolve().parents[1]
SERVICE_FILE = ROOT / "data" / "processed" / "yelp_services.csv"
EMBEDDINGS_FILE = ROOT / "data" / "processed" / "service_embeddings.npy"
MODEL_NAME = str(ROOT / "models" / "fine_tuned_search")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. DATA & MODEL INITIALIZATION ---
services_df = pd.read_csv(SERVICE_FILE).fillna("")
col_map = {}
for c in services_df.columns:
    col_clean = c.strip().lower()
    if col_clean in ["service_name", "name", "business_name"]:
        col_map[c] = "service_name"
    elif col_clean in ["area", "city", "location"]:
        col_map[c] = "area"
    elif col_clean in ["category", "categories", "tags"]:
        col_map[c] = "category"
    elif col_clean in ["nlp_text", "description", "text"]:
        col_map[c] = "nlp_text"

services_df = services_df.rename(columns=col_map)
services_df["search_text"] = (
    services_df["service_name"].astype(str) + ". " +
    services_df["category"].astype(str) + ". " +
    services_df["area"].astype(str) + ". " +
    services_df["nlp_text"].astype(str)
)

model = SentenceTransformer(MODEL_NAME)

if EMBEDDINGS_FILE.exists():
    service_embeddings = np.load(EMBEDDINGS_FILE)
else:
    print("⏳ Generating embeddings...")
    service_embeddings = model.encode(
        services_df["search_text"].tolist(),
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    np.save(EMBEDDINGS_FILE, service_embeddings)

# --- 2. INITIALIZE PERSONALIZATION ENGINE ---
personalised_engine = PersonalisedEngine(
    model=model,
    services_df=services_df,
    embeddings=service_embeddings
)

# --- 3. REST ENDPOINTS ---

@app.get("/api/meta")
def get_metadata():
    # FIXED: Group by whole categories instead of breaking "Beauty & Spa" into two strings
    unique_cats = sorted([str(c).strip() for c in services_df["category"].unique() if str(c).strip()])
    unique_areas = sorted([str(a).strip() for a in services_df["area"].unique() if str(a).strip()])
    return {
        "status": "success",
        "categories": unique_cats,
        "areas": unique_areas
    }

@app.get("/api/recommendations")
def get_recommendations(user_id: Optional[str] = "default_user", top_k: int = 6):
    """Fetches recommendations directly from PersonalisedEngine."""
    recs = personalised_engine.get_homepage_recommendations(user_id=user_id, top_k=top_k)
    return {"status": "success", "data": recs}

@app.get("/api/search")
def search_services(
    query: str = "top services",  # FIXED: Default fallbacks added to avoid crashing empty inputs
    category: Optional[str] = "",
    area: Optional[str] = "",
    user_id: Optional[str] = "default_user",
    top_k: int = 6
):
    # DYNAMIC LEARNING: Record search term into user's profile history
    full_context_query = f"{query} {category} {area}".strip()
    personalised_engine.record_interaction(user_id=user_id, query=full_context_query)

    query_embed = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    scores = cosine_similarity(query_embed, service_embeddings)[0]

    results = services_df.copy()
    results["score"] = scores

    # Soft score boosting for target filters (avoids returning 0 matches)
    if category and category.strip():
        cat_match = results["category"].str.contains(category, case=False, na=False)
        results.loc[cat_match, "score"] += 0.20

    if area and area.strip():
        area_match = results["area"].str.contains(area, case=False, na=False)
        results.loc[area_match, "score"] += 0.20

    top_results = results.sort_values("score", ascending=False).head(top_k)

    return {
        "status": "success",
        "data": [
            {
                "service_id": str(r.get("service_id", "")),
                "service_name": str(r["service_name"]),
                "category": str(r["category"]),
                "area": str(r["area"]),
                "score": float(r["score"])
            }
            for _, r in top_results.iterrows()
        ]
    }
# --- 4. AUTHENTICATION ENDPOINTS ---
from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

class OTPRequest(BaseModel):
    email: str
    phone: str

class VerifyOTPRequest(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    otp: str

class GoogleAuthRequest(BaseModel):
    token: str

@app.post("/api/auth/login")
def login(data: LoginRequest):
    # Mocking successful login. Replace with real verification database logic later.
    return {"status": "success", "user": {"email": data.email, "name": "Test User"}}

@app.post("/api/auth/request-otp")
def request_otp(data: OTPRequest):
    # Mocking OTP generation. Replace with Twilio/Email sending system later.
    return {"status": "success", "message": "OTP sent successfully"}

@app.post("/api/auth/verify-otp")
def verify_otp(data: VerifyOTPRequest):
    # Mocking OTP verification code '123456'
    if data.otp == "123456":
        return {"status": "success", "message": "Account created!"}
    return {"status": "error", "message": "Invalid OTP code"}



# Update your existing Google route to this:
@app.post("/api/auth/google")
def google_auth(data: GoogleAuthRequest):
    try:
        # Replace 'YOUR_GOOGLE_CLIENT_://googleusercontent.com' with your actual Client ID string
        CLIENT_ID = "489059479806-k1ajuj37bb0vl2nji25kgf4ueq5o2u9g.apps.googleusercontent.com" 
        
        # Verify and decode the secure token from Google
        idinfo = id_token.verify_oauth2_token(data.token, google_requests.Request(), CLIENT_ID)
        
        # Extract your real details!
        user_email = idinfo.get("email")
        user_name = idinfo.get("name")
        user_picture = idinfo.get("picture") # Optional profile picture URL
        
        return {
            "status": "success", 
            "user": {
                "email": user_email, 
                "name": user_name,
                "picture": user_picture
            }
        }
    except ValueError:
        # Invalid token
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid Google Token")



# FIXED: Shifted completely back to the left margin so python can execute Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=3000, reload=True)
