import json
import time
import requests
from datetime import date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "symbol" / "NIFTY_50.txt"
OUTPUT_DIR = BASE_DIR / "data" / "historical" / "json"
OUTPUT_DIR_PATH = f"{BASE_DIR.name}/{OUTPUT_DIR.relative_to(BASE_DIR)}"

START_DATE = date(2011, 1, 1)
CHUNK_DAYS = 90
CHUNK_RETRIES = 3
SYMBOL_RETRIES = 3

API_URL = "https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData"

HEADERS = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "referer": "https://www.nseindia.com/report-detail/eq_security",
    "user-agent": (
        "Mozilla/5.0 (Linux; Android 15; Pixel 9) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/152.0.0.0 Mobile Safari/537.36"
    )
}

def read_symbols(path):
    if not path.exists():
        raise FileNotFoundError(f"Symbol file not found: {path}")
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]

def clear_output_dir():
    if OUTPUT_DIR.exists():
        existing_files = list(OUTPUT_DIR.glob("*.json"))
        for file_path in existing_files:
            file_path.unlink()
        print(f"Output directory exists : {OUTPUT_DIR_PATH}")
        print(f"\nCleared output directory")
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created output directory : {OUTPUT_DIR_PATH}")

def get_session(max_retries=3):
    for attempt in range(max_retries):
        try:
            session = requests.Session()
            session.headers.update(HEADERS)
            session.get("https://www.nseindia.com", timeout=10).raise_for_status()
            time.sleep(1)
            return session
        except requests.RequestException:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)

def date_chunks(start, end, days):
    chunks = []
    current = start
    while current <= end:
        chunk_end = min(current + timedelta(days=days - 1), end)
        chunks.append((current.strftime("%d-%m-%Y"), chunk_end.strftime("%d-%m-%Y")))
        current = chunk_end + timedelta(days=1)
    return chunks

def fetch_chunk(session, params, chunk_retries):
    for attempt in range(chunk_retries):
        try:
            if attempt > 0:
                session = get_session()
            response = session.get(API_URL, params=params, timeout=15)
            response.raise_for_status()
            payload = response.json()
            if "data" not in payload:
                raise ValueError()
            return session, payload["data"]
        except (requests.RequestException, ValueError):
            if attempt == chunk_retries - 1:
                raise
            time.sleep(2 ** attempt)

def fetch_symbol(session, symbol, chunk_retries=CHUNK_RETRIES):
    all_records = []
    end_date = date.today() - timedelta(days=1)
    for from_date, to_date in date_chunks(START_DATE, end_date, CHUNK_DAYS):
        params = {
            "from": from_date,
            "to": to_date,
            "symbol": symbol,
            "type": "priceVolumeDeliverable",
            "series": "EQ",
        }
        
        session, records = fetch_chunk(session, params, chunk_retries)
        all_records.extend(records)
        
        time.sleep(0.5)
    return session, {"data": all_records}

def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def main():
    try:
        symbols = read_symbols(INPUT_PATH)
        total = len(symbols)
        width = len(str(total))
        
        clear_output_dir()
        print(f"\nDownloading data for {total} symbols ...\n")
        
        try:
            session = get_session()
        except requests.RequestException:
            print("Failed to connect to NSE")
            return
        
        success = 0
        
        for i, symbol in enumerate(symbols, start=1):
            label = f"[{i:0{width}}/{total}]  {symbol:<12}"
            output_path = OUTPUT_DIR / f"{symbol}.json"
            
            if i % 50 == 1 and i > 1:
                print(f"\nRefreshing session ...\n")
                try:
                    session = get_session()
                except requests.RequestException:
                    print("Failed to refresh session")
                    break
            
            for attempt in range(SYMBOL_RETRIES):
                try:
                    if attempt > 0:
                        session = get_session()
                    session, data = fetch_symbol(session, symbol)
                    save_json(data, output_path)
                    count = len(data.get("data", []))
                    suffix = " (retry)" if attempt > 0 else ""
                    print(f"{label}->  {count} records{suffix}")
                    success += 1
                    break
                except Exception:
                    pass
            else:
                print(f"{label}->  ERROR")
            
            time.sleep(1)
        
        print()
        print(f"Downloaded data for {success}/{total} symbols")
        print(f"Saved to : {OUTPUT_DIR_PATH}")
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled")

if __name__ == "__main__":
    main()
