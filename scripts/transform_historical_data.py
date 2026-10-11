import csv
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "historical" / "csv"
OUTPUT_DIR = BASE_DIR / "data" / "historical" / "csv_transformed"
OUTPUT_DIR_PATH = f"{BASE_DIR.name}/{OUTPUT_DIR.relative_to(BASE_DIR)}"

DATE_FORMAT = "%d-%b-%Y"

COLUMN_MAP = {
    "date": "mTIMESTAMP",
    "open": "CH_OPENING_PRICE",
    "high": "CH_TRADE_HIGH_PRICE",
    "low": "CH_TRADE_LOW_PRICE",
    "close": "CH_CLOSING_PRICE",
    "vwap": "VWAP",
    "last_price": "CH_LAST_TRADED_PRICE",
    "prev_close": "CH_PREVIOUS_CLS_PRICE",
    "total_trades": "CH_TOTAL_TRADES",
    "total_traded_qty": "CH_TOT_TRADED_QTY",
    "total_traded_val": "CH_TOT_TRADED_VAL",
    "delivered_qty": "COP_DELIV_QTY",
    "delivery_pct": "COP_DELIV_PERC",
}

OUTPUT_FIELDNAMES = list(COLUMN_MAP.keys())

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

def transform_row(row):
    result = {new_col: row.get(old_col, "") for new_col, old_col in COLUMN_MAP.items()}
    if result["date"]:
        result["date"] = datetime.strptime(result["date"], DATE_FORMAT).strftime("%Y-%m-%d")
    return result

def transform_csv(input_path, output_path):
    with open(input_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = [transform_row(row) for row in reader]
    
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
    print(f"\nTransforming {total} CSV files ...\n")
    
    success = 0
    
    for i, csv_path in enumerate(csv_paths, start=1):
        symbol = csv_path.stem
        label = f"[{i:0{width}}/{total}]  {symbol:<12}"
        
        try:
            rows = transform_csv(csv_path, OUTPUT_DIR / f"{symbol}.csv")
            print(f"{label}->  {rows:>4} rows")
            success += 1
        except Exception:
            print(f"{label}->  ERROR")
    
    print()
    print(f"Transformed {success}/{total} CSV files")
    print(f"Saved to : {OUTPUT_DIR_PATH}")

if __name__ == "__main__":
    main()
