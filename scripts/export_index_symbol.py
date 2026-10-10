import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "misc" / "index"
OUTPUT_DIR = BASE_DIR / "data" / "symbol"
OUTPUT_DIR_PATH = f"{BASE_DIR.name}/{OUTPUT_DIR.relative_to(BASE_DIR)}"

def ensure_output_dir():
    if OUTPUT_DIR.exists():
        print(f"Output directory exists : {OUTPUT_DIR_PATH}")
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created output directory : {OUTPUT_DIR_PATH}")

def export_symbols(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    
    symbols = [row[0] for row in rows[2:]]
    name = rows[1][0].replace(" ", "_")
    
    out_path = OUTPUT_DIR / f"{name}.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(symbols) + "\n")
    
    return name

def main():
    ensure_output_dir()
    print()
    
    csv_paths = sorted(INPUT_DIR.glob("*.csv"))
    total = len(csv_paths)
    print(f"Generating symbols for {total} indices ...")
    print()
    
    success = 0
    for i, csv_path in enumerate(csv_paths, start=1):
        try:
            name = export_symbols(csv_path)
            print(f"[{i}/{total}] {name}")
            success += 1
        except Exception:
            print(f"[{i}/{total}] {csv_path.name} : ERROR")
    
    print()
    print(f"Generated symbols for {success}/{total} indices")
    print(f"Exported to : {OUTPUT_DIR_PATH}")

if __name__ == "__main__":
    main()
