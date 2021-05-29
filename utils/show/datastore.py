import pandas as pd

from common import *
from product import *

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
## Landsat
['s3://deafrica-data/usgs/c1/l5',
 'Landsat 5 data for Africa (from GA - minimize queries)', 
 [ls5_c1_l2_prod_name],
  '.xml'],
['s3://deafrica-data/usgs/c1/l7',
 'Landsat 7 data for Africa (from GA - minimize queries)', 
 [ls7_c1_l2_prod_name],
  '.xml'],
['s3://deafrica-data/usgs/c1/l8',
 'Landsat 8 data for Africa (from GA - minimize queries)', 
 [ls8_c1_l2_prod_name],
 '.xml'],
['s3://usgs-landsat/collection02/level-2/standard/tm',
 'USGS-hosted Landsat 5 C2 L2 Data (World, Requester Pays)',
 [ls5_c2_l2_prod_name],
 'MTL.xml'], # TODO: This data store is also STAC-compliant (`[...]_stac.json`).
['s3://usgs-landsat/collection02/level-2/standard/etm',
 'USGS-hosted Landsat 7 C2 L2 Data (World, Requester Pays)',
 [ls7_c2_l2_prod_name],
 'MTL.xml'], # TODO: This data store is also STAC-compliant (`[...]_stac.json`).
['s3://usgs-landsat/collection02/level-2/standard/oli-tirs',
 'USGS-hosted Landsat 8 C2 L2 Data (World, Requester Pays)',
 [ls8_c2_l2_prod_name],
 'MTL.xml'], # TODO: This data store is also STAC-compliant (`[...]_stac.json`).
## Sentinel-1
### Sentinel-1 RTC eu-central-1
['s3://sh.s1-card4l.eu-central-1.nasa/order_2021-03-17T15:13:58Z/s1_rtc',
 'Sentinel-1 RTC Cloud-Optimized GeoTIFFs', 
 [s1_rtc_card4l_prod_name],
 'metadata.json'],
### Sentinel-1 RTC us-east-1
 ['s3://va-s3-requesterpays/order_2021-03-17T15:13:58Z/s1_rtc',
  'Sentinel-1 RTC Cloud-Optimized GeoTIFFs', 
 [s1_rtc_card4l_prod_name],
 'metadata.json'],
## Sentinel-2
['s3://sentinel-cogs/sentinel-s2-l2a-cogs',
 'Sentinel-2 L2A Cloud-Optimized GeoTIFFs', 
 [s2_l2a_aws_cog_prod_name],
 'L2A.json'],
## Copernicus Global Land Cover
['s3://vito.landcover.global/v3.0.1',
 'Copernicus annual Global Land Cover GeoTIFFs', 
 [copernicus_lc100_prod_name],
 ''],
## Drones ##
### WebODM DJI Mavic Mini
['N/A',
 'WebODM DJI MavicMini (DEM, RGBA)', 
 [WebODM_MavicMini_prod_name, WebODM_MavicMini_RGBA_prod_name],
 ''],
## End Drones ##
 ])

odc_ds_df_exp = odc_ds_df.explode(odc_ds_df_col_prds)
from product import prd_df_col_prd
odc_ds_df_exp.rename(columns={odc_ds_df_col_prds: prd_df_col_prd}, inplace=True)
odc_ds_df_exp[odc_ds_df_col_prds] = odc_ds_df[odc_ds_df_col_prds]
odc_ds_df = odc_ds_df_exp