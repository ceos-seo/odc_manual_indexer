import click

@click.command("data-cog-stac-s3-pipeline")
@click.option(
    "--extension",
    default=".tif",
    type=str,
    help="The extension of the raster files for this dataset (usually `.tif`).",
)
@click.option(
    "--cog-convert/--no-cog-convert",
    is_flag=True,
    default=False,
    help=("Converts files to Cloud Optimised GeoTIFFs"),
)
@click.option(
    "--create-metadata",
    is_flag=True,
    default=False,
    help="Create STAC and ODC metadata files for scenes to allow indexing",
)
@click.option(
    "--upload",
    is_flag=True,
    default=False,
    help=("Indexes the data after it is uploaded to S3"),
)
@click.option(
    "--index",
    is_flag=True,
    default=False,
    help=("Indexes the data after it is uploaded to S3"),
)
@click.argument("product",  type=str, required=True)
@click.argument("directory", type=str, nargs=1)
@click.argument("s3_uri", type=str, nargs=1)
@click.argument("s3_region", type=str, nargs=1)
def cli(
    extension,
    cog_convert,
    create_metadata,
    upload,
    index,
    product,
    directory,
    s3_uri,
    s3_region
):
    """
    Create STAC and ODC metadata files for scenes for a product.
    Convert TIFFs to COGs.
    Upload the data to S3.
    Index the data to the datacube.

    product: str
    
        Name of the ODC product the data maps to (e.g. black_marble_night_lights).

    directory: str

        The path to the directory containing the data.

    s3_uri: str
    
        The S3 path to copy the data to, excluding the scheme. 
        For the bucket `mybucket` and prefix `mydata`, this should be 
        `mybucket/mydata`, not `s3://mybucket/mydata`.
    
    s3_region: str

        The AWS region the bucket is in (e.g. us-west-2).
    
    """

    s3_uri_w_scheme = f's3://{s3_uri}'
    from data_prep import data_to_cog_stac_odc_meta
    if create_metadata:
        data_to_cog_stac_odc_meta(extension, cog_convert, product, directory, s3_uri)
    from utils.upload.s3_upload import s3_upload
    if upload:
        s3_upload(directory, s3_uri_w_scheme)
    from utils.index.s3_to_dc import s3_to_dc
    if index:
        s3_to_dc(s3_uri, s3_region, product)


if __name__ == "__main__":
    cli()