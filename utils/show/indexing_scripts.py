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
ls_c1_idx_scr_dir_container = f'{ls_c1_dir_container}/{idx_scr_dir_name}'
ls_c1_idx_scr_dir = f'{ls_c1_dir}/{idx_scr_dir_name}'
ls_c2_idx_scr_dir_container = f'{ls_c2_dir_container}/{idx_scr_dir_name}'
ls_c2_idx_scr_dir = f'{ls_c2_dir}/{idx_scr_dir_name}'

ls7_c1_l2_idx_scr_name = 'ls7_public_bucket.py'
ls8_c1_l2_idx_scr_name = 'ls8_public_bucket.py'
ls5_c2_l2_idx_scr_name = 'ls5_l2_c2_public_bucket.py'
ls7_c2_l2_idx_scr_name = 'ls7_l2_c2_public_bucket.py'
ls8_c2_l2_idx_scr_name = 'ls8_l2_c2_public_bucket.py'
# End File Path Variables #

idx_scr_df = pd.DataFrame(
    columns = idx_scr_cols,
    data = [
[# Path-Format
 f'{ls_c1_idx_scr_dir}/{ls7_c1_l2_idx_scr_name} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix}',
 # Origin
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/old-prep-scripts/ls_public_bucket.py',
 # Products
 ['ls7_usgs_sr_scene'],
 # Supported dataset origin types.
 ['s3']],
[ 
 f'{ls_c1_idx_scr_dir}/{ls8_c1_l2_idx_scr_name} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix}',
 
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/old-prep-scripts/ls_public_bucket.py',
 ['ls8_usgs_sr_scene'],
 ['s3']],
 [f'{ls_c2_idx_scr_dir}/{ls8_c1_l2_idx_scr_name} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix}',
 
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/old-prep-scripts/ls_public_bucket.py',
 ['ls5_l2_c2'],
 ['s3']],
[f'{ls_c2_idx_scr_dir}/{ls5_c2_l2_idx_scr_name} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix}',
 
 'https://github.com/opendatacube/datacube-dataset-config/blob/master/old-prep-scripts/ls_public_bucket.py',
 ['ls7_l2_c2'],
 ['s3']],
[f'{ls_c2_idx_scr_dir}/{ls8_c2_l2_idx_scr_name} {fmt_desc_s3_bkt} '\
 f'-p {fmt_desc_s3_pth} --suffix={fmt_desc_suffix}',
 
 f'{ls_c1_idx_scr_dir}/{ls8_c1_l2_idx_scr_name}',
 ['ls8_l2_c2'],
 ['s3']]])

idx_scr_df_exp = idx_scr_df.explode(idx_scr_df_col_prds)
from product import prd_df_col_prd
idx_scr_df_exp.rename(columns={idx_scr_df_col_prds: prd_df_col_prd}, inplace=True)
idx_scr_df_exp[idx_scr_df_col_prds] = idx_scr_df[idx_scr_df_col_prds]
idx_scr_df = idx_scr_df_exp