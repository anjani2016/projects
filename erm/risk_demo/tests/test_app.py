import pytest
from streamlit.testing.v1 import AppTest

def test_app_initial_state():
    """Test that the app loads and displays the correct initial state."""
    at = AppTest.from_file("src/app.py").run()
    
    assert not at.exception
    assert at.title[0].value == "🎲 Monte Carlo Simulation Dashboard 🪙"
    assert at.selectbox[0].value == "Coin Toss"
    assert at.number_input[0].value == 100 # trials
    assert at.number_input[1].value == 1000 # repeats

def test_coin_toss_simulation():
    """Test running the Coin Toss simulation."""
    at = AppTest.from_file("src/app.py").run()
    
    # Click the Run Simulation button
    at.button[0].click().run()
    
    assert not at.exception
    
    # Check that a simulation result was added to the history
    assert len(at.subheader) > 0
    assert "Simulation #1 - Coin Toss" in [sh.value for sh in at.subheader]

def test_dice_roll_simulation():
    """Test running the Dice Roll simulation."""
    at = AppTest.from_file("src/app.py").run()
    
    # Select Dice Roll mode
    at.selectbox[0].select("Dice Roll").run()
    assert at.selectbox[0].value == "Dice Roll"
    
    # Click the Run Simulation button
    at.button[0].click().run()
    
    assert not at.exception
    
    # Check that a simulation result was added to the history
    assert "Simulation #1 - Dice Roll" in [sh.value for sh in at.subheader]

def test_project_schedule_no_file_error():
    """Test that running Project Schedule without a file shows an error."""
    at = AppTest.from_file("src/app.py").run()
    
    # Select Project Schedule mode
    at.selectbox[0].select("Project Schedule").run()
    assert at.selectbox[0].value == "Project Schedule"
    
    # Click the Run Simulation button
    at.button[0].click().run()
    
    assert not at.exception
    # Should show an error message
    assert len(at.error) > 0
    assert at.error[0].value == "Please upload an .xer or .csv file to run the project simulation."
