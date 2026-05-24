import geopandas as gpd
subs = gpd.read_parquet('data/processed/analyzed_substations.parquet')
print("Total substations:", len(subs))
