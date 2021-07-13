from common import *

## Product Names and Paths##
## Landsat
landsat_prod_dir = f'{prod_def_dir}/Landsat'
### Landsat Collection 1
landsat_c1_prod_dir = f'{landsat_prod_dir}/collection_1'
ls5_c1_l2_prod_name = 'ls5_usgs_sr_scene'
ls5_c1_l2_prod_path = f'{landsat_c1_prod_dir}/{ls5_c1_l2_prod_name}.yaml'
ls7_c1_l2_prod_name = 'ls7_usgs_sr_scene'
ls7_c1_l2_prod_path = f'{landsat_c1_prod_dir}/{ls7_c1_l2_prod_name}.yaml'
ls8_c1_l2_prod_name = 'ls8_usgs_sr_scene'
ls8_c1_l2_prod_path = f'{landsat_c1_prod_dir}/{ls8_c1_l2_prod_name}.yaml'
### Landsat Collection 2
landsat_c2_prod_dir = f'{landsat_prod_dir}/collection_2'
ls5_c2_l2_prod_name = 'ls5_l2_c2'
ls5_c2_l2_prod_path = f'{landsat_c2_prod_dir}/{ls5_c2_l2_prod_name}.yaml'
ls7_c2_l2_prod_name = 'ls7_l2_c2'
ls7_c2_l2_prod_path = f'{landsat_c2_prod_dir}/{ls7_c2_l2_prod_name}.yaml'
ls8_c2_l2_prod_name = 'ls8_l2_c2'
ls8_c2_l2_prod_path = f'{landsat_c2_prod_dir}/{ls8_c2_l2_prod_name}.yaml'
## Sentinel-1
sentinel_1_prod_dir = f'{prod_def_dir}/Sentinel-1'
s1_rtc_card4l_prod_name = 's1_rtc_card4l'
s1_rtc_card4l_prod_path = f'{sentinel_1_prod_dir}/{s1_rtc_card4l_prod_name}.yaml'
## Sentinel-2
sentinel_2_prod_dir = f'{prod_def_dir}/Sentinel-2'
s2_ard_scene_prod_name = 's2_ard_scene'
s2_ard_scene_prod_path = f'{sentinel_2_prod_dir}/{s2_ard_scene_prod_name}.yaml'
s2_l2a_aws_cog_prod_name = 's2_l2a_aws_cog'
s2_l2a_aws_cog_prod_path = f'{sentinel_2_prod_dir}/{s2_l2a_aws_cog_prod_name}.yaml'
## JERS-1
jers_1_prod_dir = f'{prod_def_dir}/JERS-1'
jers_sar_mosaic_prod_name = 'jers_sar_mosaic'
jers_sar_mosaic_prod_path = f'{jers_1_prod_dir}/{jers_sar_mosaic_prod_name}.yaml'
## Copernicus Global Land Cover
copernicus_lc100_prod_name = 'copernicus_lc100'
copernicus_lc100_prod_path = f'{prod_def_dir}/{copernicus_lc100_prod_name}.yaml'
## Black Marble Night Lights
black_marble_night_lights_prod_name = 'black_marble_night_lights'
black_marble_night_lights_prod_path = f'{prod_def_dir}/{black_marble_night_lights_prod_name}.yaml'
## WebODM DJI Mavic Mini
WebODM_MavicMini_prod_dir = f'{prod_def_dir}/WebODM_MavicMini'
WebODM_MavicMini_prod_name = 'WebODM_MavicMini'
WebODM_MavicMini_prod_path = f'{WebODM_MavicMini_prod_dir}/{WebODM_MavicMini_prod_name}.yaml'
# Same as `WebODM_MavicMini`, but only RGBA measurements.
WebODM_MavicMini_RGBA_prod_name = 'WebODM_MavicMini_RGBA'
WebODM_MavicMini_RGBA_prod_path = f'{WebODM_MavicMini_prod_dir}/{WebODM_MavicMini_RGBA_prod_name}.yaml'
## End Product Names ##

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
## Landsat
[ls5_c1_l2_product_type, ls5_c1_l2_prod_name, 'N/A', '30m', 
 'EPSG:4326', ls5_c1_l2_prod_path,
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml'],
[ls7_c1_l2_product_type, ls7_c1_l2_prod_name, 'N/A', '30m',
 'EPSG:4326', ls7_c1_l2_prod_path, 
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml'],
[ls8_c1_l2_product_type, ls8_c1_l2_prod_name, 'N/A', '30m',
 'EPSG:4326', ls8_c1_l2_prod_path, 
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml'],
[ls5_c2_l2_product_type, ls5_c2_l2_prod_name, 'N/A', '30m',
 'EPSG:4326', ls5_c2_l2_prod_path, 
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml'],
[ls7_c2_l2_product_type, ls7_c2_l2_prod_name, 'N/A', '30m',
 'EPSG:4326', ls7_c2_l2_prod_path, 
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml'],
[ls8_c2_l2_product_type, ls8_c2_l2_prod_name, 'N/A', '30m', 
 'EPSG:4326', ls8_c2_l2_prod_path, \
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml'],
## Sentinel-1
[sntnl1_product_type, s1_rtc_card4l_prod_name, 'from Copernicus Open Access Hub', '20m',
 'varies', ls8_c2_l2_prod_path, 'N/A'],
## Sentinel-2
[sntnl2_l2a_product_type, s2_ard_scene_prod_name, 'from Copernicus Open Access Hub', '10-60m',
 'varies', s2_ard_scene_prod_path, 'N/A'],
[sntnl2_l2a_product_type, s2_l2a_aws_cog_prod_name, 'Sentinel-2 L2A Cloud-Optimized GeoTIFFs at s3://sentinel-cogs/sentinel-s2-l2a-cogs', '10-60m',
 'varies', s2_l2a_aws_cog_prod_path, 'N/A'],
## JERS-1
[jers1_sar_hh_product_type, jers_sar_mosaic_prod_name, 'N/A', '25m', 
 'EPSG:4326', jers_sar_mosaic_prod_path,
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml'],
## Copernicus Global Land Cover
[copernicus_glc_product_type, copernicus_lc100_prod_name, 'N/A', '100m', 
 'EPSG:4326', copernicus_lc100_prod_path,
 'N/A'],
## Black Marble Night Lights
[black_marble_night_lights_product_type, black_marble_night_lights_prod_name, 'N/A', '450m', 
 'EPSG:4326', black_marble_night_lights_prod_path,
 'N/A'],
])
