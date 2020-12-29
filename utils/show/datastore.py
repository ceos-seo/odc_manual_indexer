from common import *

# Columns (remote data stores):
# Define columns as vars for autocomplete (convenient, avoids typos).
odc_ds_df_col_pth = 'DsPath'
odc_ds_df_col_desc = 'DsDesc'
odc_ds_df_col_prds = 'DsProds'
odc_ds_df_col_suffix = 'DsMtdtSufx'
odc_ds_cols = [odc_ds_df_col_pth, odc_ds_df_col_desc,
               odc_ds_df_col_prds, odc_ds_df_col_suffix]

odc_ds_df = pd.DataFrame(
    columns=odc_ds_cols,
    data=[
['s3://sentinel-s2-l1c/tiles',
 'AWS Open Data Sentinel 2 Level 1C (Requester Pays)', 
 [],
 ''], # TODO: There is no prod def or indexing script for this.
['s3://deafrica-data/usgs/c1/l7',
 'Landsat 7 data for Africa (from GA - minimize queries)', 
 ['ls7_usgs_sr_scene'],
  '.xml'],
['s3://deafrica-data/usgs/c1/l8',
 'Landsat 8 data for Africa (from GA - minimize queries)', 
 ['ls8_usgs_sr_scene'],
 '.xml'],
['s3://usgs-landsat/collection02/level-2/standard/oli-tirs',
 'USGS-hosted Landsat 8 C2 L2 Data (World)',
 ['ls8_l2_c2'],
 'MTL.xml'] # TODO: This data store is also STAC-compliant (`[...]_stac.json`).
 ])

odc_ds_df_exp = odc_ds_df.explode(odc_ds_df_col_prds)
from product import prd_df_col_prd
odc_ds_df_exp.rename(columns={odc_ds_df_col_prds: prd_df_col_prd}, inplace=True)
odc_ds_df_exp[odc_ds_df_col_prds] = odc_ds_df[odc_ds_df_col_prds]
odc_ds_df = odc_ds_df_exp