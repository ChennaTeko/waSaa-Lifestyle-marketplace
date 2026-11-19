from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
SERVICE_FILE = ROOT / "data" / "processed" / "nlp_ready.csv"
TRAIN_FILE = ROOT / "data" / "raw" / "train_pairs.csv"

# Make sure the folder exists
TRAIN_FILE.parent.mkdir(parents=True, exist_ok=True)

if SERVICE_FILE.exists():
    df = pd.read_csv(SERVICE_FILE)
    
    train_data = []
    for _, row in df.iterrows():
        # Pair 1: Query variation mapping to service
        train_data.append({
            "query_text": f"looking for {str(row['service_name']).lower()}",
            "service_name": row['service_name'],
            "nlp_text": row['nlp_text']
        })
        # Pair 2: Category and location mapping to service
        train_data.append({
            "query_text": f"{str(row['category']).lower()} services in {row['area']}",
            "service_name": row['service_name'],
            "nlp_text": row['nlp_text']
        })

    train_df = pd.DataFrame(train_data)
    train_df.to_csv(TRAIN_FILE, index=False)
    print(f"✅ Success! Generated {len(train_df)} training pairs at: {TRAIN_FILE}")
else:
    print(f"❌ Error: Could not find {SERVICE_FILE}. Check your data folder structure.")
