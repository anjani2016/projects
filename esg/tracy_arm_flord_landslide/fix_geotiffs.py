import rasterio
from rasterio.transform import from_bounds
import os

def fix_geotiff(input_path, output_path, lon_min, lat_min, lon_max, lat_max):
    with rasterio.open(input_path) as src:
        data = src.read(1)
        height, width = data.shape
        
        # Calculate the affine transform based on the bounding box
        transform = from_bounds(lon_min, lat_min, lon_max, lat_max, width, height)
        
        # Update metadata to include CRS and Transform
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': 'EPSG:4326',
            'transform': transform,
            'driver': 'GTiff'
        })
        
        with rasterio.open(output_path, 'w', **kwargs) as dst:
            dst.write(data, 1)
            
if __name__ == "__main__":
    # Bounds defined in the data_processor.py
    lon_min, lat_min, lon_max, lat_max = -134.15, 57.75, -133.55, 58.00
    
    print("Fixing DEM...")
    fix_geotiff('data/raw/tracy_arm_dem.tif', 'data/raw/tracy_arm_dem_fixed.tif', lon_min, lat_min, lon_max, lat_max)
    os.rename('data/raw/tracy_arm_dem_fixed.tif', 'data/raw/tracy_arm_dem.tif')
    
    print("Fixing Bathymetry...")
    fix_geotiff('data/raw/tracy_arm_bathymetry.tif', 'data/raw/tracy_arm_bathymetry_fixed.tif', lon_min, lat_min, lon_max, lat_max)
    os.rename('data/raw/tracy_arm_bathymetry_fixed.tif', 'data/raw/tracy_arm_bathymetry.tif')
    
    print("Files successfully georeferenced!")
