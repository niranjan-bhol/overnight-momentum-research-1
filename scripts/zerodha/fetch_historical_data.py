import os
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ACCESS_TOKEN_FILE = "access_token.txt"
TOKEN_PATH = BASE_DIR / "data" / "zerodha" / "auth" / ACCESS_TOKEN_FILE
SYMBOLS_PATH = BASE_DIR / "data" / "zerodha" / "symbol" / "symbols.json"
OUTPUT_DIR = BASE_DIR / "data" / "zerodha" / "historical" / "json"
OUTPUT_DIR_PATH = f"{BASE_DIR.name}/{OUTPUT_DIR.relative_to(BASE_DIR)}"

API_BASE_URL = "https://api.kite.trade/instruments/historical"

INTERVAL = "minute"
MAX_DAYS = 60

START_DATE = "2015-02-01"
END_DATE = "2026-09-30"  # None = up to yesterday, or set e.g. 2025-12-31

def load_access_token():
    with open(TOKEN_PATH, "r") as f:
        return f.read().strip()

def load_symbols():
    with open(SYMBOLS_PATH, "r") as f:
        return json.load(f)

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

def generate_date_chunks(start_date_str, end_date_str, max_days):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    chunk_delta = timedelta(days=max_days)
    chunks = []
    current_start = start_date
    
    while current_start <= end_date:
        current_end = min(current_start + chunk_delta - timedelta(days=1), end_date)
        
        chunks.append((
            current_start.strftime("%Y-%m-%d"),
            current_end.strftime("%Y-%m-%d")
        ))
        
        current_start = current_end + timedelta(days=1)
    
    return chunks

def fetch_historical_data(instrument_token, from_date, to_date, access_token):
    url = f"{API_BASE_URL}/{instrument_token}/{INTERVAL}"
    
    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {API_KEY}:{access_token}"
    }
    
    params = {
        "from": from_date,
        "to": to_date,
        "continuous": 0,
        "oi": 1
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None

def merge_candle_data(chunks_data):
    all_candles = []
    
    for chunk_data in chunks_data:
        if chunk_data and chunk_data.get("status") == "success":
            candles = chunk_data.get("data", {}).get("candles", [])
            all_candles.extend(candles)
    
    unique_candles = {}
    for candle in all_candles:
        timestamp = candle[0]
        unique_candles[timestamp] = candle
    
    sorted_candles = sorted(unique_candles.values(), key=lambda x: x[0])
    
    return {
        "status": "success",
        "data": {
            "candles": sorted_candles
        }
    }

def process_symbol(symbol_name, instrument_token, end_date, access_token, idx, total):
    print(f"\n[{idx}/{total}] {symbol_name}")
    print(f"  Instrument : {instrument_token}")
    print(f"  Date range : {START_DATE} to {end_date}")
    
    date_chunks = generate_date_chunks(START_DATE, end_date, MAX_DAYS)
    
    print(f"  Fetching data in {len(date_chunks)} chunks")
    
    chunks_data = []
    total_chunks = len(date_chunks)
    chunk_width = len(str(total_chunks))
    
    for chunk_idx, (chunk_from, chunk_to) in enumerate(date_chunks, 1):
        print(f"    Chunk {chunk_idx:>{chunk_width}}/{total_chunks}  :  {chunk_from} to {chunk_to}  ->", end="  ")
        
        data = fetch_historical_data(
            instrument_token,
            f"{chunk_from} 00:00:00", f"{chunk_to} 23:59:59",
            access_token
        )
        
        if data:
            candle_count = len(data.get("data", {}).get("candles", []))
            print(f"{candle_count:,} candles")
            chunks_data.append(data)
        else:
            print("ERROR")
    
    if len(chunks_data) > 1:
        print("  Merging chunks")
        final_data = merge_candle_data(chunks_data)
    elif len(chunks_data) == 1:
        final_data = chunks_data[0]
    else:
        print("  ERROR : no data fetched")
        return False
    
    output_file = OUTPUT_DIR / f"{symbol_name}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2)
    
    total_candles = len(final_data.get("data", {}).get("candles", []))
    print(f"  Saved : {total_candles:,} total candles to {symbol_name}.json")
    
    return True

def main():
    try:
        access_token = load_access_token()
        symbols = load_symbols()
        
        end_date = END_DATE if END_DATE else (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        clear_output_dir()
        
        success_count = 0
        total_symbols = len(symbols)
        
        for idx, (symbol_name, instrument_token) in enumerate(symbols.items(), 1):
            if process_symbol(symbol_name, instrument_token, end_date, access_token, idx, total_symbols):
                success_count += 1
        
        print(f"\nSuccessfully downloaded data for {success_count}/{total_symbols} symbols")
        print(f"Saved to : {OUTPUT_DIR_PATH}")
    
    except Exception:
        print("ERROR")

if __name__ == "__main__":
    main()
