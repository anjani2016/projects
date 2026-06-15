import pandas as pd
import numpy as np
import seaborn as sns
import requests as req
import io
import geopandas as gpd
import folium
import matplotlib.pyplot as plt
import dash
from dash import dcc, html
import plotly.express as px
    
def load_data():
    url = "https://www.cer-rec.gc.ca/open/energy/energyfutures2026/electricity-capacity-2026.csv"
    df = pd.read_csv(url)                                   
    return df

def process_data(df):
    """Filter for Canada and pivot data."""
    df_canada = df[df['Region'] == 'Canada'].pivot_table(
        index='Year',
        columns='Scenario',
        values='Value'
    ).sort_index()
    return df_canada

def create_figure(df_canada):
    """Create the Plotly line chart."""
    fig = px.line(df_canada,
                  title='Energy Futures - Canada',
                  labels={'value': 'Energy Demand',
                          'Year': 'Year',
                          'variable': 'Scenario'},
                  markers=True)
    return fig

def get_layout(fig):
    """Return the Dash app layout."""
    return html.Div([
        html.H1("Canada Energy Plotly Dashboard"),
        dcc.Graph(id='main-chart',
                  figure=fig)
    ])

# 1. Initialize the app
app = dash.Dash(__name__)

# 2. Expose the server (CRITICAL for free hosting like Render)
server = app.server

# 3. Setup global data (for runtime)
try:
    df_raw = load_data()
    df_processed = process_data(df_raw)
    figure = create_figure(df_processed)
    app.layout = get_layout(figure)
except Exception as e:
    print(f"Error loading initial data: {e}")
    app.layout = html.Div([html.H1("Error loading data")])

if __name__ == '__main__':
    app.run(debug=True)
