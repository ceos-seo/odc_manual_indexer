from common import *
from product import *

## Columns (indexing scripts) ##
# Define columns as vars for autocomplete (convenient, avoids typos).
idx_scr_df_col_pth_fmt = 'IdxScrPathFormat'
idx_scr_df_col_origin = 'IdxScrOrigin'
idx_scr_df_col_prds = 'IdxScrProds'
idx_scr_df_col_sup_ds_origs = 'IdxScrSupDsOrigins'
idx_scr_cols = [idx_scr_df_col_pth_fmt, idx_scr_df_col_origin,
                idx_scr_df_col_prds, idx_scr_df_col_sup_ds_origs]
## End Columns ##

## Path-Format Parameter Descriptions ##
## General
fmt_desc_product_name = '<product-name>' 
fmt_desc_product_type = '<product-type>'
fmt_desc_platform_code = '<platform-code>'
fmt_desc_suffix = '<string (The file suffix of dataset metadata documents)>'
### Local Path
fmt_desc_local_path = '<datastore-path>'
### S3
fmt_desc_s3_bkt = '<bucket (S3 bucket name)>'
fmt_desc_s3_pth = '<path (path in bucket in which to recursively search for Data Cube datasets to index)>'
## End Path-Format Parameter Descriptions ##

## File Path Variables ##

### Script Paths ###
## Landsat
landsat_idx_scr_dir = f'{idx_scr_dir}/Landsat'
### Landsat Collection 1
landsat_c1_prod_dir = f'{landsat_idx_scr_dir}/collection_1'
ls5_c1_l2_idx_scr_path = f'{landsat_c1_prod_dir}/ls5_usgs_sr_scene.py'
ls7_c1_l2_idx_scr_path = f'{landsat_c1_prod_dir}/ls7_usgs_sr_scene.py'
ls8_c1_l2_idx_scr_path = f'{landsat_c1_prod_dir}/ls8_usgs_sr_scene.py'
### Landsat Collection 2
landsat_c2_idx_scr_dir = f'{landsat_idx_scr_dir}/collection_2'
ls5_c2_l2_idx_scr_path = f'{landsat_c2_idx_scr_dir}/ls5_l2_c2.py'
ls7_c2_l2_idx_scr_path = f'{landsat_c2_idx_scr_dir}/ls7_l2_c2.py'
ls8_c2_l2_idx_scr_path = f'{landsat_c2_idx_scr_dir}/ls8_l2_c2.py'
## Sentinel-1
sentinel_1_idx_scr_dir = f'{idx_scr_dir}/Sentinel-1'
s1_idx_scr_path = f'{sentinel_1_idx_scr_dir}/s1_rtc_card4l.py'
## Sentinel-2
sentinel_2_idx_scr_dir = f'{idx_scr_dir}/Sentinel-2'
s2_l2a_s3_cog_idx_scr_path = f'{sentinel_2_idx_scr_dir}/s2_l2a_aws_cog.py'
## Copernicus Global Land Cover
copernicus_glc_idx_scr_path = f'{idx_scr_dir}/copernicus_lc100.py'
## Black Marble Night Lights
black_marble_night_lights_idx_scr_path = f'{idx_scr_dir}/black_marble_night_lights.py'
### End Script Paths ###

## End File Path Variables ##

## Data Extents ##

s1_data_extents = '--lat1=35 --lat2=39 --lon1=-85 --lon2=-75 --start_date=2017-01-01 --end_date=2019-12-31'
deafrica_data_extents = '--lat1=-36 --lat2=38 --lon1=-18 --lon2=52'

## End Data Extents ##

idx_scr_df = pd.DataFrame(
    columns = idx_scr_cols,
    data = [
## Landsat
[# Path-Format
f'{ls5_c1_l2_idx_scr_path} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix} {deafrica_data_extents}',
 # Origin
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/old-prep-scripts/ls_public_bucket.py',
 # Products
 [ls5_c1_l2_prod_name],
 # Supported dataset origin types.
 ['s3']],
[f'{ls7_c1_l2_idx_scr_path} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix} {deafrica_data_extents}',
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/old-prep-scripts/ls_public_bucket.py',
 [ls7_c1_l2_prod_name],
 ['s3']],
[f'{ls8_c1_l2_idx_scr_path} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix} {deafrica_data_extents}',
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/old-prep-scripts/ls_public_bucket.py',
 [ls8_c1_l2_prod_name],
 ['s3']],
[f'{ls5_c2_l2_idx_scr_path} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix}',
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/old-prep-scripts/ls_public_bucket.py',
 [ls5_c2_l2_prod_name],
 ['s3']],
[f'{ls7_c2_l2_idx_scr_path} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix}',
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/old-prep-scripts/ls_public_bucket.py',
 [ls7_c2_l2_prod_name],
 ['s3']],
[f'{ls8_c2_l2_idx_scr_path} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix}',
 f'{ls8_c1_l2_idx_scr_path}',
 [ls8_c2_l2_prod_name],
 ['s3']],
## Sentinel-1
[f'{s1_idx_scr_path} {fmt_desc_s3_bkt} '\
  f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix} {s1_data_extents}',
  f'{s1_idx_scr_path}',
  [s1_rtc_card4l_prod_name],
  ['s3']],
## Sentinel-2
[f'{s2_l2a_s3_cog_idx_scr_path} {fmt_desc_s3_bkt} '\
  f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix}',
  'N/A',
  [s2_l2a_aws_cog_prod_name],
  ['s3']],
## JERS-1
# TODO: Create a JERS-1 indexing script.
## Copernicus Global Land Cover

[f'{copernicus_glc_idx_scr_path} {fmt_desc_s3_bkt} '\
  f'-p {fmt_desc_s3_pth}',
  'N/A',
  [copernicus_lc100_prod_name],
  ['s3']],
  # e.g. Copernicus/Land_Cover/indexer.py vito.landcover.global --prefix v3.0.1 --lat1 40 --lat2 40 --lon1 -100 --lon2 -80
## Black Marble Night Lights
[f'{black_marble_night_lights_idx_scr_path} {fmt_desc_s3_bkt} '\
  f'-p {fmt_desc_s3_pth}',
  'N/A',
  [black_marble_night_lights_prod_name],
  ['s3']],
])


idx_scr_df_exp = idx_scr_df.explode(idx_scr_df_col_prds)
from product import prd_df_col_prd
idx_scr_df_exp.rename(columns={idx_scr_df_col_prds: prd_df_col_prd}, inplace=True)
idx_scr_df_exp[idx_scr_df_col_prds] = idx_scr_df[idx_scr_df_col_prds]
idx_scr_df = idx_scr_df_exp