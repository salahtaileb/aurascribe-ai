# tools/import_mappings.py
import csv, json, sys
from typing import List

def parse_keywords(field: str):
    if not field:
        return []
    return [k.strip() for k in field.split(';') if k.strip()]

def convert(csv_path: str):
    out = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            out.append({
                "key": row.get("key"),
                "label": {"fr": row.get("label_fr",""), "en": row.get("label_en","")},
                "icd10ca": row.get("icd10ca",""),
                "ccp": row.get("ccp",""),
                "keywords": {"fr": parse_keywords(row.get("keywords_fr","")), "en": parse_keywords(row.get("keywords_en",""))}
            })
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/import_mappings.py path/to/mappings.csv", file=sys.stderr)
        sys.exit(2)
    convert(sys.argv[1])