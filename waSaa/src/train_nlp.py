from pathlib import Path
import pandas as pd
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader


SRC_DIR = Path(__file__).resolve().parent
ROOT = SRC_DIR.parent
TRAIN_FILE = ROOT / "data" / "raw" / "train_pairs.csv"
OUTPUT_DIR = ROOT / "models" / "fine_tuned_search"


def train_model():
    print("🤖 Loading pretrained base model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    if not TRAIN_FILE.exists():
        raise FileNotFoundError(f"Missing training file at: {TRAIN_FILE}")
        
    df = pd.read_csv(TRAIN_FILE)
    
    print("📦 Formatting training dataset...")
    train_examples = []
    for _, row in df.iterrows():
        query = str(row['query_text']).strip()
        service_context = f"{row['service_name']}. {row['nlp_text']}".strip()
        train_examples.append(InputExample(texts=[query, service_context]))
        
    # DataLoader manages feeding pairs into the model in small groups
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
    
    # Loss function optimizes weights so matches have high cosine similarity scores
    train_loss = losses.MultipleNegativesRankingLoss(model=model)
    
    print(f"🚀 Starting training loop with {len(train_examples)} examples...")
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=3, 
        warmup_steps=10,
        output_path=str(OUTPUT_DIR),
        show_progress_bar=True
    )
    print(f"🎉 Success! Fine-tuned model saved locally to: {OUTPUT_DIR}")

if __name__ == "__main__":
    train_model()

