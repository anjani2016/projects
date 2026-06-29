import pytest
import pandas as pd

@pytest.fixture
def mock_energy_data():
    """Returns a small sample dataframe matching the expected structure of the CSV."""
    data = {
        'Region': ['Canada', 'Canada', 'Ontario', 'Quebec', 'Canada', 'Canada'],
        'Year': [2020, 2021, 2020, 2020, 2020, 2021],
        'Scenario': ['Net-zero', 'Net-zero', 'Net-zero', 'Net-zero', 'Current', 'Current'],
        'Value': [100, 110, 50, 40, 90, 95]
    }
    return pd.DataFrame(data)
