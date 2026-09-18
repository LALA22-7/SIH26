import os
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

MOSDAC_USERNAME = os.getenv('MOSDAC_USERNAME')
MOSDAC_PASSWORD = os.getenv('MOSDAC_PASSWORD')
MOSDAC_LOGIN_URL = 'https://mosdac.gov.in/login' # Example URL
MOSDAC_CATALOG_URL = 'https://mosdac.gov.in/catalog/search' # Example URL

def download_insat_data(event_name: str, start_date: str, end_date: str, output_dir: str):
    """
    Automated pipeline for downloading INSAT-3DR HDF5 data from MOSDAC.
    Uses a requests Session to maintain login cookies.
    """
    print(f"Starting MOSDAC download for {event_name} ({start_date} to {end_date})")
    
    if not MOSDAC_USERNAME or not MOSDAC_PASSWORD:
        raise ValueError("MOSDAC credentials not found. Please check your .env file.")

    session = requests.Session()
    
    # 1. Fetch login page to get CSRF tokens if any
    try:
        print("Connecting to MOSDAC...")
        login_page = session.get(MOSDAC_LOGIN_URL)
        soup = BeautifulSoup(login_page.text, 'html.parser')
        
        # Scrape CSRF token (adjust based on actual MOSDAC login form)
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        csrf_value = csrf_token['value'] if csrf_token else ''

        # 2. Perform Login
        print("Authenticating...")
        login_data = {
            'username': MOSDAC_USERNAME,
            'password': MOSDAC_PASSWORD,
            'csrf_token': csrf_value
        }
        
        # Some endpoints require specific headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        auth_response = session.post(MOSDAC_LOGIN_URL, data=login_data, headers=headers)
        
        if auth_response.status_code != 200:
            print("Warning: Login might have failed. Status code:", auth_response.status_code)
        
        # 3. Query Catalog for INSAT-3DR data
        print("Querying INSAT-3DR catalog...")
        # Note: Replace with actual MOSDAC API parameters for INSAT-3DR L1B/L1C data
        search_params = {
            'satellite': 'INSAT-3DR',
            'sensor': 'IMAGER',
            'start_date': start_date,
            'end_date': end_date
        }
        
        catalog_response = session.get(MOSDAC_CATALOG_URL, params=search_params)
        
        if catalog_response.status_code == 200:
            # Parse the catalog response (assuming JSON for this example)
            # data_files = catalog_response.json().get('files', [])
            data_files = [] # Mocked for now
            
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            
            for file_info in data_files:
                file_url = file_info['download_url']
                file_name = file_info['name']
                print(f"Downloading {file_name}...")
                
                with session.get(file_url, stream=True) as r:
                    r.raise_for_status()
                    with open(out_path / file_name, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
            
            print(f"Success: Automation pipeline ready to download data for {event_name}.")
            print("Note: Update the parsing logic with actual MOSDAC API responses once you inspect the payload.")
        else:
            print(f"Failed to query catalog. Status: {catalog_response.status_code}")
            
    except Exception as e:
        print(f"Error during MOSDAC automation: {e}")

if __name__ == "__main__":
    # Example usage for testing
    import argparse
    parser = argparse.ArgumentParser(description="Download INSAT-3DR data from MOSDAC")
    parser.add_argument("--event", type=str, required=True, help="Cyclone event name (e.g. Biparjoy)")
    parser.add_argument("--start", type=str, required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", type=str, required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--out", type=str, default="../data/raw/insat", help="Output directory")
    
    args = parser.parse_args()
    download_insat_data(args.event, args.start, args.end, args.out)
