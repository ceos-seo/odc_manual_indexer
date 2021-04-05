import pandas as pd

col_product_type = 'Product Type'
## Landsat
ls5_c1_l2_product_type = 'Landsat 5 Collection 1 Level 2 (SR)'
ls7_c1_l2_product_type = 'Landsat 7 Collection 1 Level 2 (SR)'
ls8_c1_l2_product_type = 'Landsat 8 Collection 1 Level 2 (SR)'
ls5_c2_l2_product_type = 'Landsat 5 Collection 2 Level 2 (SR)'
ls7_c2_l2_product_type = 'Landsat 7 Collection 2 Level 2 (SR)'
ls8_c2_l2_product_type = 'Landsat 8 Collection 2 Level 2 (SR)'
# Sentinel-1
sntnl1_product_type = 'Sentinel-1'
## Sentinel-2
sntnl2_l1c_product_type = 'Sentinel-2 Level 1C'
sntnl2_l2a_product_type = 'Sentinel-2 Level 2A (Copernicus Format)'
## JERS-1
jers1_sar_hh_product_type = 'JERS-1 SAR (HH)'

# File Path Variables #
dataset_dir = 'datasets'

## Landsat
ls_c1_dir_container = 'Landsat/collection_1'
ls_c1_dir = f'{dataset_dir}/{ls_c1_dir_container}'
ls_c2_dir_container = 'Landsat/collection_2'
ls_c2_dir = f'{dataset_dir}/{ls_c2_dir_container}'
## Sentinel-1
s1_dir_container = 'Sentinel-1'
s1_dir = f'{dataset_dir}/{s1_dir_container}'
## Sentinel-2
s2_l2a_dir_container = 'Sentinel-2/L2A'
s2_l2a_dir = f'{dataset_dir}/{s2_l2a_dir_container}'

# End File Path Variables #