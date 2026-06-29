import pytest
import pandas as pd
from unittest.mock import patch
from energydata_plot.app import load_data, process_data, create_figure, get_layout

# --- Unit Tests ---

@patch('pandas.read_csv')
def test_load_data(mock_read_csv, mock_energy_data):
    """Unit test: load_data should call pd.read_csv with the correct URL."""
    mock_read_csv.return_value = mock_energy_data
    
    df = load_data()
    
    mock_read_csv.assert_called_once()
    assert "electricity-capacity-2026.csv" in mock_read_csv.call_args[0][0]
    assert df.equals(mock_energy_data)

def test_process_data(mock_energy_data):
    """Unit test: process_data should filter for 'Canada' and pivot correctly."""
    processed_df = process_data(mock_energy_data)
    
    # Check that only 'Canada' remains (Region should be dropped in pivot, so check shape/content)
    # Expected: index Year (2020, 2021), columns Scenario (Current, Net-zero)
    assert processed_df.index.name == 'Year'
    assert list(processed_df.columns) == ['Current', 'Net-zero']
    assert 2020 in processed_df.index
    assert 2021 in processed_df.index
    
    # Check specific values
    # Canada, 2020, Net-zero -> 100
    assert processed_df.loc[2020, 'Net-zero'] == 100
    # Canada, 2021, Current -> 95
    assert processed_df.loc[2021, 'Current'] == 95

# --- Block (Integration) Tests ---

def test_pipeline_integration(mock_energy_data):
    """Block test: Test the full flow from processing to figure creation."""
    processed_df = process_data(mock_energy_data)
    fig = create_figure(processed_df)
    
    # Verify the figure object
    assert fig.layout.title.text == 'Energy Futures - Canada'
    # Plotly Express markers attribute
    assert len(fig.data) == 2 # Two scenarios: Current, Net-zero
    assert fig.data[0].mode == 'lines+markers'

def test_layout_structure():
    """Block test: Verify the Dash layout contains expected components."""
    # Create a dummy pivoted dataframe
    dummy_df = pd.DataFrame({'Scenario A': [1, 2], 'Scenario B': [3, 4]}, index=[2000, 2001])
    dummy_df.index.name = 'Year'
    fig = create_figure(dummy_df)
    
    layout = get_layout(fig)
    
    # Check for main components
    children = layout.children
    assert any(child.children == "Canada Energy Plotly Dashboard" for child in children if hasattr(child, 'children'))
    assert any(child.id == 'main-chart' for child in children if hasattr(child, 'id'))

# --- Regression Tests ---

def test_figure_labels_regression(mock_energy_data):
    """Regression test: Ensure labels and titles don't change unexpectedly."""
    processed_df = process_data(mock_energy_data)
    fig = create_figure(processed_df)
    
    assert fig.layout.xaxis.title.text == 'Year'
    assert fig.layout.yaxis.title.text == 'Energy Demand' # Updated to match app.py labels
    assert fig.layout.legend.title.text == 'Scenario'
    
    # Verify markers are enabled (as per requirement in app.py)
    for trace in fig.data:
        assert 'markers' in trace.mode
