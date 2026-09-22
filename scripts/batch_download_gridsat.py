import os
import sys
import urllib.request
from datetime import timedelta
from pathlib import Path

# Add the project root to sys.path so we can import the unified pipeline
script_dir = Path(__file__).parent.resolve()
project_root = script_dir.parent
sys.path.append(str(project_root))

from notebooks.sih26_unified_pipeline import EVENTS

def main():
    print("="*60)
    print("SIH26 - LOCAL NOAA GRIDSAT-B1 BATCH DOWNLOADER")
    print("="*60)
    
    download_dir = project_root / "data" / "raw" / "gridsat"
    download_dir.mkdir(parents=True, exist_ok=True)
    
    # We can download data for ALL cyclones since GridSat goes back decades!
    # Unlike INSAT-3DR which was only post-2016.
    print(f"Found {len(EVENTS)} total cyclones to download.")
    
    base_url = "https://noaa-cdr-gridsat-b1-pds.s3.amazonaws.com/data/{year}/GRIDSAT-B1.{year}.{month:02d}.{day:02d}.{hour:02d}.v02r01.nc"
    
    for i, event in enumerate(EVENTS):
        event_id = event["id"]
        start_date = event["start"]
        end_date = event["end"]
        
        event_download_dir = download_dir / event_id
        event_download_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n[{i+1}/{len(EVENTS)}] {event_id} ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
        
        current_date = start_date
        while current_date <= end_date:
            for hour in [0, 3, 6, 9, 12, 15, 18, 21]:
                year = current_date.year
                month = current_date.month
                day = current_date.day
                
                url = base_url.format(year=year, month=month, day=day, hour=hour)
                filename = f"GRIDSAT-B1.{year}.{month:02d}.{day:02d}.{hour:02d}.v02r01.nc"
                filepath = event_download_dir / filename
                
                if filepath.exists():
                    print(f"  [SKIPPED] {filename} already exists.")
                    continue
                
                try:
                    print(f"  [DOWNLOADING] {filename}...", end="", flush=True)
                    # Add a User-Agent header just in case, though S3 public buckets rarely require it
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=30) as response, open(filepath, 'wb') as out_file:
                        data = response.read()
                        out_file.write(data)
                    print(f" Done! ({len(data) / 1024 / 1024:.2f} MB)")
                except urllib.error.HTTPError as e:
                    if e.code == 404:
                        print(f" Not Found (404) on AWS S3.")
                    else:
                        print(f" HTTP Error: {e.code}")
                except Exception as e:
                    print(f" Error: {e}")
                    
            current_date += timedelta(days=1)
            
    print("\nBatch download process finished!")

if __name__ == "__main__":
    main()
