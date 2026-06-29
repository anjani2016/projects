import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.utils.harvester import AISHarvester
from unittest.mock import patch, MagicMock

@pytest.fixture
def harvester():
    return AISHarvester()

def test_fetch_live_data_mock(harvester):
    # Test fallback to mock data when API key is missing
    with patch.object(harvester, 'api_key', None):
        df = harvester.fetch_live_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 15
        assert all(col in df.columns for col in ['mmsi', 'lat', 'lon', 'speed', 'course', 'timestamp'])

def test_process_data_empty(harvester):
    df = pd.DataFrame()
    processed_df = harvester.process_data(df)
    assert processed_df.empty

def test_process_data_valid(harvester):
    now = datetime.now()
    stale_time = now - timedelta(minutes=25)
    recent_time = now - timedelta(minutes=5)
    
    data = {
        'mmsi': ['V1', 'V2'],
        'lat': [26.5, 27.0],
        'lon': [56.0, 56.5],
        'speed': [10.0, 15.0],
        'course': [90.0, 180.0],
        'timestamp': [stale_time, recent_time]
    }
    df = pd.DataFrame(data)
    processed_df = harvester.process_data(df)
    
    assert 'is_dark' in processed_df.columns
    assert 'in_critical_zone' in processed_df.columns
    assert 'stale_minutes' in processed_df.columns
    
    # V1 is stale, so it should be dark
    assert processed_df.loc[processed_df['mmsi'] == 'V1', 'is_dark'].iloc[0] == True
    # V2 is recent, so it should not be dark
    assert processed_df.loc[processed_df['mmsi'] == 'V2', 'is_dark'].iloc[0] == False
    
    # Check critical zone (V1 is in Hormuz polygon, V2 is on the edge/outside)
    # Hormuz: (55.8, 26.2) to (56.8, 26.8) roughly
    # 26.5, 56.0 is inside
    assert processed_df.loc[processed_df['mmsi'] == 'V1', 'in_critical_zone'].iloc[0] == True

def test_predict_future_positions(harvester):
    data = {
        'mmsi': ['V1'],
        'lat': [26.0],
        'lon': [56.0],
        'speed': [10.0],
        'course': [90.0]  # East
    }
    df = pd.DataFrame(data)
    pred_df = harvester.predict_future_positions(df, minutes_ahead=60)
    
    assert 'pred_lat' in pred_df.columns
    assert 'pred_lon' in pred_df.columns
    
    # After 60 minutes at 10 knots (~18.52 km/h) heading East
    # Lat should be roughly same, Lon should increase
    assert np.isclose(pred_df['pred_lat'].iloc[0], 26.0, atol=0.1)
    assert pred_df['pred_lon'].iloc[0] > 56.0

def test_detect_collisions(harvester):
    data = {
        'mmsi': ['V1', 'V2'],
        'lat': [26.0, 26.0],
        'lon': [56.0, 56.001], # Very close
        'pred_lat': [26.1, 26.1],
        'pred_lon': [56.0, 56.001]
    }
    df = pd.DataFrame(data)
    collisions = harvester.detect_collisions(df, safety_radius_km=1.0)
    
    assert len(collisions) == 1
    assert collisions[0]['v_a'] == 'V1'
    assert collisions[0]['v_b'] == 'V2'
