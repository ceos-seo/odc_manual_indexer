"""
This file contains the implementations of the commands in show.py.

`click.Command` functions cannot be called directly in Python code.
We can use `click.Context` for this, but this method is more convenient.
"""
import sys
import re
import pandas as pd
import numpy as np

# Set pandas to show all columns in dataframes.
pd.options.display.width = 0
pd.options.display.max_colwidth = None
pd.options.mode.chained_assignment = None  # default='warn'

from common import *

from product import *

from datastore import *

from indexing_scripts import *

# Obtain Merged Datasets in Different Formats #
# Inner join to only show full rows of product-indexing script-dataset combinations.
# In other words, only complete rows that contain a means of indexing data are included.
inner_merged_df = prd_df\
    .merge(idx_scr_df,
           on=prd_df_col_prd)\
    .merge(odc_ds_df,
           on=prd_df_col_prd)

# Left merge the tables on product name to have 1 row per product.
# This can show more information related to missing items, 
# such as products with no indexing scripts or no datasets.
outer_merged_df = prd_df\
    .merge(idx_scr_df,
           on=prd_df_col_prd, how='outer')\
    .merge(odc_ds_df,
           on=prd_df_col_prd, how='outer')
# End Obtain Merged Datasets in Different Formats #

format_info_str = 'Note that text enclosed in square brackets '\
                  'in calling formats denotes something optional.'

show_all_rows_desc = 'Whether to show rows for all products. By default, only rows '\
                     'for products with an indexing script and 1 or more datasets are shown.'
show_all_rows_default = False

show_prd_origin_desc = 'Whether to show the product definition origin.'
show_origin_default = False

opt_list_default = []

def show_product_types_impl(show_all_rows=show_all_rows_default):
    return show_columns_impl(cols=[col_product_type], show_all_rows=show_all_rows)

def show_columns_impl(product_types=opt_list_default, products=opt_list_default, 
                      cols=opt_list_default, show_all_rows=show_all_rows_default):
    show_cols_df = inner_merged_df if not show_all_rows else outer_merged_df
    # Rows with no dataset path must be discarded unless `show_all_rows`.
    show_cols_df = show_cols_df[show_cols_df['DsPath'] != 'N/A'].reset_index(drop=True) if not show_all_rows else show_cols_df
    # Select specified product types.
    show_cols_df = show_cols_df[show_cols_df[col_product_type].isin(product_types)] if len(product_types) > 0 else show_cols_df
    # Select specified products.
    show_cols_df = show_cols_df[show_cols_df[prd_df_col_prd].isin(products)] if len(products) > 0 else show_cols_df
    # Select specified columns.
    show_cols_df = show_cols_df[cols] if len(cols) > 0 else show_cols_df
    return show_cols_df.dropna(how='all') # drop rows will no data.

def show_data_stores_impl(product_types=opt_list_default, products=opt_list_default, 
                          show_all_rows=show_all_rows_default):
    return show_columns_impl(product_types=product_types, products=products, \
                             cols=odc_ds_cols, show_all_rows=show_all_rows)

def show_indexing_impl(product_types=opt_list_default, products=opt_list_default, 
                       show_all_rows=show_all_rows_default):
    cols_to_load = [prd_df_col_prd, idx_scr_df_col_pth_fmt, \
                    odc_ds_df_col_pth, idx_scr_df_col_sup_ds_origs, odc_ds_df_col_suffix]
    df = show_columns_impl(product_types=product_types, products=products, \
                           cols=cols_to_load, show_all_rows=show_all_rows)
    
    # Create an indexing command column from information about an indexing script and datastore.
    def get_formatted_idx_cmd(idx_scr_df_col_pth_fmt, odc_ds_df_col_pth, 
                              idx_scr_df_col_sup_ds_origs, odc_ds_df_col_suffix,
                              idx_scr_df_col_prd):
        if not isinstance(odc_ds_df_col_pth, str) and np.isnan(odc_ds_df_col_pth):
            return '' # No dataset path. No indexing command.
        # 1. Determine datastore origin type (e.g. local, S3).
        patterns = {'scheme_path_pattern': re.compile('(.*)://(.*)'),
                    'file_path_pattern': re.compile('(/.*)')}
        for pattern_name, pattern in patterns.items():
            match = pattern.search(odc_ds_df_col_pth)
            if match is not None:
                if pattern_name == 'scheme_path_pattern':
                    scheme = match.group(1)
                    path = match.group(2)
                    if scheme == 's3':
                        bucket_path_match = re.search('(.*?)/(.*)', path)
                        bucket = bucket_path_match.group(1)
                        bucket_path = bucket_path_match.group(2)
                if pattern_name == 'file_path_pattern':
                    scheme = 'local_file'
                    path = match.group(1)
                break
        if match is None:
            return '' # No pattern matched. Unrecognized origin. No indexing command.
        
        # 2. Determine if the indexing script supports this datastore origin type.
        if not isinstance(idx_scr_df_col_sup_ds_origs, list) or scheme not in idx_scr_df_col_sup_ds_origs:
            return '' # No scheme or scheme not supported by this indexing script. No indexing command.

        # 3. If this origin type is supported, determine the needed elements 
        # (e.g. bucket, path, suffix) and check if they are present in the data source info,
        # extracting them when found.
        if scheme == 's3':
            idx_scr_df_col_pth_fmt = idx_scr_df_col_pth_fmt.replace(fmt_desc_s3_bkt, bucket)
            idx_scr_df_col_pth_fmt = idx_scr_df_col_pth_fmt.replace(fmt_desc_s3_pth, bucket_path)
            idx_scr_df_col_pth_fmt = idx_scr_df_col_pth_fmt.replace(fmt_desc_suffix, odc_ds_df_col_suffix)
        if scheme == 'local_file':
            idx_scr_df_col_pth_fmt = idx_scr_df_col_pth_fmt.replace(fmt_desc_product_name, idx_scr_df_col_prd)
        return idx_scr_df_col_pth_fmt

    df['IdxCmdFmt'] = \
        df.apply(lambda row: get_formatted_idx_cmd(row[idx_scr_df_col_pth_fmt], 
                                                   row[odc_ds_df_col_pth],
                                                   row[idx_scr_df_col_sup_ds_origs],
                                                   row[odc_ds_df_col_suffix],
                                                   row[prd_df_col_prd]), axis=1)
    cols_to_show = [prd_df_col_prd, 'IdxCmdFmt', odc_ds_df_col_pth]
    df = df[cols_to_show]
    # Rows with an empty `IdxCmdFmt` cell must be discarded unless `show_all_rows`.
    return df[df['IdxCmdFmt'] != ''].reset_index(drop=True) if not show_all_rows else df

def show_products_impl(product_types=opt_list_default, products=opt_list_default, 
                       show_all_rows=show_all_rows_default, show_origin=show_origin_default):
    cols_to_show = [prd_col for prd_col in prd_cols if prd_col != prd_df_col_origin] \
                   if not show_origin else prd_cols
    return show_columns_impl(product_types=product_types, products=products, 
                             cols=cols_to_show, show_all_rows=show_all_rows)

def show_indexing_scripts_impl(product_types=opt_list_default, products=opt_list_default, 
                               show_all_rows=show_all_rows_default, show_origin=show_origin_default):
    cols_to_show = [idx_scr_col for idx_scr_col in idx_scr_cols if idx_scr_col != idx_scr_df_col_origin] \
                   if not show_origin else idx_scr_cols
    return show_columns_impl(product_types=product_types, products=products, \
                             cols=cols_to_show, show_all_rows=show_all_rows)