import pandas as pd
import numpy as np
import seaborn as sns
import requests as req
import io
import geopandas as gpd
import folium
import matplotlib.pyplot as plt
import streamlit as st
# from ydata_profiling import ProfileReport


# This is the direct link to the 'Electricity Capacity 2026' CSV from the Open Gov portal
def load_data():
    url = "https://www.cer-rec.gc.ca/open/energy/energyfutures2026/electricity-capacity-2026.csv"
    df = pd.read_csv(url)                                   
    return df





def main():
    
    st.title('Energy Futures')

    df = load_data()                    # Load directly into your project

    # data manipulation

    df_canada = df[df['Region'] == 'Canada'].pivot_table(
        index = 'Year',
        columns ='Scenario',
        values = 'Value'
    ).sort_index()


    # data visualization

    # 1. create the plot
    ax = df_canada.plot (kind = 'line', marker = 'o', figsize= (10,6))

    # 2. professional styling

    plt.title('Energy Futures', fontsize = 36)
    plt.xlabel('Year', fontsize = 12)
    plt.ylabel ('Energy Demand', fontsize = 12)
    plt.grid(True, linestyle = '--', alpha = .3)
    plt.legend( title = 'Scenarios', loc= 'upper left')

    # plt.legend( title = 'Scenarios', bbox_to_anchor=(1.05,1),loc= 'upper left')

    # 3.display
    plt.tight_layout()
    plt.show()
    st.pyplot(ax.figure)

if __name__ == '__main__':
    main()