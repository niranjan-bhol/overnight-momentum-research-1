import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TRADES_DIR = BASE_DIR / "data" / "calculated" / "trades"
OUTPUT_DIR = BASE_DIR / "data" / "result"
OUTPUT_PATH = OUTPUT_DIR / "summary.csv"
OUTPUT_PATH_STR = f"{BASE_DIR.name}/{OUTPUT_PATH.relative_to(BASE_DIR)}"

OUTPUT_FIELDNAMES = ["symbol", "trade_count", "abs_pnl", "pct_pnl"]

def summarize_trades(trades_path):
    trade_count = 0
    abs_pnl_total = 0.0
    pct_pnl_total = 0.0
    
    with open(trades_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("date"):
                continue
            trade_count += 1
            try:
                abs_pnl_total += float(row["abs_pnl"])
            except (KeyError, ValueError):
                pass
            try:
                pct_pnl_total += float(row["pct_pnl"])
            except (KeyError, ValueError):
                pass
    
    return trade_count, round(abs_pnl_total, 4), round(pct_pnl_total, 4)

def main():
    csv_paths = sorted(TRADES_DIR.glob("*.csv"))
    total = len(csv_paths)
    width = len(str(total))
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nGenerating summary for {total} CSV files ...\n")
    
    output_rows = []
    success = 0
    
    for i, trades_path in enumerate(csv_paths, start=1):
        symbol = trades_path.stem
        label = f"[{i:0{width}}/{total}]  {symbol:<12}"
        
        try:
            trade_count, abs_pnl_total, pct_pnl_total = summarize_trades(trades_path)
            output_rows.append({
                "symbol": symbol,
                "trade_count": trade_count,
                "abs_pnl": abs_pnl_total,
                "pct_pnl": pct_pnl_total,
            })
            print(f"{label}->  {trade_count:>4} trades")
            success += 1
        except Exception:
            print(f"{label}->  ERROR")
    
    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(output_rows)
    
    print()
    print(f"Processed {success}/{total} CSV files")
    print(f"Saved to : {OUTPUT_PATH_STR}")

if __name__ == "__main__":
    main()
