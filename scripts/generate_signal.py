import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "historical" / "csv_transformed"
CA_DIR = BASE_DIR / "data" / "historical" / "csv_ca_transformed"
SPREADS_DIR = BASE_DIR / "data" / "calculated" / "price_spreads"
OUTPUT_DIR = BASE_DIR / "data" / "calculated" / "signals"
OUTPUT_DIR_PATH = f"{BASE_DIR.name}/{OUTPUT_DIR.relative_to(BASE_DIR)}"

OUTPUT_FIELDNAMES = ["date", "label_ca", "label_trade"]

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

def read_ca_dates(ca_path):
    ex_dates = set()
    if not ca_path.exists():
        return ex_dates
    with open(ca_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ex_date = row.get("ex_date", "")
            if ex_date:
                ex_dates.add(ex_date)
    return ex_dates

def read_close_vwap(spreads_path):
    close_vwap_by_date = {}
    if not spreads_path.exists():
        return close_vwap_by_date
    with open(spreads_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row.get("date", "")
            value = row.get("abs_close-vwap", "")
            try:
                close_vwap_by_date[date] = float(value)
            except ValueError:
                close_vwap_by_date[date] = None
    return close_vwap_by_date

def generate_signal(input_path, ca_path, spreads_path, output_path):
    ex_dates = read_ca_dates(ca_path)
    close_vwap_by_date = read_close_vwap(spreads_path)
    
    with open(input_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            date = row.get("date", "")
            label_ca = date in ex_dates
            close_vwap = close_vwap_by_date.get(date)
            label_trade = close_vwap is not None and close_vwap > 0
            writer.writerow({
                "date": date,
                "label_ca": label_ca,
                "label_trade": label_trade,
            })
    
    return len(rows)

def main():
    csv_paths = sorted(INPUT_DIR.glob("*.csv"))
    total = len(csv_paths)
    width = len(str(total))
    
    clear_output_dir()
    print(f"\nGenerating signals for {total} CSV files ...\n")
    
    success = 0
    
    for i, input_path in enumerate(csv_paths, start=1):
        symbol = input_path.stem
        label = f"[{i:0{width}}/{total}]  {symbol:<12}"
        ca_path = CA_DIR / f"{symbol}.csv"
        spreads_path = SPREADS_DIR / f"{symbol}.csv"
        output_path = OUTPUT_DIR / f"{symbol}.csv"
        
        try:
            rows = generate_signal(input_path, ca_path, spreads_path, output_path)
            print(f"{label}->  {rows:>4} rows")
            success += 1
        except Exception:
            print(f"{label}->  ERROR")
    
    print()
    print(f"Processed {success}/{total} CSV files")
    print(f"Saved to : {OUTPUT_DIR_PATH}")

if __name__ == "__main__":
    main()
