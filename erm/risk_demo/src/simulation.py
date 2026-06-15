import numpy as np
import pandas as pd
from xerparser.reader import Reader
import cpm  # CPM math engine

# --- GAME LOGIC ---

def run_game_simulation(mode, trials, repeats):
    """Runs a simple game simulation. Returns an array of sums."""
    if mode == "Coin Toss":
        # 0 or 1, summed over 'trials' times, repeated 'repeats' times
        return np.random.randint(0, 2, size=(repeats, trials)).sum(axis=1)
    elif mode == "Dice Roll":
        # 1 through 6, summed over 'trials' times, repeated 'repeats' times
        return np.random.randint(1, 7, size=(repeats, trials)).sum(axis=1)
    return np.array([])

# --- PROJECT LOGIC ---

def extract_project_data(uploaded_file):
    """Extracts project data from XER or CSV into DataFrames."""
    filename = uploaded_file.name.lower()
    
    if filename.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
        # Normalize column names for flexible matching (lowercase, strip whitespace)
        cols = {c.strip().lower(): c for c in df.columns}
        
        # Helper to find column by exact or partial match
        def get_col(name):
            return cols.get(name.lower())
        
        tasks_data = []
        rels_data = []
        
        for _, row in df.iterrows():
            # Get Task ID
            task_id_col = get_col('s.no.(aka task id)') or get_col('task id') or get_col('id')
            task_id = str(row[task_id_col]) if task_id_col and pd.notna(row[task_id_col]) else str(_)
            
            # Get Durations
            likely_col = get_col('most likely duration') or get_col('duration')
            likely = float(row[likely_col]) if likely_col and pd.notna(row[likely_col]) else 0.0
            
            min_col = get_col('min duration')
            min_d = float(row[min_col]) if min_col and pd.notna(row[min_col]) else likely * 0.9
            
            max_col = get_col('max duration')
            max_d = float(row[max_col]) if max_col and pd.notna(row[max_col]) else likely * 1.3
            
            tasks_data.append({
                'task_id': task_id,
                'base_duration': likely,
                'duration': likely, # Default for base CPM calculation
                'min_duration': min_d,
                'max_duration': max_d,
                'likely_duration': likely
            })
            
            # Get Relationships
            pred_col = get_col('predecessor')
            succ_col = get_col('successor')
            
            preds = str(row[pred_col]).split(',') if pred_col and pd.notna(row[pred_col]) else []
            succs = str(row[succ_col]).split(',') if succ_col and pd.notna(row[succ_col]) else []
            
            for p in preds:
                p = p.strip()
                if p and p != 'nan':
                    rels_data.append({'predecessor': p, 'successor': task_id})
            for s in succs:
                s = s.strip()
                if s and s != 'nan':
                    rels_data.append({'predecessor': task_id, 'successor': s})
                    
        return pd.DataFrame(tasks_data), pd.DataFrame(rels_data)
        
    else:
        # Default XER handling
        uploaded_file.seek(0)
        xer = Reader(uploaded_file.read().decode('cp1252'))
        
        tasks_data = []
        for t in xer.tasks:
            duration = (t.target_drtn_hr_cnt or 0) / 8
            tasks_data.append({
                'task_id': t.task_code,
                'base_duration': duration,
                'duration': duration,
                'min_duration': duration * 0.9,
                'max_duration': duration * 1.3,
                'likely_duration': duration
            })
            
        rels_data = [{'predecessor': r.predecessor_code, 'successor': r.successor_code} for r in xer.taskpreds]
        
        return pd.DataFrame(tasks_data), pd.DataFrame(rels_data)

def run_project_simulation(tasks_df, rels_df, repeats):
    """Runs the Monte Carlo loop using the CPM engine for project schedule."""
    results = []
    for _ in range(repeats):
        sim_tasks = tasks_df.copy()
        def randomize_duration(row):
            min_d = row.get('min_duration', 0)
            max_d = row.get('max_duration', 0)
            likely = row.get('likely_duration', 0)
            
            if max_d > min_d:
                return np.random.triangular(min_d, likely, max_d)
            elif row.get('base_duration', 0) > 0:
                x = row['base_duration']
                return np.random.triangular(x * 0.9, x, x * 1.3)
            return 0
            
        sim_tasks['duration'] = sim_tasks.apply(randomize_duration, axis=1)
        
        # Calculate finish date using the CPM engine
        finish = cpm.calculate_cpm_end_date(sim_tasks, rels_df)
        results.append(finish)
    return np.array(results)

