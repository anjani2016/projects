import pandas as pd
import numpy as np
import io
import pytest
from simulation import (
    run_game_simulation,
    extract_project_data,
    run_project_simulation,
    calculate_stats,
    calculate_theory,
    generate_comparison_summary
)

def test_run_game_simulation_coin_toss():
    results = run_game_simulation("Coin Toss", 100, 1000)
    assert len(results) == 1000
    assert (results >= 0).all() and (results <= 100).all()

def test_run_game_simulation_dice_roll():
    results = run_game_simulation("Dice Roll", 10, 500)
    assert len(results) == 500
    assert (results >= 10).all() and (results <= 60).all()

def test_run_game_simulation_invalid():
    results = run_game_simulation("Unknown", 10, 10)
    assert len(results) == 0

def test_calculate_stats():
    arr = np.array([1, 2, 3, 4, 5])
    stats = calculate_stats(arr)
    assert stats['mean'] == 3.0
    assert stats['median'] == 3.0
    assert stats['min_val'] == 1
    assert stats['max_val'] == 5
    assert stats['sd'] > 0

def test_calculate_theory_coin_toss():
    mean, sd = calculate_theory("Coin Toss", 100)
    assert mean == 50.0
    assert sd == 5.0

def test_calculate_theory_dice_roll():
    mean, sd = calculate_theory("Dice Roll", 100)
    assert mean == 350.0
    assert np.isclose(sd, 17.078, atol=0.01)

def test_calculate_theory_project_schedule():
    mean, sd = calculate_theory("Project Schedule", 100, base_duration=42.0)
    assert mean == 42.0
    assert sd == 0.0

def test_generate_comparison_summary():
    sim1 = {
        'mode': 'Coin Toss',
        'trials': 100,
        'repeats': 1000,
        'stats': {'mean': 50.1, 'sd': 5.0, 'p80': 55.0, 'p90': 58.0}
    }
    sim2 = {
        'mode': 'Coin Toss',
        'trials': 50,
        'repeats': 1000,
        'stats': {'mean': 25.1, 'sd': 3.5, 'p80': 28.0, 'p90': 30.0}
    }
    
    summary = generate_comparison_summary(sim1, sim2)
    assert "Law of Large Numbers Effect" in summary
    assert "By increasing the trials" in summary

def test_extract_project_data_csv():
    csv_data = "s.no.(aka task id),task,duration,predecessor,successor\n1,Task A,5,,\n2,Task B,3,1,"
    uploaded_file = io.StringIO(csv_data)
    uploaded_file.name = "test.csv"
    
    tasks_df, rels_df = extract_project_data(uploaded_file)
    assert len(tasks_df) == 2
    assert len(rels_df) == 1
    assert rels_df.iloc[0]['predecessor'] == '1.0'
    assert rels_df.iloc[0]['successor'] == '2'

def test_run_project_simulation():
    tasks_df = pd.DataFrame([
        {'task_id': '1', 'base_duration': 10, 'likely_duration': 10, 'min_duration': 8, 'max_duration': 12},
        {'task_id': '2', 'base_duration': 5, 'likely_duration': 5, 'min_duration': 4, 'max_duration': 6}
    ])
    rels_df = pd.DataFrame([
        {'predecessor': '1', 'successor': '2'}
    ])
    results = run_project_simulation(tasks_df, rels_df, 100)
    assert len(results) == 100
    assert (results >= 12).all() and (results <= 18).all()
