import os
import cdsapi
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

CDSAPI_URL = os.getenv("CDSAPI_URL")
CDSAPI_KEY = os.getenv("CDSAPI_KEY")

def download_era5_sample():
    print("Testing Copernicus ERA5 download via cdsapi...")
    if not CDSAPI_URL or not CDSAPI_KEY:
        print("Error: CDSAPI credentials not found in .env")
        return
        
    c = cdsapi.Client(url=CDSAPI_URL, key=CDSAPI_KEY)
    
    out_dir = Path(__file__).parent.parent / "data" / "raw" / "era5"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "sample_era5.nc"
    
    print("Requesting 1 hour of wind data...")
    c.retrieve(
        'reanalysis-era5-single-levels',
        {
            'product_type': 'reanalysis',
            'format': 'netcdf',
            'variable': [
                '10m_u_component_of_wind', '10m_v_component_of_wind',
            ],
            'year': '2023',
            'month': '06',
            'day': '01',
            'time': [
                '12:00',
            ],
            'area': [
                30, 50, 0, 100, # Bounding box for Indian Ocean region roughly
            ],
        },
        str(out_file)
    )
    print(f"Download complete! Saved to {out_file}")

if __name__ == "__main__":
    download_era5_sample()
