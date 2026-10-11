import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SYMBOL_DIR = BASE_DIR / "data" / "symbol"
TRADES_DIR = BASE_DIR / "data" / "calculated" / "trades"
OUTPUT_DIR = BASE_DIR / "data" / "result" / "summary" / "by_index"

OUTPUT_FIELDNAMES = ["symbol", "trade_count", "abs_pnl", "pct_pnl"]

def read_index_symbols(index_path):
    with open(index_path) as f:
        return [line.strip() for line in f if line.strip()]

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

def generate_summary_for_index(index_path):
    index_name = index_path.stem
    symbols = read_index_symbols(index_path)
    total = len(symbols)
    width = len(str(total))
    
    print(f"\nGenerating summary for {index_name} ({total} symbols) ...\n")
    
    output_rows = []
    success = 0
    
    for i, symbol in enumerate(symbols, start=1):
        label = f"[{i:0{width}}/{total}]  {symbol:<12}"
        trades_path = TRADES_DIR / f"{symbol}.csv"
        
        if not trades_path.exists():
            print(f"{label}->  MISSING")
            continue
        
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
    
    output_path = OUTPUT_DIR / f"{index_name}.csv"
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(output_rows)
    
    print(f"\nProcessed {success}/{total} symbols")
    print(f"Saved to : {output_path.relative_to(BASE_DIR)}")

def main():
    index_paths = sorted(SYMBOL_DIR.glob("*.txt"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    for index_path in index_paths:
        generate_summary_for_index(index_path)

if __name__ == "__main__":
    main()
