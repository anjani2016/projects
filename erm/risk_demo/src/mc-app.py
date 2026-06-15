import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import simulation as sim
import content
import cpm

st.set_page_config(page_title="Monte Carlo Simulation", layout="wide")

if 'sim_count' not in st.session_state:
    st.session_state.sim_count = 0
if 'simulation_history' not in st.session_state:
    st.session_state.simulation_history = []

st.title("🎲 Monte Carlo Simulation Dashboard 🪙")

with st.expander("📖 Introduction to Monte Carlo & Statistics"):
    st.markdown(content.get_intro_text())
    st.markdown(content.get_definitions())

with st.expander(" 🪙 Tossing a coin, to 🎲 Dice roll, to 🌍 Project Scheduling"):
    st.markdown(content.get_bridge_content())

with st.expander("🌍 Real-World Applications"):
    st.markdown(content.get_real_world_examples())

with st.sidebar:
    st.info(content.get_sidebar_info())
    mode = st.selectbox("Simulation Type", ["Coin Toss", "Dice Roll", "Project Schedule"])
    
    if mode == "Project Schedule":
        uploaded_file = st.file_uploader("Upload .xer or .csv file", type=["xer", "csv"])
        st.markdown("**For CSV files, recommended columns:**")
        st.info("`s.no.(aka task id)`, `task`, `early start`, `early finish`, `min duration`, `max duration`, `most likely duration`, `predecessor`, `successor`")
        repeats = st.number_input("Repeats (Simulations)", value=1000, step=100, max_value=10000)
        st.caption("Max limit: 10,000 simulations to ensure app stability")
        trials = None # N/A for project
    else:
        uploaded_file = None
        trials = st.number_input("Trials per Repeat", value=100, step=10, max_value=10000)
        repeats = st.number_input("Repeats (Sample Size)", value=1000, step=100, max_value=10000)
        st.caption("Max limit: 10,000 per input to ensure app stability")
        
    run_btn = st.button("Run Simulation")

if run_btn:
    if mode == "Project Schedule" and not uploaded_file:
        st.error("Please upload an .xer or .csv file to run the project simulation.")
    else:
        st.session_state.sim_count += 1
        
        # Run Simulation
        if mode == "Project Schedule":
            tasks_df, rels_df = sim.extract_project_data(uploaded_file)
            base_duration = cpm.calculate_cpm_end_date(tasks_df, rels_df)
            results = sim.run_project_simulation(tasks_df, rels_df, repeats)
            t_mean, t_sd = sim.calculate_theory(mode, trials=0, base_duration=base_duration)
        else:
            results = sim.run_game_simulation(mode, trials, repeats)
            t_mean, t_sd = sim.calculate_theory(mode, trials)
            
        stats = sim.calculate_stats(results)
        
        # Build Sim Object
        current_sim = {
            'sim_num': st.session_state.sim_count,
            'mode': mode,
            'trials': trials if trials else "N/A",
            'repeats': repeats,
            'results': results,
            'stats': stats,
            't_mean': t_mean,
            't_sd': t_sd
        }
        
        # Generate Summary
        prev_sim = st.session_state.simulation_history[0] if len(st.session_state.simulation_history) > 0 else None
        current_sim['summary'] = sim.generate_comparison_summary(current_sim, prev_sim)
        
        # Prepend to history so newest is on top
        st.session_state.simulation_history.insert(0, current_sim)

# Display History
if len(st.session_state.simulation_history) > 0:
    st.header("📊 Results History")
    
    for sim_run in st.session_state.simulation_history:
        st.subheader(f"Simulation #{sim_run['sim_num']} - {sim_run['mode']}")
        
        st.info(sim_run['summary'])
        
        # Create columns for Visuals and Data
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig, ax = plt.subplots()
            import numpy as np
            
            # Plot probability density instead of frequency
            label_text = f"Trials: {sim_run['trials']}\\nRepeats: {sim_run['repeats']}"
            ax.hist(sim_run['results'], bins=50, density=True, color='skyblue', edgecolor='black', alpha=0.7, label=label_text)
            
            # Superimpose Theoretical Normal Curve
            t_mean = sim_run['t_mean']
            t_sd = sim_run['t_sd']
            
            if t_sd > 0:
                xmin, xmax = ax.get_xlim()
                x = np.linspace(xmin, xmax, 100)
                # Normal Distribution PDF Formula
                p = (1 / (t_sd * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - t_mean) / t_sd) ** 2)
                ax.plot(x, p, 'k--', linewidth=2, label='_nolegend_')
            
            ax.set_title(f"Probability Density Function of {sim_run['mode']}")
            ax.set_xlabel("Value")
            ax.set_ylabel("Probability Density")
            ax.legend()
            st.pyplot(fig)
            
        with col2:
            st.markdown("### Empirical Stats")
            st.write(f"**Mean:** {sim_run['stats']['mean']:.2f}")
            st.write(f"**Median:** {sim_run['stats']['median']:.2f}")
            st.write(f"**Mode:** {sim_run['stats']['mode']:.2f}")
            st.write(f"**Standard Dev:** {sim_run['stats']['sd']:.2f}")
            st.write(f"**Range:** {sim_run['stats']['min_val']:.2f} to {sim_run['stats']['max_val']:.2f}")
            
            st.markdown("### Theoretical Values")
            t_mean = sim_run['t_mean']
            t_sd = sim_run['t_sd']
            
            if t_sd == 0.0:
                st.warning(f"Base Deterministic Duration: {t_mean:.2f}\\n\\n(Theoretical normal distribution bounds are N/A for raw project schedule calculations.)")
            else:
                sigmas = [1, 2, 3, 6]
                df = pd.DataFrame({
                    "Sigma": [f"{s}σ" for s in sigmas],
                    "Lower Bound": [t_mean - (s * t_sd) for s in sigmas],
                    "Upper Bound": [t_mean + (s * t_sd) for s in sigmas]
                })
                st.table(df)
        
        st.divider()