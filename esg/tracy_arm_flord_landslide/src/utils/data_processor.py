import os
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from shapely.geometry import box

class TopobathyProcessor:
    """
    Handles CRS reprojection, clipping, and merging of Land DEM 
    and Bathymetry datasets for the Tracy Arm Digital Twin.
    """
    def __init__(self, raw_dir="data/raw", processed_dir="data/processed"):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        
        # Define target CRS: NAD83 / UTM Zone 8N (Units: Meters)
        self.target_crs = "EPSG:26908"
        
        # Bounding Box for Tracy Arm Fjord (WGS84 Geographic)
        self.bbox_wgs84 = {
            "lon_min": -134.15,
            "lat_min": 57.75,
            "lon_max": -133.55,
            "lat_max": 58.00
        }
        
        os.makedirs(self.processed_dir, exist_ok=True)

    def merge_dem_tiles(self, tile_filenames, output_filename):
        """
        Mosaics multiple DEM tiles into a single TIFF.
        """
        from rasterio.merge import merge
        
        tile_paths = [os.path.join(self.raw_dir, name) for name in tile_filenames]
        opened_files = [rasterio.open(p) for p in tile_paths]
        try:
            mosaic, out_trans = merge(opened_files)
            out_meta = opened_files[0].meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": mosaic.shape[1],
                "width": mosaic.shape[2],
                "transform": out_trans,
                "crs": opened_files[0].crs
            })
            
            output_path = os.path.join(self.raw_dir, output_filename)
            with rasterio.open(output_path, "w", **out_meta) as dest:
                dest.write(mosaic)
                
            return output_path
        finally:
            for f in opened_files:
                f.close()

    def reproject_raster(self, input_filename, output_filename, resolution=30.0):
        """
        Reprojects an input raster to the target UTM Coordinate Reference System.
        """
        input_path = os.path.join(self.raw_dir, input_filename)
        output_path = os.path.join(self.processed_dir, output_filename)
        
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Missing raw data file: {input_path}")
            
        with rasterio.open(input_path) as src:
            transform, width, height = calculate_default_transform(
                src.crs, self.target_crs, src.width, src.height, *src.bounds,
                resolution=resolution
            )
            metadata = src.meta.copy()
            metadata.update({
                'crs': self.target_crs,
                'transform': transform,
                'width': width,
                'height': height
            })
            
            with rasterio.open(output_path, 'w', **metadata) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=self.target_crs,
                        resampling=Resampling.bilinear
                    )
        return output_path

    def clip_to_fjord(self, input_processed_path, final_filename):
        """
        Clips the reprojected UTM raster to the Tracy Arm operational bounding window.
        """
        final_output_path = os.path.join(self.processed_dir, final_filename)
        
        # Create bounding polygon geometry
        geom = box(
            self.bbox_wgs84["lon_min"], 
            self.bbox_wgs84["lat_min"], 
            self.bbox_wgs84["lon_max"], 
            self.bbox_wgs84["lat_max"]
        )
        
        with rasterio.open(input_processed_path) as src:
            # Transform geometry bounding parameters to match raster CRS
            from rasterio.warp import transform_geom
            geom_utm = transform_geom("EPSG:4326", src.crs, geom)
            
            # Crop raster
            out_image, out_transform = mask(src, [geom_utm], crop=True)
            out_meta = src.meta.copy()
            
            out_meta.update({
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform
            })
            
            with rasterio.open(final_output_path, "w", **out_meta) as dest:
                dest.write(out_image)
                
        return final_output_path

    def generate_unified_mesh(self, dem_path, bathy_path):
        """
        Combines Land DEM and Bathymetry data into a singular model matrix grid.
        Assumes bathymetry depths are negative or zero, and land values are positive.
        """
        with rasterio.open(dem_path) as dem_src, rasterio.open(bathy_path) as bathy_src:
            # Read and resample bathymetry to exactly match the resolution footprint of Land DEM
            bathy_data = bathy_src.read(
                1,
                out_shape=(dem_src.height, dem_src.width),
                resampling=Resampling.cubic
            )
            dem_data = dem_src.read(1)
            
            # Clean NoData values (replace with 0.0 baseline or interpolation proxies)
            dem_data[dem_data == dem_src.nodata] = 0.0
            bathy_data[bathy_data == bathy_src.nodata] = 0.0
            
            # Ensure bathymetry values are negative representing subsurface depths
            if np.min(bathy_data) >= 0 and np.max(bathy_data) > 0:
                print("Bathymetry values detected as positive. Negating to represent subsurface depths.")
                bathy_data = -np.abs(bathy_data.astype(np.float32))
            
            # Merge logic: Use bathymetry where values are strictly sub-surface (< 0) 
            # and land DEM where elevation structures emerge (> 0)
            unified_topo_matrix = np.where(dem_data > 0, dem_data, bathy_data)
            
            # Export structured binary array matrix for high performance calculation loops
            matrix_output_path = os.path.join(self.processed_dir, "tracy_arm_mesh.npy")
            np.save(matrix_output_path, unified_topo_matrix)
            
            # Save a geo-referenced master GeoTIFF output
            master_meta = dem_src.meta.copy()
            master_output_path = os.path.join(self.processed_dir, "tracy_arm_topobathy.tif")
            with rasterio.open(master_output_path, "w", **master_meta) as dst:
                dst.write(unified_topo_matrix, 1)
                
        print("Pipeline execution complete. Hydrodynamic simulation matrices generated.")

# Execution entrypoint block
if __name__ == "__main__":
    processor = TopobathyProcessor()
    try:
        # Check if individual tiles exist and merge them
        raw_dem_57 = os.path.join(processor.raw_dir, "tracy_arm_dem_57.tif")
        raw_dem_58 = os.path.join(processor.raw_dir, "tracy_arm_dem_58.tif")
        
        if os.path.exists(raw_dem_57) and os.path.exists(raw_dem_58):
            print("Real DEM tiles detected (57, 58). Merging tiles...")
            processor.merge_dem_tiles(["tracy_arm_dem_57.tif", "tracy_arm_dem_58.tif"], "tracy_arm_dem.tif")
            
        # Step 1: Reproject files
        # Reproject DEM with 30m resolution for stable simulation grid sizing
        dem_proj = processor.reproject_raster("tracy_arm_dem.tif", "dem_utm.tif", resolution=30.0)
        
        # Make bathymetry reprojection optional if raw bathymetry is not present
        bathy_raw_path = os.path.join(processor.raw_dir, "tracy_arm_bathymetry.tif")
        if os.path.exists(bathy_raw_path):
            bathy_proj = processor.reproject_raster("tracy_arm_bathymetry.tif", "bathy_utm.tif", resolution=30.0)
            final_bathy = processor.clip_to_fjord(bathy_proj, "tracy_arm_bathymetry_clipped.tif")
        else:
            print("Raw bathymetry file missing. Using pre-processed bathymetry...")
            final_bathy = os.path.join(processor.processed_dir, "tracy_arm_bathymetry_clipped.tif")
            
        # Step 2: Clip to exact bounding window parameters
        final_dem = processor.clip_to_fjord(dem_proj, "tracy_arm_dem_clipped.tif")
        
        # Step 3: Align resolutions and build array matrix
        processor.generate_unified_mesh(final_dem, final_bathy)
        
    except FileNotFoundError as e:
        print(f"Execution Halted: {e}")
        print("Please ensure source files are placed in data/raw/ before running execution steps.")