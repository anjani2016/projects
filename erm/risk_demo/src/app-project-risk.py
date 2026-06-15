import streamlit as st
import simulation-project-risk as sim

st.title("🏗️ Project Risk Simulator 🪙")

file = st.file_uploader("Upload .xer file", type="xer")

if file:
    tasks, rels = sim.extract_xer_data(file)
    st.write(f"Loaded {len(tasks)} tasks.")

    if st.button("Run Simulation"):
        # The result list is returned directly here
        final_results = sim.run_project_simulation(tasks, rels, 1000)
        
        st.subheader("Simulation Results")
        st.line_chart(final_results)
        st.write(f"Average Projected Duration: {sum(final_results)/len(final_results):.2f} days")