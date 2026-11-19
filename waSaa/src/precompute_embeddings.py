from pathlib import Path
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[1]
SERVICE_FILE = ROOT / "data" / "processed" / "yelp_services.csv"
MODEL_NAME = str(ROOT / "models" / "fine_tuned_search")
EMBEDDINGS_FILE = ROOT / "data" / "processed" / "service_embeddings.npy"

print("⏳ Loading model & generating embeddings (one-time process)...")
services = pd.read_csv(SERVICE_FILE).fillna("")

search_text = (
    services["service_name"] + ". " +
    services["category"] + ". " +
    services["area"] + ". " +
    services["nlp_text"]
).tolist()

model = SentenceTransformer(MODEL_NAME)
embeddings = model.encode(search_text, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=True)

np.save(EMBEDDINGS_FILE, embeddings)
print(f"✅ Saved precomputed embeddings to: {EMBEDDINGS_FILE}")
