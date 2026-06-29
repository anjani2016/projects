import pandas as pd
from cpm import calculate_cpm_end_date

def test_calculate_cpm_end_date_simple():
    tasks = pd.DataFrame([
        {'task_id': 'A', 'duration': 5},
        {'task_id': 'B', 'duration': 3},
        {'task_id': 'C', 'duration': 4}
    ])
    rels = pd.DataFrame([
        {'predecessor': 'A', 'successor': 'B'},
        {'predecessor': 'A', 'successor': 'C'}
    ])
    
    end_date = calculate_cpm_end_date(tasks, rels)
    assert end_date == 9

def test_calculate_cpm_end_date_linear():
    tasks = pd.DataFrame([
        {'task_id': '1', 'duration': 10},
        {'task_id': '2', 'duration': 20}
    ])
    rels = pd.DataFrame([
        {'predecessor': '1', 'successor': '2'}
    ])
    
    end_date = calculate_cpm_end_date(tasks, rels)
    assert end_date == 30
