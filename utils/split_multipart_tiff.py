"""
Exports a multipart TIFF ("BigTIFF") 
to multile single-layer TIFFs.
"""

from osgeo import gdal
from import_export import export_xarray_to_geotiff

# open TIFF file (reading) mode and get dimensions
ds = gdal.Open(r'LEVEL2_S2_FORCE_BOA.tif', 0)
width = ds.RasterXSize
height = ds.RasterYSize

# define tile size and number of pixels to move in each direction
tile_size_x = 10980
tile_size_y = 10980
stride_x = 10980
stride_y = 10980

# Determine the CRS.
# import rasterio as rio
# with rio.open(r'LEVEL2_S2_FORCE_BOA.tif') as src:
#     print(src.crs)

# Find these from the TIFF with `gdalinfo`.
band_names = \
    ['blue', 'green', 'red', 'rededge1', 'rededge2',
     'rededge3', 'broadnir', 'nir', 'swir1', 'swir2']

for x_off in range(0, width, stride_y):
    for y_off in range(0, height, stride_x):

        # read tile and export each band
        arr = ds.ReadAsArray(x_off, y_off, tile_size_x, tile_size_y)
        for i in range(10):
            arr_band = arr[i]
            import xarray as xr
            import numpy as np
            y_coords = np.linspace(699960, 809760, stride_x)
            x_coords = np.linspace(3490200, 3600000, stride_y)
            xr_da = \
                xr.DataArray(arr_band, 
                    dims=['x', 'y'],
                    coords={'x':x_coords, 'y':y_coords}, 
                    attrs={'crs': "EPSG:32636"})

            # export to TIFF
            output_tiff_path = f'{band_names[i]}.tif'
            print(f"exporting to {output_tiff_path}")
            export_xarray_to_geotiff(xr_da, tif_path=output_tiff_path,
                x_coord='x', y_coord='y')