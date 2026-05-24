#!/bin/bash
# Activate the virtual environment
source fjord_env/bin/activate

# Ensure Python can find the 'src' directory
export PYTHONPATH=.

# Run Streamlit using the virtual environment's Python
python -m streamlit run app/main.py
