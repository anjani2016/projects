import pytest
import pandas as pd
import numpy as np
from models.hydrology_engine import calculate_nutrient_loading, get_runoff_coefficient, build_3d_mesh, ingest_ontario_csv

def test_calculate_nutrient_loading():
    volume = calculate_nutrient_loading(10.0, 5.0, 0.5)
    # 10mm = 0.01m, 5km2 = 5e6 m2. 0.01 * 5e6 * 0.5 = 25000.0
    assert volume == 25000.0

def test_get_runoff_coefficient():
    coeff = get_runoff_coefficient(60) # 60% agri
    # 0.6 * 0.5 + 0.4 * 0.1 = 0.3 + 0.04 = 0.34
    assert round(coeff, 2) == 0.34

def test_build_3d_mesh():
    df = pd.DataFrame({
        'x': [0, 1, 0, 1],
        'y': [0, 0, 1, 1],
        'depth': [-5, -10, -5, -10]
    })
    grid_x, grid_y, grid_z = build_3d_mesh(df)
    assert grid_x.shape == (100, 100)
    assert grid_y.shape == (100, 100)
    assert grid_z.shape == (100, 100)

def test_ingest_ontario_csv(tmp_path):
    df_in = pd.DataFrame({
        'OGF_ID': [1, 2],
        'DEPTH': [5, 10],
        'geometry': ['POINT(1 1)', 'POINT(2 2)']
    })
    file_path = tmp_path / "test.csv"
    df_in.to_csv(file_path, index=False)
    
    df_out = ingest_ontario_csv(file_path)
    assert 'depth' in df_out.columns
    # Ensure depth is negative
    assert df_out['depth'].iloc[0] == -5
    assert df_out['depth'].iloc[1] == -10
