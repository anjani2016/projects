# src/engines/scraper.py
import pandas as pd
import requests
from io import StringIO
import os
from datetime import datetime, timedelta

def fetch_ieso_data(year_month):
    """
    Fetches the Day-Ahead Hourly Energy LMP for a specific month by aggregating daily reports.
    year_month: string in 'YYYYMM' format.
    """
    base_url = "https://reports-public.ieso.ca/public/DAHourlyEnergyLMP/PUB_DAHourlyEnergyLMP_{date}.csv"
    
    # Calculate start and end date for the month
    try:
        start_date = datetime.strptime(year_month, "%Y%m")
        if start_date.month == 12:
            end_date = datetime(start_date.year + 1, 1, 1)
        else:
            end_date = datetime(start_date.year, start_date.month + 1, 1)
    except Exception as e:
        return f"Error parsing month: {e}"

    all_frames = []
    current_date = start_date
    
    while current_date < end_date:
        date_str = current_date.strftime("%Y%m%d")
        url = base_url.format(date=date_str)
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # The CSV has 1 row of metadata before the header
                df_day = pd.read_csv(StringIO(response.text), skiprows=1)
                
                # Filter for the Ontario Zonal Price
                df_zonal = df_day[df_day['Pricing Location'] == 'ONTARIO_ZONAL_PRICE'].copy()
                
                if not df_zonal.empty:
                    # Add a proper timestamp column
                    df_zonal['Date'] = current_date.strftime("%Y-%m-%d")
                    all_frames.append(df_zonal)
            else:
                # Some days might be missing if they are in the future or not yet published
                pass
        except Exception:
            # Skip failed days but log if necessary
            pass
            
        current_date += timedelta(days=1)

    if not all_frames:
        return f"Error: No data found for {year_month} in the Day-Ahead LMP reports."

    # Combine all days
    full_df = pd.concat(all_frames, ignore_index=True)
    
    # Standardize column names for the app logic
    full_df = full_df.rename(columns={'LMP': 'Ontario Price', 'Delivery Hour': 'Hour'})
    
    # Create a proper Timestamp column
    # Hour in IESO is 1-24. We convert to 0-23 for pandas to_datetime
    full_df['Timestamp'] = pd.to_datetime(full_df['Date']) + pd.to_timedelta(full_df['Hour'] - 1, unit='h')
    
    # Sort by Timestamp
    full_df = full_df.sort_values('Timestamp')
    
    return full_df

def save_raw_data(df, year_month):
    """Saves the dataframe to the data/raw directory."""
    file_path = f"data/raw/ieso_prices_{year_month}.csv"
    df.to_csv(file_path, index=False)
    return file_path
