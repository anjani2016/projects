import pytest
from unittest.mock import patch
from models.weather_engine import get_forecasted_rainfall

@patch('models.weather_engine.requests.get')
def test_get_forecasted_rainfall(mock_get):
    mock_response = mock_get.return_value
    mock_response.json.return_value = {
        'list': [
            {'rain': {'3h': 5}},
            {'rain': {'3h': 2}},
            {'rain': {}},
            {}
        ]
    }
    
    rain = get_forecasted_rainfall('dummy_api_key', 'Aurora,CA')
    assert rain == 7
