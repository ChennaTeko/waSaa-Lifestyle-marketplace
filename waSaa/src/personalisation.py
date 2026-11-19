from pathlib import Path
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

SRC_DIR = Path(__file__).resolve().parent
ROOT = SRC_DIR.parent
SERVICE_FILE = ROOT / "data" / "processed" / "yelp_services.csv"
MODEL_PATH = ROOT / "models" / "fine_tuned_search"

class PersonalisedEngine:
    def __init__(self, model=None, services_df=None, embeddings=None):
        """Reuses model and embeddings loaded at app startup to save memory and execution time."""
        self.model = model if model else SentenceTransformer(str(MODEL_PATH))
        
        if services_df is not None:
            self.services = services_df
        else:
            self.services = pd.read_csv(SERVICE_FILE).fillna("")
            self.services["search_text"] = (
                self.services["service_name"] + ". " +
                self.services["category"] + ". " +
                self.services["area"] + ". " +
                self.services["nlp_text"]
            )

        if embeddings is not None:
            self.service_embeddings = embeddings
        else:
            self.service_embeddings = self.model.encode(
                self.services["search_text"].tolist(),
                convert_to_numpy=True,
                normalize_embeddings=True
            )

        # Dynamic user click and search interaction store
        self.user_histories = {}

    def get_user_history(self, user_id: str):
        """Returns or initializes default interest seeds for a user."""
        if user_id not in self.user_histories:
            self.user_histories[user_id] = [
                "Urgent care and medical centers in Tampa",
                "Family doctors and general clinics"
            ]
        return self.user_histories[user_id]

    def record_interaction(self, user_id: str, query: str):
        """Appends new user searches or clicks to adapt their profile dynamically."""
        if not query or not query.strip():
            return
        
        history = self.get_user_history(user_id)
        history.append(query.strip())
        
        # Keep sliding memory window to the last 10 interactions
        if len(history) > 10:
            history.pop(0)

    def get_homepage_recommendations(self, user_id: str = "default_user", top_k: int = 6):
        """Generates dynamic homepage feed using the averaged profile vector."""
        history = self.get_user_history(user_id)
        
        # 1. Encode user interaction history
        history_embeddings = self.model.encode(
            history,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        # 2. Build aggregate user profile vector (averaging recent taste vectors)
        user_profile_vector = np.mean(history_embeddings, axis=0).reshape(1, -1)

        # 3. Compute cosine similarity against all service embeddings
        scores = cosine_similarity(user_profile_vector, self.service_embeddings)[0]

        recommendations = self.services.copy()
        recommendations["taste_match_score"] = scores

        top_recs = recommendations.sort_values("taste_match_score", ascending=False).head(top_k)

        return [
            {
                "service_id": str(r.get("service_id", "")),
                "service_name": str(r["service_name"]),
                "category": str(r["category"]),
                "area": str(r["area"]),
                "score": float(r["taste_match_score"])
            }
            for _, r in top_recs.iterrows()
        ]