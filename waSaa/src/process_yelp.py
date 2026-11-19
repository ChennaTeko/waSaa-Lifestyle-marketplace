from pathlib import Path
import pandas as pd
import json


SRC_DIR = Path(__file__).resolve().parent
ROOT = SRC_DIR.parent
YELP_JSON_PATH = ROOT / "data" / "raw" / "yelp" / "yelp_academic_dataset_business.json"
OUTPUT_CSV_PATH = ROOT / "data" / "processed" / "yelp_services.csv"


def convert_yelp_data(limit=5000):
    print("⏳ Parsing Yelp business records...")
    records = []
    
    with open(YELP_JSON_PATH, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            data = json.loads(line)
            
            # Map Yelp's layout directly into your search engine architecture
            records.append({
                "service_id": i,
                "service_name": data.get("name", ""),
                "category": data.get("categories", ""),
                "area": data.get("city", ""),
                "nlp_text": f"Located at {data.get('address', '')}. Has {data.get('review_count', 0)} reviews with a star rating of {data.get('stars', 0)}."
            })
            
    yelp_df = pd.DataFrame(records)
    # Filter out empty entries
    yelp_df = yelp_df.dropna(subset=["service_name", "category"])
    
    OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    yelp_df.to_csv(OUTPUT_CSV_PATH, index=False)
    print(f"✅ Successfully extracted {len(yelp_df)} Yelp businesses to: {OUTPUT_CSV_PATH}")

if __name__ == "__main__":
    convert_yelp_data()
