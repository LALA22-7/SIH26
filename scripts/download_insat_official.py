import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

MOSDAC_USERNAME = os.getenv("MOSDAC_USERNAME")
MOSDAC_PASSWORD = os.getenv("MOSDAC_PASSWORD")

if not MOSDAC_USERNAME or not MOSDAC_PASSWORD:
    print("Error: MOSDAC_USERNAME and MOSDAC_PASSWORD must be set in scripts/.env")
    print("Please refer to scripts/.env.example for the format.")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Automated MOSDAC INSAT-3DR Downloader using Official API")
    parser.add_argument("--event", type=str, help="Name of the event (e.g. biparjoy_2023)")
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--dataset", type=str, default="3SIMG_L1B_STD", help="Dataset ID (Default: 3SIMG_L1B_STD for INSAT-3DR Imager)")
    
    args = parser.parse_args()

    # Define paths
    script_dir = Path(__file__).parent.resolve()
    mosdac_api_dir = script_dir / "mosdac_api"
    config_path = mosdac_api_dir / "config.json"
    download_dir = script_dir.parent / "data" / "raw" / "insat"
    download_dir.mkdir(parents=True, exist_ok=True)
    
    # We must format path correctly for JSON (forward slashes)
    download_path_str = str(download_dir).replace('\\', '/')

    print(f"[{args.event}] Generating MOSDAC config.json for {args.start} to {args.end}...")
    
    # Construct config.json exactly as the manual requires
    # Important: The key is "username" or "username/email" depending on the mdapi.py version.
    # The manual says "username" in the example, but the actual config.json had "username/email".
    # We will use "username" as per manual Appendix A, but let's check config.json we viewed: it had "username/email".
    # We will use "username" because the manual explicitly corrects it in the text.
    
    config_data = {
        "user_credentials": {
            "username": MOSDAC_USERNAME,
            "password": MOSDAC_PASSWORD
        },
        "search_parameters": {
            "datasetId": args.dataset,
            "startTime": args.start,
            "endTime": args.end,
            "count": "",
            "boundingBox": "",
            "gId": ""
        },
        "download_settings": {
            "download_path": download_path_str,
            "organize_by_date": False,
            "skip_user_input": True,
            "generate_error_logs": True,
            "error_logs_dir": ""
        }
    }

    # Write the config.json inside the mosdac_api directory
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=4)
        
    print(f"Config saved to {config_path}. Launching official mdapi.py...")
    
    # Run the official mdapi.py
    try:
        # We must run it from inside its own directory because it looks for config.json locally
        result = subprocess.run(
            [sys.executable, "mdapi.py"],
            cwd=mosdac_api_dir,
            check=True
        )
        print("MOSDAC download process finished successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running mdapi.py. Process exited with code {e.returncode}")
        sys.exit(1)
        
if __name__ == "__main__":
    main()
