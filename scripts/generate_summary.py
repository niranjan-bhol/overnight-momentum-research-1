import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TRADES_DIR = BASE_DIR / "data" / "calculated" / "trades"
OUTPUT_DIR = BASE_DIR / "data" / "result" / "summary"
OUTPUT_PATH = OUTPUT_DIR / "summary.csv"
OUTPUT_PATH_STR = f"{BASE_DIR.name}/{OUTPUT_PATH.relative_to(BASE_DIR)}"

OUTPUT_FIELDNAMES = [
    "symbol", "trade_count", "abs_pnl", "pct_pnl",
    "win_count", "loss_count", "win_rate",
    "max_drawdown_abs", "max_drawdown_pct",
]

def summarize_trades(trades_path):
    trade_count = 0
    abs_pnl_total = 0.0
    pct_pnl_total = 0.0
    win_count = 0
    loss_count = 0
    
    cum_abs = 0.0
    cum_pct = 0.0
    peak_abs = 0.0
    peak_pct = 0.0
    max_drawdown_abs = 0.0
    max_drawdown_pct = 0.0
    
    with open(trades_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("date"):
                continue
            trade_count += 1
            try:
                abs_pnl = float(row["abs_pnl"])
                abs_pnl_total += abs_pnl
                if abs_pnl > 0:
                    win_count += 1
                elif abs_pnl < 0:
                    loss_count += 1
                cum_abs += abs_pnl
                peak_abs = max(peak_abs, cum_abs)
                max_drawdown_abs = max(max_drawdown_abs, peak_abs - cum_abs)
            except (KeyError, ValueError):
                pass
            try:
                pct_pnl = float(row["pct_pnl"])
                pct_pnl_total += pct_pnl
                cum_pct += pct_pnl
                peak_pct = max(peak_pct, cum_pct)
                max_drawdown_pct = max(max_drawdown_pct, peak_pct - cum_pct)
            except (KeyError, ValueError):
                pass
    
    win_rate = round(win_count / trade_count * 100, 4) if trade_count else 0.0
    
    return (
        trade_count, round(abs_pnl_total, 4), round(pct_pnl_total, 4),
        win_count, loss_count, win_rate,
        round(max_drawdown_abs, 4), round(max_drawdown_pct, 4),
    )

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
            (
                trade_count, abs_pnl_total, pct_pnl_total,
                win_count, loss_count, win_rate,
                max_drawdown_abs, max_drawdown_pct,
            ) = summarize_trades(trades_path)
            output_rows.append({
                "symbol": symbol,
                "trade_count": trade_count,
                "abs_pnl": abs_pnl_total,
                "pct_pnl": pct_pnl_total,
                "win_count": win_count,
                "loss_count": loss_count,
                "win_rate": win_rate,
                "max_drawdown_abs": max_drawdown_abs,
                "max_drawdown_pct": max_drawdown_pct,
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
