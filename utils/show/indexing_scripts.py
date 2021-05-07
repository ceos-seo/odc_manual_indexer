from common import *

# Columns (indexing scripts) #
# Define columns as vars for autocomplete (convenient, avoids typos).
idx_scr_df_col_pth_fmt = 'IdxScrPathFormat'
idx_scr_df_col_origin = 'IdxScrOrigin'
idx_scr_df_col_prds = 'IdxScrProds'
idx_scr_df_col_sup_ds_origs = 'IdxScrSupDsOrigins'
idx_scr_cols = [idx_scr_df_col_pth_fmt, idx_scr_df_col_origin,
                idx_scr_df_col_prds, idx_scr_df_col_sup_ds_origs]
# End Columns #

# Path-Format Parameter Descriptions #
fmt_desc_s3_bkt = '<bucket (S3 bucket name)>'
fmt_desc_s3_pth = '<path (path in bucket in which to recursively search for Data Cube datasets to index)>'
fmt_desc_suffix = '<string (The file suffix of dataset metadata documents)>'
# End Path-Format Parameter Descriptions #

# File Path Variables #
idx_scr_dir_name = 'index_scripts'

# Path in the container vs path in the repo.
## Landsat
ls_c1_idx_scr_dir_container = f'{ls_c1_dir_container}/{idx_scr_dir_name}'
ls_c1_idx_scr_dir = f'{ls_c1_dir}/{idx_scr_dir_name}'
ls_c2_idx_scr_dir_container = f'{ls_c2_dir_container}/{idx_scr_dir_name}'
ls_c2_idx_scr_dir = f'{ls_c2_dir}/{idx_scr_dir_name}'
## Sentinel-1
s1_idx_scr_dir_container = f'{s1_dir_container}/{idx_scr_dir_name}'
s1_idx_scr_dir = f'{s1_dir}/{idx_scr_dir_name}'
## Sentinel-2
s2_l2a_idx_scr_dir_container = f'{s2_l2a_dir_container}/{idx_scr_dir_name}'
s2_l2a_idx_scr_dir = f'{s2_l2a_dir}/{idx_scr_dir_name}'
## Copernicus Global Land Cover
ls_c1_idx_scr_dir_container = f'{copernicus_glc_dir_container}/{idx_scr_dir_name}'
copernicus_glc_idx_scr_dir = f'{copernicus_glc_dir}/{idx_scr_dir_name}'

# Script names
## Landsat
ls5_c1_l2_idx_scr_name = 'ls5_public_bucket.py'
deafrica_data_extents = '--lat1=-36 --lat2=38 --lon1=-18 --lon2=52'
ls7_c1_l2_idx_scr_name = 'ls7_public_bucket.py'
ls8_c1_l2_idx_scr_name = 'ls8_public_bucket.py'
ls5_c2_l2_idx_scr_name = 'ls5_l2_c2_public_bucket.py'
ls7_c2_l2_idx_scr_name = 'ls7_l2_c2_public_bucket.py'
ls8_c2_l2_idx_scr_name = 'ls8_l2_c2_public_bucket.py'
## Sentinel-1
s1_idx_scr_name = 's1_rtc_card4l.py'
s1_data_extents = '--lat1=35 --lat2=39 --lon1=-85 --lon2=-75 --start_date=2017-01-01 --end_date=2019-12-31'
## Sentinel-2
s2_l2a_s3_cog_idx_scr_name = 's2_l2a_aws_cog.py'
## Copernicus Global Land Cover
copernicus_glc_idx_scr_name = 'indexer.py'


# End File Path Variables #

idx_scr_df = pd.DataFrame(
    columns = idx_scr_cols,
    data = [
## Landsat
[# Path-Format
f'{ls_c1_idx_scr_dir}/{ls5_c1_l2_idx_scr_name} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix} {deafrica_data_extents}',
 # Origin
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/old-prep-scripts/ls_public_bucket.py',
 # Products
 ['ls5_usgs_sr_scene'],
 # Supported dataset origin types.
 ['s3']],
[f'{ls_c1_idx_scr_dir}/{ls7_c1_l2_idx_scr_name} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix} {deafrica_data_extents}',
 # Origin
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/old-prep-scripts/ls_public_bucket.py',
 # Products
 ['ls7_usgs_sr_scene'],
 # Supported dataset origin types.
 ['s3']],
[f'{ls_c1_idx_scr_dir}/{ls8_c1_l2_idx_scr_name} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix} {deafrica_data_extents}',
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/old-prep-scripts/ls_public_bucket.py',
 ['ls8_usgs_sr_scene'],
 ['s3']],
[f'{ls_c2_idx_scr_dir}/{ls5_c2_l2_idx_scr_name} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix}',
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/old-prep-scripts/ls_public_bucket.py',
 ['ls5_l2_c2'],
 ['s3']],
[f'{ls_c2_idx_scr_dir}/{ls7_c2_l2_idx_scr_name} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix}',
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/old-prep-scripts/ls_public_bucket.py',
 ['ls7_l2_c2'],
 ['s3']],
[f'{ls_c2_idx_scr_dir}/{ls8_c2_l2_idx_scr_name} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix}',
 f'{ls_c1_idx_scr_dir}/{ls8_c1_l2_idx_scr_name}',
 ['ls8_l2_c2'],
 ['s3']],
## Sentinel-1
[f'{s1_idx_scr_dir}/{s1_idx_scr_name} {fmt_desc_s3_bkt} '\
  f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix} {s1_data_extents}',
  f'{s1_idx_scr_dir}/{s1_idx_scr_name}',
  ['s1_rtc_card4l'],
  ['s3']],
## Sentinel-2
[f'{s2_l2a_idx_scr_dir}/{s2_l2a_s3_cog_idx_scr_name} {fmt_desc_s3_bkt} '\
  f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix}',
  'N/A',
  ['s2_l2a_aws_cog'],
  ['s3']],
## JERS-1
# TODO: Create a JERS-1 indexing script.
## Copernicus Global Land Cover
[f'{copernicus_glc_idx_scr_dir}/{copernicus_glc_idx_scr_name} {fmt_desc_s3_bkt} '\
  f'-p {fmt_desc_s3_pth}',
  'N/A',
  ['copernicus_lc100'],
  ['s3']],
  # e.g. Copernicus/Land_Cover/indexer.py vito.landcover.global --prefix v3.0.1 --lat1 40 --lat2 40 --lon1 -100 --lon2 -80
])


idx_scr_df_exp = idx_scr_df.explode(idx_scr_df_col_prds)
from product import prd_df_col_prd
idx_scr_df_exp.rename(columns={idx_scr_df_col_prds: prd_df_col_prd}, inplace=True)
idx_scr_df_exp[idx_scr_df_col_prds] = idx_scr_df[idx_scr_df_col_prds]
idx_scr_df = idx_scr_df_exp