from common import *

# Columns (products): 
# Define columns as vars for autocomplete (convenient, avoids typos).
prd_df_col_prd = 'ProdName'
prd_df_col_descr = 'ProdDesc'
prd_df_col_res = 'ProdRes'
prd_df_col_proj = 'ProdProj'
prd_df_col_prd_def_path = 'ProdDefPath'
prd_df_col_origin = 'ProdDefOrigin'
prd_cols = [col_product_type, prd_df_col_prd, prd_df_col_descr, prd_df_col_res,
            prd_df_col_proj, prd_df_col_prd_def_path, prd_df_col_origin]

prd_df = pd.DataFrame(
    columns=prd_cols,
    data=[
[ls5_c1_l2_product_type, 'ls5_usgs_sr_scene',
 'N/A', '30m', 'EPSG:4326', 'Landsat/collection_1/prod_defs/ls5_usgs_sr_scene.yaml',
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml'],
[ls7_c1_l2_product_type, 'ls7_usgs_sr_scene', 'N/A', '30m',
 'EPSG:4326', 'Landsat/collection_1/prod_defs/ls7_usgs_sr_scene.yaml', 
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml'],
[ls8_c1_l2_product_type, 'ls8_usgs_sr_scene', 'N/A', '30m',
 'EPSG:4326', 'Landsat/collection_1/prod_defs/ls8_usgs_sr_scene.yaml', 
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml'],
[jers1_sar_hh_product_type, 'jers_sar_mosaic', 'N/A', '25m', 'EPSG:4326', 'JERS-1/prod_defs/jers_sar_mosaic.yaml',
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml'],
[sntnl2_l2a_product_type, 's2_ard_scene', 'from Copernicus Open Access Hub', '10-20m',
 'varies', 'Sentinel-2/L2A/prod_defs/s2_ard_scene_prod_def.yaml', 'N/A'],
[ls8_c2_l2_product_type, 'ls8_l2_c2', 'N/A', '30m', 'EPSG:4326',
 'Landsat/collection_2/prod_defs/ls8_l2_c2_public_bucket.yaml', \
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml'],
[ls7_c2_l2_product_type, 'ls7_l2_c2', 'N/A', '30m',
 'EPSG:4326', 'Landsat/collection_2/prod_defs/ls7_l2_c2.yaml', 
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml']])