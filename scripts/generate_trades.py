import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SIGNALS_DIR = BASE_DIR / "data" / "calculated" / "signals"
HISTORICAL_DIR = BASE_DIR / "data" / "nse" / "csv_transformed"
SPREADS_DIR = BASE_DIR / "data" / "calculated" / "price_spreads"
OUTPUT_DIR = BASE_DIR / "data" / "calculated" / "trades"
OUTPUT_DIR_PATH = f"{BASE_DIR.name}/{OUTPUT_DIR.relative_to(BASE_DIR)}"

OUTPUT_FIELDNAMES = [
    "date", "close", "vwap", "abs_close-vwap", "pct_close-vwap", "next_day_open",
    "buy_price", "sell_price", "abs_pnl", "pct_pnl",
]

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

def read_signals(signals_path):
    labels_by_date = {}
    if not signals_path.exists():
        return labels_by_date
    with open(signals_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            labels_by_date[row.get("date", "")] = {
                "label_ca": row.get("label_ca", "") == "True",
                "label_trade": row.get("label_trade", "") == "True",
            }
    return labels_by_date

def read_spreads(spreads_path):
    spreads_by_date = {}
    if not spreads_path.exists():
        return spreads_by_date
    with open(spreads_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            spreads_by_date[row.get("date", "")] = {
                "abs_close-vwap": row.get("abs_close-vwap", ""),
                "pct_close-vwap": row.get("pct_close-vwap", ""),
            }
    return spreads_by_date

def generate_trades(historical_path, signals_path, spreads_path, output_path):
    labels_by_date = read_signals(signals_path)
    spreads_by_date = read_spreads(spreads_path)
    
    with open(historical_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    output_rows = []
    for i in range(len(rows) - 1):
        row, next_row = rows[i], rows[i + 1]
        date, next_date = row.get("date", ""), next_row.get("date", "")
        
        if labels_by_date.get(next_date, {}).get("label_ca"):
            continue
        if not labels_by_date.get(date, {}).get("label_trade"):
            continue
        
        try:
            close = float(row["close"])
            vwap = float(row["vwap"])
            next_day_open = float(next_row["open"])
            buy_price = close
            sell_price = next_day_open
        except (KeyError, ValueError):
            continue
        
        abs_pnl = sell_price - buy_price
        pct_pnl = (abs_pnl / buy_price * 100) if buy_price != 0 else ""
        
        spread = spreads_by_date.get(date, {})
        output_rows.append({
            "date": date,
            "close": close,
            "vwap": vwap,
            "abs_close-vwap": spread.get("abs_close-vwap", ""),
            "pct_close-vwap": spread.get("pct_close-vwap", ""),
            "next_day_open": next_day_open,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "abs_pnl": round(abs_pnl, 4),
            "pct_pnl": round(pct_pnl, 4) if pct_pnl != "" else "",
        })
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(output_rows)
    
    return len(output_rows)

def main():
    csv_paths = sorted(HISTORICAL_DIR.glob("*.csv"))
    total = len(csv_paths)
    width = len(str(total))
    
    clear_output_dir()
    print(f"\nGenerating trades for {total} CSV files ...\n")
    
    success = 0
    
    for i, historical_path in enumerate(csv_paths, start=1):
        symbol = historical_path.stem
        label = f"[{i:0{width}}/{total}]  {symbol:<12}"
        signals_path = SIGNALS_DIR / f"{symbol}.csv"
        spreads_path = SPREADS_DIR / f"{symbol}.csv"
        output_path = OUTPUT_DIR / f"{symbol}.csv"
        
        try:
            rows = generate_trades(historical_path, signals_path, spreads_path, output_path)
            print(f"{label}->  {rows:>4} rows")
            success += 1
        except Exception:
            print(f"{label}->  ERROR")
    
    print()
    print(f"Processed {success}/{total} CSV files")
    print(f"Saved to : {OUTPUT_DIR_PATH}")

if __name__ == "__main__":
    main()
