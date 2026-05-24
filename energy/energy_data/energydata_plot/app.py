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
    
# This is the direct link to the 'Electricity Capacity 2026' CSV from the Open Gov portal
def load_data():
    url = "https://www.cer-rec.gc.ca/open/energy/energyfutures2026/electricity-capacity-2026.csv"
    df = pd.read_csv(url)                                   
    return df

df = load_data()                    # Load directly into your project

# data manipulation

df_canada = df[df['Region'] == 'Canada'].pivot_table(
    index = 'Year',
    columns ='Scenario',
    values = 'Value'
).sort_index()

# data visualization

    # 1. create the plot
fig = px.line(df_canada,
              title = 'Energy Futures - Canada',
              labels = {'Value': 'Energy Demand',
                        'Year': 'Year'},
              markers = True)


# 1. Initialize the app
app = dash.Dash(__name__)

# 2. Expose the server (CRITICAL for free hosting like Render)
server = app.server

# 3. Define the layout (This is where the HTML-like structure goes)
app.layout = html.Div([
    html.H1("Canada Energy Plotly Dashboard"),
    dcc.Graph(id='main-chart',
              figure=fig)
])

if __name__ == '__main__':
    app.run_server(debug=True)
