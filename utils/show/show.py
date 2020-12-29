import click
import ast

from show_impl import *

class PythonLiteralOption(click.Option):
    def type_cast_value(self, ctx, value):
        try:
            return ast.literal_eval(value)
        except:
            raise click.BadParameter(value)

@click.group(help=f"""
Columns:\n
{odc_ds_df_col_pth}: The path to the dataset (e.g. an S3 bucket-path).\n
{odc_ds_df_col_desc}: A description of the dataset.\n
{odc_ds_df_col_prds}: The products the dataset is compatible with.\n
{odc_ds_df_col_suffix}: The file suffix of the metadata files for this dataset.\n
{idx_scr_df_col_pth_fmt}: The calling format for the script.\n
{idx_scr_df_col_origin}: The origin of the script (what it is derived from).\n
{idx_scr_df_col_prds}: The products the indexing script is compatible with.\n
{idx_scr_df_col_sup_ds_origs}: The supported datastore origin types for the indexing script.\n
{prd_df_col_prd}: The name of the product.\n
{prd_df_col_descr}: Description of the product.\n
{prd_df_col_res}: The resolution of the product \n
{prd_df_col_proj}: The projection of the product.\n
{prd_df_col_prd_def_path}: The container path to the product definition file.\n
{prd_df_col_origin}: The origin of the product definition (what it is derived from).\n
""")
def cli():
    pass

@cli.command('show-product-types', help=f"""
Show currently recorded product types.

Some examples of product types include Landsat 8 Collection 1 Level 2 products
or Sentinel-2 Level 2A products.

{format_info_str}

Calling format: show-product-types [<product_type_1> <product_type_2> ...] [-p "['product1', 'product2', ...]"] [-c "['col1', 'col2', ...]"] [-a] \n
Example usage: show-columns "Sentinel-2 Level 2A (Copernicus Format)" "Landsat 8 Collection 1 Level 2 (SR)" -p "['ls8_usgs_sr_scene', 's2_ard_scene']" -c "['ProdName', 'ProdRes']" -a
""")
@click.option('--show_all_rows', '-a', is_flag=True, help=show_all_rows_desc, default=show_all_rows_default)
def show_product_types(show_all_rows):
    print(show_product_types_impl(show_all_rows).to_markdown(index=False, tablefmt='simple'))

@cli.command('show-columns', help=f"""\
Show selected columns of the data (see `show.py --help`).

{format_info_str}

Calling format: show-columns [<product_type_1> <product_type_2> ...] [-p "['product1', 'product2', ...]"] [-c "['col1', 'col2', ...]"] [-a] \n
Example usage: show-columns "Landsat 8 Collection 1 Level 2 (SR)" -p "['ls8_usgs_sr_scene']" -c "['ProdName', 'ProdRes']" -a
""")
@click.argument('product-types', nargs=-1)
@click.option('--products', '-p', cls=PythonLiteralOption, default=str(opt_list_default))
@click.option('--cols', '-c', cls=PythonLiteralOption, default=str(opt_list_default))
@click.option('--show_all_rows', '-a', is_flag=True, help=show_all_rows_desc, default=show_all_rows_default)
def show_columns(product_types, products, cols, show_all_rows):
    print(show_columns_impl(product_types, products, cols, show_all_rows).to_markdown(index=False, tablefmt='simple'))

@cli.command('show-data-stores', help=f"""\
Show currently recorded datastores.

{format_info_str}

Calling format: show-data-stores [<product_type_1> <product_type_2> ...] [-p "['product1', 'product2', ...]"] [-a] \n
Example usage: show-data-stores -p "['ls8_usgs_sr_scene']"
""")
@click.argument('product-types', nargs=-1)
@click.option('--products', '-p', cls=PythonLiteralOption, default=str(opt_list_default))
@click.option('--show_all_rows', '-a', is_flag=True, help=show_all_rows_desc, default=show_all_rows_default)
def show_data_stores(product_types, products, show_all_rows):
    print(show_data_stores_impl(product_types, products, show_all_rows).to_markdown(index=False, tablefmt='simple'))

@cli.command('show-indexing', help=f"""\
Show currently recorded products and how to index them.

{format_info_str}

Calling format: show-indexing [<product_type_1> <product_type_2> ...] [-p "['product1', 'product2', ...]"] [-a] \n
Example usage: show-indexing -p "['ls8_usgs_sr_scene']"
""")
@click.argument('product-types', nargs=-1)
@click.option('--products', '-p', cls=PythonLiteralOption, default=str(opt_list_default))
@click.option('--show_all_rows', '-a', is_flag=True, help=show_all_rows_desc, default=show_all_rows_default)
def show_indexing(product_types, products, show_all_rows):
    print(show_indexing_impl(product_types, products, show_all_rows).to_markdown(index=False, tablefmt='simple'))

@cli.command('show-products', help=f"""\
Show the currently recorded products.

{format_info_str}

Calling format: show-products [<product_type_1> <product_type_2> ...] [-p "['product1', 'product2', ...]"] [-a] [-o] \n
Example usage: show-products -p "['s2_ard_scene']" -a
""")
@click.argument('product-types', nargs=-1)
@click.option('--products', '-p', cls=PythonLiteralOption, default=str(opt_list_default))
@click.option('--show_all_rows', '-a', is_flag=True, help=show_all_rows_desc, default=show_all_rows_default)
@click.option('--show_origin', '-o', is_flag=True, help=show_prd_origin_desc, default=show_all_rows_default)
def show_products(product_types, products, show_all_rows, show_origin):
    print(show_products_impl(product_types, products, show_all_rows, show_origin).to_markdown(index=False, tablefmt='simple'))

@cli.command('show-idx-scr', help=f"""\
Show the indexing scripts.

{format_info_str}

Calling format: show-idx-scr [<product_type_1> <product_type_2> ...] [-p "['product1', 'product2', ...]"] [-a] [-o] \n
Example usage: show-idx-scr -p "['s2_ard_scene']" -a
""")
@click.argument('product-types', nargs=-1)
@click.option('--products', '-p', cls=PythonLiteralOption, default=str(opt_list_default))
@click.option('--show_all_rows', '-a', is_flag=True, help=show_all_rows_desc, default=show_all_rows_default)
@click.option('--show_origin', '-o', is_flag=True, help=show_prd_origin_desc, default=show_all_rows_default)
def show_indexing_scripts(product_types, products, show_all_rows, show_origin):
    print(show_indexing_scripts_impl(product_types, products, show_all_rows, show_origin).to_markdown(index=False, tablefmt='simple'))

def show_datastores():
    pass

if __name__ == "__main__":
    cli()



