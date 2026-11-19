
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

YELP_DIR = ROOT / "data" / "raw" / "yelp"
BUSINESS_FILE = YELP_DIR / "yelp_academic_dataset_business.json"
OUTPUT_DIR = ROOT / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Categories worth investigating for WaSaa.
RELEVANT_TERMS = [
    "beauty", "hair", "salon", "barber", "spa",
    "health", "medical", "dentist", "fitness",
    "home services", "cleaning", "plumbing",
    "electrician", "moving", "transportation",
    "automotive", "tutoring", "education",
    "child care", "photograph"
]


def main():
    if not BUSINESS_FILE.exists():
        raise FileNotFoundError(
            f"Yelp business file not found:\n{BUSINESS_FILE}"
        )

    total = 0
    missing_categories = 0
    category_counts = Counter()
    city_counts = Counter()
    relevant_samples = []

    with BUSINESS_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            try:
                business = json.loads(line)
            except json.JSONDecodeError:
                continue

            total += 1

            name = business.get("name") or ""
            categories = business.get("categories") or ""
            city = business.get("city") or ""
            state = business.get("state") or ""

            if not categories:
                missing_categories += 1
                continue

            category_list = [
                category.strip()
                for category in categories.split(",")
                if category.strip()
            ]

            category_counts.update(category_list)

            if city:
                city_counts[city] += 1

            categories_lower = categories.lower()

            if any(term in categories_lower for term in RELEVANT_TERMS):
                if len(relevant_samples) < 1000:
                    relevant_samples.append({
                        "business_id": business.get("business_id"),
                        "name": name,
                        "categories": categories,
                        "city": city,
                        "state": state,
                        "stars": business.get("stars"),
                        "review_count": business.get("review_count"),
                        "source": "yelp",
                    })

    # Save a small sample for examination, not model training.
    import csv

    sample_path = OUTPUT_DIR / "yelp_business_sample.csv"

    columns = [
        "business_id", "name", "categories", "city",
        "state", "stars", "review_count", "source"
    ]

    with sample_path.open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(relevant_samples)

    report_path = OUTPUT_DIR / "yelp_inspection_report.txt"

    with report_path.open("w", encoding="utf-8") as report:
        report.write(f"Businesses read: {total}\n")
        report.write(f"Missing categories: {missing_categories}\n")
        report.write(f"Potentially relevant records sampled: "
                     f"{len(relevant_samples)}\n\n")

        report.write("TOP 30 CATEGORIES\n")
        for category, count in category_counts.most_common(30):
            report.write(f"{category}: {count}\n")

        report.write("\nTOP 20 CITIES\n")
        for city, count in city_counts.most_common(20):
            report.write(f"{city}: {count}\n")

    print(f"Businesses read: {total:,}")
    print(f"Missing categories: {missing_categories:,}")
    print(f"Relevant sample: {len(relevant_samples):,}")
    print(f"\nSaved sample: {sample_path}")
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
