import csv
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "historical" / "csv_ca"
OUTPUT_DIR = BASE_DIR / "data" / "historical" / "csv_ca_transformed"
OUTPUT_DIR_PATH = f"{BASE_DIR.name}/{OUTPUT_DIR.relative_to(BASE_DIR)}"

DATE_FORMAT = "%d-%b-%Y"

OUTPUT_FIELDNAMES = ["ex_date", "corp_action", "info", "amount"]

CATEGORY_PATTERNS = [
    ("dividend", re.compile(r"dividend", re.IGNORECASE)),
    ("bonus", re.compile(r"bonus", re.IGNORECASE)),
    ("split", re.compile(r"split", re.IGNORECASE)),
    ("rights", re.compile(r"rights", re.IGNORECASE)),
    ("buyback", re.compile(r"buy\s*-?\s*back", re.IGNORECASE)),
    ("demerger", re.compile(r"demerger", re.IGNORECASE)),
]

RATIO_RE = re.compile(r"(\d+)\s*:\s*(\d+)")
RS_AMOUNT_RE = re.compile(r"R[se]\.?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)

def extract_rs_amounts(subject):
    return [float(value) for value in RS_AMOUNT_RE.findall(subject)]

def format_plain(value):
    return str(int(value)) if value == int(value) else str(value)

def category_info_amount(category, subject):
    subject_lower = subject.lower()
    
    if category == "dividend":
        tags = []
        if "interim" in subject_lower:
            tags.append("interim")
        if "special" in subject_lower:
            tags.append("special")
        info = ",".join(tags)
        amounts = extract_rs_amounts(subject)
        amount = f"{sum(amounts):.2f}" if amounts else ""
        return info, amount
    
    if category in ("bonus", "rights"):
        match = RATIO_RE.search(subject)
        info = f"{match.group(1)}:{match.group(2)}" if match else ""
        if category == "rights":
            amounts = extract_rs_amounts(subject)
            amount = f"{sum(amounts):.2f}" if amounts else ""
            return info, amount
        return info, ""
    
    if category == "split":
        amounts = extract_rs_amounts(subject)[:2]
        info = ":".join(format_plain(value) for value in amounts)
        return info, ""
    
    # buyback, demerger
    return "", ""

def transform_row(row):
    ex_date = row.get("exDate", "") or ""
    if ex_date:
        ex_date = datetime.strptime(ex_date, DATE_FORMAT).strftime("%Y-%m-%d")
    subject = row.get("subject", "") or ""
    categories = [name for name, pattern in CATEGORY_PATTERNS if pattern.search(subject)]
    
    if not categories:
        return None
    
    infos = []
    amounts = []
    for category in categories:
        info, amount = category_info_amount(category, subject)
        infos.append(info)
        amounts.append(amount)
    
    corp_action = ",".join(categories)
    if len(categories) == 1:
        info, amount = infos[0], amounts[0]
    else:
        info = ",".join(infos)
        non_blank_amounts = [float(value) for value in amounts if value]
        amount = f"{sum(non_blank_amounts):.2f}" if non_blank_amounts else ""
    
    return {"ex_date": ex_date, "corp_action": corp_action, "info": info, "amount": amount}

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

def transform_csv(input_path, output_path):
    with open(input_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = [row for row in (transform_row(row) for row in reader) if row is not None]
    
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
