import click

@click.command("data-cog-stac-s3-pipeline")
@click.option(
    "--extension",
    default=".tif",
    type=str,
    help="Extension of files to work on.",
)
# @click.option(
#     "--default-date",
#     default=None,
#     type=str,
#     help="A date for the file. Todo: work out how to make this magic.",
# )
# @click.option(
#     "--platform",
#     type=str,
#     required=True,
#     help="Platform name for the product",
# )
# @click.option(
#     "--band-name",
#     type=str,
#     required=True,
#     help="Band name for the asset/measurement",
# )
# @click.option(
#     "--band-type",
#     type=str,
#     default="uint8",
#     help="Band date type for the band",
# )
# @click.option(
#     "--band-nodata",
#     type=float,
#     default=0,
#     help="Band data type for the band",
# )
# @click.option(
#     "--create-product/--no-create-product",
#     is_flag=True,
#     default=True,
#     help=("Creates a basic EO3 product definition"),
# )
@click.option(
    "--cog-convert/--no-cog-convert",
    is_flag=True,
    default=False,
    help=("Converts files to Cloud Optimised GeoTIFFs"),
)
# Name of the ODC product the data maps to.
@click.argument("product",  type=str, required=True)
# The directory the data resides in.
@click.argument("directory", type=str, nargs=1)
# The S3 path to copy the data in `directory` to (maintain structure).
@click.argument("s3_uri", type=str, nargs=1)
def cli(
    extension,
    # default_date,
    # platform,
    # create_product,
    # band_name,
    # band_type,
    # band_nodata,
    cog_convert,
    product,
    directory,
    s3_uri,
):
    from data_prep import data_to_cog_stac_odc_meta
    data_to_cog_stac_odc_meta(extension, cog_convert, product, directory, s3_uri)
    from utils.upload.s3_upload import s3_upload
    s3_upload(directory, s3_uri)


if __name__ == "__main__":
    cli()