# --- STATISTICAL HELPERS ---

def calculate_stats(results_array):
    """Returns a dictionary of empirical statistics for the given results."""
    s = pd.Series(results_array)
    mean = s.mean()
    median = s.median()
    # mode() returns a Series of modes. Grab the first one.
    modes = s.mode()
    mode = modes[0] if not modes.empty else np.nan
    sd = s.std()
    
    min_val = s.min()
    max_val = s.max()
    p80 = np.percentile(results_array, 80)
    p90 = np.percentile(results_array, 90)
    
    return {
        "mean": mean,
        "median": median,
        "mode": mode,
        "sd": sd,
        "min_val": min_val,
        "max_val": max_val,
        "p80": p80,
        "p90": p90
    }

def calculate_theory(mode, trials, base_duration=None):
    """
    Calculates theoretical mean and standard deviation.
    For projects, uses the base CPM calculation as 'mean', and N/A for SD.
    """
    if mode == "Coin Toss":
        # Binomial distribution: n=trials, p=0.5
        mean = trials * 0.5
        sd = np.sqrt(trials * 0.5 * 0.5)
        return mean, sd
    elif mode == "Dice Roll":
        # Sum of uniform discrete variables
        # Mean of one die = 3.5. Var = 35/12
        mean = trials * 3.5
        sd = np.sqrt(trials * (35/12))
        return mean, sd
    elif mode == "Project Schedule":
        # Theoretical mean is just the deterministic CPM duration
        # We don't have a simple theoretical SD, so we return 0 or None
        return base_duration, 0.0
    
    return 0.0, 0.0

def generate_comparison_summary(current_sim, previous_sim=None):
    """
    Generates a textual summary explaining the results,
    comparing to a previous run if available.
    """
    mode = current_sim['mode']
    c_trials = current_sim['trials']
    c_repeats = current_sim['repeats']
    c_stats = current_sim['stats']
    
    summary = f"**Simulation Summary:** You ran a {mode} simulation with {c_trials} trials per repeat, repeated {c_repeats} times. "
    summary += f"The empirical mean is {c_stats['mean']:.2f} with a standard deviation of {c_stats['sd']:.2f}. "
    
    if previous_sim:
        p_mode = previous_sim['mode']
        p_trials = previous_sim['trials']
        p_repeats = previous_sim['repeats']
        p_stats = previous_sim['stats']
        
        if mode == p_mode:
            if c_trials > p_trials:
                summary += f"\\n\\n**Law of Large Numbers Effect:** By increasing the trials from {p_trials} to {c_trials}, you should notice the distribution curve becoming smoother and closer to a perfect bell shape. "
            elif c_trials < p_trials:
                summary += f"\\n\\n**Law of Large Numbers Effect:** By decreasing the trials from {p_trials} to {c_trials}, the distribution curve may look more jagged and less like a perfect normal distribution. "
            elif c_trials == p_trials and c_repeats == p_repeats:
                mean_diff = abs(c_stats['mean'] - p_stats['mean'])
                summary += f"\\n\\n**Noise:** You ran the exact same parameters as the previous simulation. Notice how the mean shifted slightly by {mean_diff:.2f}? This random variation between identical runs is what we call 'noise'."
        else:
            summary += "\\n\\n(Previous simulation was a different type, so a direct parameter comparison is omitted.)"
            
    summary += "\\n\\n**Percentiles (Statistical Significance):** "
    if mode == "Project Schedule":
        summary += f"The project is expected to be completed in {c_stats['p80']:.1f} days with an 80% significance (P80), "
        summary += f"and {c_stats['p90']:.1f} days with a 90% significance (P90)."
    else:
        summary += f"The values being less than {c_stats['p80']:.1f} is 80% statistically significant (P80). "
        summary += f"The values being less than {c_stats['p90']:.1f} is 90% statistically significant (P90)."
            
    return summary