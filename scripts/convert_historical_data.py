import csv
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "historical" / "json"
OUTPUT_CSV_DIR = BASE_DIR / "data" / "historical" / "csv"
OUTPUT_CA_DIR = BASE_DIR / "data" / "historical" / "csv_ca"
OUTPUT_CSV_DIR_PATH = f"{BASE_DIR.name}/{OUTPUT_CSV_DIR.relative_to(BASE_DIR)}"
OUTPUT_CA_DIR_PATH = f"{BASE_DIR.name}/{OUTPUT_CA_DIR.relative_to(BASE_DIR)}"

def clear_output_dirs():
    for label, directory, directory_path in (
        ("Main", OUTPUT_CSV_DIR, OUTPUT_CSV_DIR_PATH),
        ("CA", OUTPUT_CA_DIR, OUTPUT_CA_DIR_PATH),
    ):
        if directory.exists():
            existing_files = list(directory.glob("*.csv"))
            for file_path in existing_files:
                file_path.unlink()
            print(f"{label} output directory exists : {directory_path}")
            print(f"Cleared {label.lower()} output directory")
        else:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created {label.lower()} output directory : {directory_path}")

def read_json(path):
    with open(path) as f:
        return json.load(f)

def parse_date(record):
    try:
        return datetime.strptime(record.get("mTIMESTAMP", ""), "%d-%b-%Y")
    except (ValueError, TypeError):
        return datetime.min

def collect_fieldnames(records, exclude=None):
    all_fieldnames = set()
    for record in records:
        all_fieldnames.update(record.keys())
    all_fieldnames.discard(exclude)
    return sorted(all_fieldnames)

def save_csv(data, path):
    if not data or "data" not in data or not data["data"]:
        return 0
    
    sorted_records = sorted(data["data"], key=parse_date)
    fieldnames = collect_fieldnames(sorted_records, exclude="CA")
    
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted_records)
    
    return len(sorted_records)

def save_ca_csv(data, path):
    if not data or "data" not in data or not data["data"]:
        return 0
    
    ca_records = []
    for record in data["data"]:
        if record.get("CA"):
            timestamp = record.get("mTIMESTAMP", "")
            for ca in record["CA"]:
                ca_records.append({"mTIMESTAMP": timestamp, **ca})
    
    if not ca_records:
        return 0
    
    fieldnames = collect_fieldnames(ca_records)
    
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ca_records)
    
    return len(ca_records)

def main():
    json_paths = sorted(INPUT_DIR.glob("*.json"))
    total = len(json_paths)
    width = len(str(total))
    
    clear_output_dirs()
    print(f"\nConverting {total} JSON files ...\n")
    
    success = 0
    ca_count = 0
    
    for i, json_path in enumerate(json_paths, start=1):
        symbol = json_path.stem
        label = f"[{i:0{width}}/{total}]  {symbol:<12}"
        
        try:
            data = read_json(json_path)
            rows = save_csv(data, OUTPUT_CSV_DIR / f"{symbol}.csv")
            ca_rows = save_ca_csv(data, OUTPUT_CA_DIR / f"{symbol}.csv")
            
            if ca_rows > 0:
                print(f"{label}->  {rows:>4} rows  ({ca_rows} CA)")
                ca_count += 1
            else:
                print(f"{label}->  {rows:>4} rows")
            success += 1
        except Exception:
            print(f"{label}->  ERROR")
    
    print()
    if ca_count > 0:
        print(f"Extracted corporate actions for {ca_count} symbols")
        print(f"Saved to : {OUTPUT_CA_DIR_PATH}")
        print()
    print(f"Converted {success}/{total} JSON files to CSV")
    print(f"Saved to : {OUTPUT_CSV_DIR_PATH}")

if __name__ == "__main__":
    main()
