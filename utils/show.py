import sys
import pandas as pd

# Columns (products): 
# Dataset Type	Product	
# Description	Resolution  Projection	Product Definition Path	Origin
df = pd.DataFrame(
    columns=
['Dataset Type', 'Product', 'Description', 
 'Resolution', 'Projection', 'Product Definition Path', 'Origin'],
    data=[
 ['Landsat 5 Collection 1 Level 2 (SR)', 'ls5_usgs_sr_scene',
  'N/A', '30m', 'EPSG:4326', 'Landsat/prod_defs/ls5_usgs_sr_scene',
  'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml'],
 ['Landsat 7 Collection 1 Level 2 (SR)', 'ls7_usgs_sr_scene', 'N/A', '30m',
  'EPSG:4326', 'Landsat/prod_defs/ls7_usgs_sr_scene', 
  'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml'],
 ['Landsat 8 Collection 1 Level 2 (SR)', 'ls8_usgs_sr_scene', 'N/A', '30m',
  'EPSG:4326', 'Landsat/prod_defs/ls8_usgs_sr_scene', 
  'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml'],
 ['JERS-1 SAR (HH)', 'jers_sar_mosaic', 'N/A', '25m', 'EPSG:4326', 'JERS-1/prod_defs/jers_sar_mosaic',
  'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml'],
 ['Sentinel-2 Level 2A (Copernicus Format)', 's2_ard_scene', 'from Copernicus Open Access Hub', '10-20m',
  'varies', 'Sentinel-2/L2A/prod_defs/s2_ard_scene_prod_def.yaml', 'N/A'],
 ['Landsat 8 Collection 2 Level 2 (SR)', 'ls8_l2_c2', 'N/A', '30m', 'EPSG:4326',
  'Landsat/collection_2/prod_defs/ls8_l2_c2_public_bucket', \
  'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml']])\
 .set_index('Dataset Type')
print(df)

# Columns (indexable remote datasets):
# Dataset Type	Path	
# Description	Command	Products


# Columns (indexing scripts):
# Dataset Type  Path-Format	Example	Origin

# Final columns (m denotes possible multiple records - 
# e.g. there are multiple datasets per product):
# Dataset_Type      Product     Prod_Description    Prod_Resolution 
# Prod_Projection   Prod_Def_Path_Origin    Dataset_Path(m)
# 


# TODO: Commands:
# 1. make show-products
# 2. make show-indexing <product-name>
# 3. make show-columns <col1...coln>