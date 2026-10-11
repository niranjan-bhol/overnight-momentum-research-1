import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "historical" / "csv_transformed"
OUTPUT_DIR = BASE_DIR / "data" / "calculated" / "price_spreads"
OUTPUT_DIR_PATH = f"{BASE_DIR.name}/{OUTPUT_DIR.relative_to(BASE_DIR)}"

PAIRS = [
    ("close", "open"),
    ("high", "low"),
    ("high", "open"),
    ("high", "close"),
    ("open", "low"),
    ("close", "low"),
    ("open", "vwap"),
    ("close", "vwap"),
]

ABS_FIELDNAMES = [f"abs_{a}-{b}" for a, b in PAIRS]
PCT_FIELDNAMES = [f"pct_{a}-{b}" for a, b in PAIRS]
OUTPUT_FIELDNAMES = ["date", *ABS_FIELDNAMES, *PCT_FIELDNAMES]

def clear_output_dir():
    if OUTPUT_DIR.exists():
        existing_files = list(OUTPUT_DIR.glob("*.csv"))
        for file_path in existing_files:
            file_path.unlink()
        print(f"Output directory exists : {OUTPUT_DIR_PATH}")
        print(f"\nCleared output directory")
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created output directory : {OUTPUT_DIR_PATH}")

def calculate_row(row):
    values = {}
    for field in ("open", "high", "low", "close", "vwap"):
        try:
            values[field] = float(row[field])
        except (KeyError, ValueError):
            values[field] = None
    
    result = {"date": row.get("date", "")}
    
    for a, b in PAIRS:
        va, vb = values.get(a), values.get(b)
        if va is None or vb is None:
            diff, pct = "", ""
        else:
            diff = va - vb
            pct = (diff / vb * 100) if vb != 0 else ""
        
        result[f"abs_{a}-{b}"] = round(diff, 4) if diff != "" else ""
        result[f"pct_{a}-{b}"] = round(pct, 4) if pct != "" else ""
    
    return result

def calculate_csv(input_path, output_path):
    with open(input_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = [calculate_row(row) for row in reader]
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    
    return len(rows)

def main():
    csv_paths = sorted(INPUT_DIR.glob("*.csv"))
    total = len(csv_paths)
    width = len(str(total))
    
    clear_output_dir()
    print(f"\nCalculating spreads for {total} CSV files ...\n")
    
    success = 0
    
    for i, csv_path in enumerate(csv_paths, start=1):
        symbol = csv_path.stem
        label = f"[{i:0{width}}/{total}]  {symbol:<12}"
        
        try:
            rows = calculate_csv(csv_path, OUTPUT_DIR / f"{symbol}.csv")
            print(f"{label}->  {rows:>4} rows")
            success += 1
        except Exception:
            print(f"{label}->  ERROR")
    
    print()
    print(f"Processed {success}/{total} CSV files")
    print(f"Saved to : {OUTPUT_DIR_PATH}")

if __name__ == "__main__":
    main()
