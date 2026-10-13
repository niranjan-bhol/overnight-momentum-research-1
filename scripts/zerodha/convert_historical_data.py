import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
INPUT_DIR = BASE_DIR / "data" / "zerodha" / "historical" / "json"
OUTPUT_DIR = BASE_DIR / "data" / "zerodha" / "historical" / "csv"
OUTPUT_DIR_PATH = f"{BASE_DIR.name}/{OUTPUT_DIR.relative_to(BASE_DIR)}"

CSV_HEADER = ["timestamp", "open", "high", "low", "close", "volume", "open_interest"]

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

def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_csv(data, path):
    candles = data.get("data", {}).get("candles", [])
    
    if not candles:
        return 0
    
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)
        writer.writerows(candles)
    
    return len(candles)

def main():
    json_paths = sorted(INPUT_DIR.glob("*.json"))
    total = len(json_paths)
    width = len(str(total))
    
    clear_output_dir()
    print(f"\nConverting {total} JSON files ...\n")
    
    success = 0
    
    for i, json_path in enumerate(json_paths, start=1):
        symbol = json_path.stem
        label = f"[{i:0{width}}/{total}]  {symbol:<12}"
        
        try:
            data = read_json(json_path)
            rows = save_csv(data, OUTPUT_DIR / f"{symbol}.csv")
            print(f"{label}->  {rows:>4} rows")
            success += 1
        except Exception:
            print(f"{label}->  ERROR")
    
    print()
    print(f"Converted {success}/{total} JSON files to CSV")
    print(f"Saved to : {OUTPUT_DIR_PATH}")

if __name__ == "__main__":
    main()
