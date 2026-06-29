import pytest
import pandas as pd
import numpy as np
from energy.ieso_hedging_tool.src.engines.forecasting import LMPForecaster

def test_lmp_forecaster_initialization():
    forecaster = LMPForecaster(model_type="test_model")
    assert forecaster.model_type == "test_model"

def test_lmp_forecaster_fit():
    forecaster = LMPForecaster()
    df = pd.DataFrame({
        "Ontario Price": [10, 20, 15, 25, 30]
    })
    forecaster.fit(df)
    assert hasattr(forecaster, "mu_est")
    assert hasattr(forecaster, "sigma_est")
    assert hasattr(forecaster, "theta_est")
    assert forecaster.mu_est == pytest.approx(20.0)

def test_lmp_forecaster_fit_empty():
    forecaster = LMPForecaster()
    df = pd.DataFrame(columns=["Ontario Price"])
    forecaster.fit(df)
    assert not hasattr(forecaster, "mu_est")

def test_lmp_forecaster_predict():
    forecaster = LMPForecaster()
    df = pd.DataFrame({
        "Ontario Price": [30, 31, 29, 30, 31]
    })
    forecaster.fit(df)
    predictions = forecaster.predict_next_hours(last_spot=30, hours=5)
    assert len(predictions) == 5
    assert isinstance(predictions, np.ndarray)
