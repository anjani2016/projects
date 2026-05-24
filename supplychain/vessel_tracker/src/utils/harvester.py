import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
from shapely.geometry import Point, Polygon, LineString

load_dotenv()

class AISHarvester:
    def __init__(self):
        self.api_key = os.getenv("AIS_API_KEY")
        self.log_path = "data/processed/"
        os.makedirs(self.log_path, exist_ok=True)
        
        self.bbox = {"min_lat": 26.0, "max_lat": 27.5, "min_lon": 55.5, "max_lon": 57.0}
        self.hormuz_polygon = Polygon([
            (55.8, 26.2), (56.5, 26.2), (56.8, 26.8), 
            (56.5, 27.2), (55.5, 27.0), (55.8, 26.2)
        ])

    def fetch_live_data(self):
        if not self.api_key:
            return self._generate_mock_data()
        
        url = (f"https://api.vesselfinder.com/vessels?userkey={self.api_key}"
               f"&minlat={self.bbox['min_lat']}&maxlat={self.bbox['max_lat']}"
               f"&minlon={self.bbox['min_lon']}&maxlon={self.bbox['max_lon']}")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data if isinstance(data, list) else [data])
            
            # --- Robust Normalization ---
            df.columns = [str(c).lower() for c in df.columns]
            column_mapping = {
                'longitude': 'lon', 'lng': 'lon',
                'latitude': 'lat',
                'last_seen': 'timestamp', 'time': 'timestamp',
                'heading': 'course', 'cog': 'course', 'dir': 'course'
            }
            df.rename(columns=column_mapping, inplace=True)
            
            if 'lat' not in df.columns or 'lon' not in df.columns:
                return self._generate_mock_data()
                
            return df
        except Exception:
            return self._generate_mock_data()

    def _generate_mock_data(self):
        vcount = 15
        data = {
            "mmsi": [f"MID{i+1000}" for i in range(vcount)],
            "lat": np.random.uniform(self.bbox["min_lat"], self.bbox["max_lat"], vcount),
            "lon": np.random.uniform(self.bbox["min_lon"], self.bbox["max_lon"], vcount),
            "speed": np.random.uniform(5, 22, vcount),
            "course": np.random.uniform(0, 360, vcount),
            "vessel_type": np.random.choice(["Tanker", "Cargo", "Military"], vcount),
            "timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S") for _ in range(vcount)]
        }
        return pd.DataFrame(data)

    def process_data(self, df):
        if df.empty:
            return df

        # --- Ensure Mandatory UI Columns ---
        for col in ['is_dark', 'in_critical_zone']:
            if col not in df.columns:
                df[col] = False
        
        if 'course' not in df.columns:
            df['course'] = 0.0 # Default to North if missing
            
        if 'speed' not in df.columns:
            df['speed'] = 0.0

        if 'lon' not in df.columns or 'lat' not in df.columns:
            return df

        now = datetime.now()
        df['timestamp'] = pd.to_datetime(df.get('timestamp', now))
        df['stale_minutes'] = df['timestamp'].apply(lambda x: (now - x).total_seconds() / 60)
        df['is_dark'] = df['stale_minutes'] > 20
        df['in_critical_zone'] = df.apply(
            lambda row: self.hormuz_polygon.contains(Point(row['lon'], row['lat'])), axis=1
        )
        return df

    def predict_future_positions(self, df, minutes_ahead=15):
        if df.empty or 'lat' not in df.columns or 'course' not in df.columns:
            return df
        
        R = 6371.0
        speed_km_min = (df['speed'] * 1.852) / 60
        dist = speed_km_min * minutes_ahead
        brng = np.radians(df['course'])
        lat1, lon1 = np.radians(df['lat']), np.radians(df['lon'])

        lat2 = np.arcsin(np.sin(lat1) * np.cos(dist/R) + np.cos(lat1) * np.sin(dist/R) * np.cos(brng))
        lon2 = lon1 + np.arctan2(np.sin(brng) * np.sin(dist/R) * np.cos(lat1),
                                 np.cos(dist/R) - np.sin(lat1) * np.sin(lat2))

        df['pred_lat'], df['pred_lon'] = np.degrees(lat2), np.degrees(lon2)
        return df

    def detect_collisions(self, df, safety_radius_km=0.5):
        if len(df) < 2 or 'pred_lat' not in df.columns:
            return []
            
        collisions = []
        df['path'] = df.apply(
            lambda r: LineString([(r['lon'], r['lat']), (r['pred_lon'], r['pred_lat'])]), axis=1
        )

        v_list = df.to_dict('records')
        for i in range(len(v_list)):
            for j in range(i + 1, len(v_list)):
                d = v_list[i]['path'].distance(v_list[j]['path']) * 111
                if d < safety_radius_km:
                    collisions.append({
                        "v_a": v_list[i]['mmsi'], "v_b": v_list[j]['mmsi'],
                        "dist": round(d, 3),
                        "pos_a": (v_list[i]['lat'], v_list[i]['lon']),
                        "pos_b": (v_list[j]['lat'], v_list[j]['lon'])
                    })
        return collisions