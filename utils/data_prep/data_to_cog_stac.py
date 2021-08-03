#!/usr/bin/env python

"""
Utility for converting GeoTIFFs in a directory tree to COGs.
Modified from here: https://github.com/opendatacube/datacube-stac-example/blob/master/stac-simple.py
"""

import datetime
import json
import pathlib
from utils.get_geo_ref_points import get_geo_ref_points_tiff_path
import uuid
import click
# import jinja2
# import pystac
import rasterio

from odc.index.stac import stac_transform
from pyproj import Transformer
from joblib import Parallel, delayed
from tqdm import tqdm
from rio_cogeo.cogeo import cog_translate, cog_validate
from rio_cogeo.profiles import cog_profiles
from osgeo import osr

output_profile = cog_profiles.get("deflate")
# output_profile.update(dict(nodata=0), crs="epsg:28355")
output_profile.update(crs="epsg:4326")

# stac_template = jinja2.Template(
# """
# name: {{platform}}
# description: Auto-generated product example for {{platform}}
# metadata_type: eo3

# metadata:
# product:
#     name: {{platform}}

# measurements:
# - name: '{{band_name}}'
# units: '1'
# dtype: '{{band_type}}'
# nodata: {{band_nodata}}
# ...
# """
# )

# This assumes the filename contains the datetime.
# def get_datetime(raster):
#     file_name = raster.stem
#     date_string = file_name.split("_")[3]
#     date = datetime.datetime.strptime(date_string, "%Y%m%d%H%M")
#     return date.isoformat() + "Z"


def get_geometry(bbox, from_crs):
    transformer = Transformer.from_crs(from_crs, 4326)
    bbox_lonlat = [
        [bbox.left, bbox.bottom],
        [bbox.left, bbox.top],
        [bbox.right, bbox.top],
        [bbox.right, bbox.bottom],
        [bbox.left, bbox.bottom],
    ]
    geometry = {
        "type": "Polygon",
        "coordinates": [list(transformer.itransform(bbox_lonlat))],
    }
    return geometry, bbox_lonlat


def convert_to_cog(raster, validate=True):
    out_path = str(raster.with_suffix(".tif")).replace(" ", "_")
    assert raster != out_path, "Can't convert to files of the same name"
    cog_translate(raster, out_path, output_profile, quiet=True)
    if validate:
        cog_validate(out_path)
    return pathlib.Path(out_path)


# TODO: Make this work for products with multiple measurements.
# def create_stac(raster, platform, band_name, default_date):
#     transform = None
#     shape = None
#     crs = None

#     with rasterio.open(raster) as dataset:
#         transform = dataset.transform
#         shape = dataset.shape
#         crs = dataset.crs.to_epsg()
#         bounds = dataset.bounds

#     date_string = default_date
#     if not date_string:
#         date_string = get_datetime(raster)
#     geometry, bbox = get_geometry(bounds, crs)
#     stac_dict = {
#         "id": raster.stem.replace(" ", "_"),
#         "type": "Feature",
#         "stac_version": "1.0.0-beta.2",
#         "stac_extensions": [
#             "proj"
#         ],
#         "properties": {"platform": platform, "datetime": date_string, "proj:epsg": crs},
#         "bbox": bbox,
#         "geometry": geometry,
#         "assets": {
#             band_name: {
#                 "title": f"Data file for {band_name}",
#                 "type": "image/tiff; application=geotiff; profile=cloud-optimized",
#                 "roles": ["data"],
#                 "href": raster.stem + raster.suffix,
#                 "proj:shape": shape,
#                 "proj:transform": transform,
#             }
#         },
#     }
#     with open(raster.with_suffix(".json"), "w") as f:
#         json.dump(stac_dict, f, indent=2)

#     with open(raster.with_suffix(".odc-dataset.json"), "w") as f:
#         json.dump(stac_transform(stac_dict), f, indent=2)

#     return None

def create_stac(product, raster):
    transform = None
    shape = None
    epsg_code = None

    with rasterio.open(raster) as dataset:
        transform = dataset.transform
        shape = dataset.shape
        epsg_code = dataset.crs.to_epsg()
        bounds = dataset.bounds
        tags = dataset.tags()
        # Read the data from the metadata
        if product in ['black_marble_night_lights']:
            date_string = tags['ProductionTime']
    # Old code
    # date_string = default_date
    # if not date_string:
        # date_string = get_datetime(raster)

    # Read information about this product from its definition file.
    import os
    WORKDIR = os.environ['WORKDIR']
    prod_def_paths = {
        'black_marble_night_lights': f'{WORKDIR}/prod_defs/black_marble_night_lights.yaml'}
    import yaml
    # print(f'prod_def_paths[{product}]: {prod_def_paths[product]}')
    with open(prod_def_paths[product], 'r') as prod_def_yaml_file:
        prod_def_info = yaml.safe_load(prod_def_yaml_file)
    # print(f'prod_def_info: {prod_def_info}')
    platform = prod_def_info['metadata']['platform']['code']
    measurements = prod_def_info['measurements']
    product_instrument = prod_def_info['metadata']['instrument']['name']
    product_type = prod_def_info['metadata']['product_type']
    # print(f'measurements: {measurements}')
    # print(f'raster: {raster, type(raster)}')

    geometry, bbox = get_geometry(bounds, epsg_code)
    id = str(uuid.uuid5(uuid.NAMESPACE_URL, str(raster)))

    # Create the STAC metadata file.
    stac_dict = {
        "id": id,  # raster.stem.replace(" ", "_"),
        "type": "Feature",
        "stac_version": "1.0.0-beta.2",
        "stac_extensions": [
            "proj"
        ],
        "properties": {"platform": platform, "datetime": date_string, "proj:epsg": epsg_code},
        "bbox": bbox,
        "geometry": geometry,
        "assets": {measurement['name']: {
            "title": f"Data file for {measurement['name']}",
            "type": "image/tiff; application=geotiff; profile=cloud-optimized",
            "roles": ["data"],
            "href": raster.stem + raster.suffix,
            "proj:shape": shape,
            "proj:transform": transform
        } for measurement in measurements}
        # "assets": {
        # band_name: {
        #     "title": f"Data file for {band_name}",
        #     "type": "image/tiff; application=geotiff; profile=cloud-optimized",
        #     "roles": ["data"],
        #     "href": raster.stem + raster.suffix,
        #     "proj:shape": shape,
        #     "proj:transform": transform,
        # }
        # },
    }
    with open(raster.with_suffix(".json"), "w") as f:
        json.dump(stac_dict, f, indent=2)

    from utils.get_geo_ref_points import get_geo_ref_points_tiff_path
    from utils.index.indexing_utils import get_coords
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(epsg_code)
    geo_ref_points = get_geo_ref_points_tiff_path(raster)
    coordinates = get_coords(geo_ref_points, spatial_ref)
    crs = spatial_ref.GetAttrValue("AUTHORITY", 0) + ":" + spatial_ref.GetAttrValue("AUTHORITY", 1)

    doc_measurements = {
        measurement['name']: {
            'path': f'/vsis3/{raster}'
        } for measurement in measurements}
    # print(f'doc_measurements: {doc_measurements}')

    # Create the ODC dataset metadata file.
    odc_dataset_doc = {
        "$schema": "https://schemas.opendatacube.org/dataset",
        "id": id,
        'product': {'name': product},
        'instrument': {'name': product_instrument},
        'product_type': product_type,
        'creation_dt': date_string,
        'platform': {'code': platform},
        'extent': {
            'from_dt': date_string,
            'to_dt': date_string,
            'center_dt': date_string,
            'coord': coordinates,
        },
        'format': {'name': 'GeoTiff'},
        'grid_spatial': {
            'projection': {
                'geo_ref_points': geo_ref_points,
                'spatial_reference': crs,
            }
        },
        'image': {
            'bands': doc_measurements
        },
        'lineage': {'source_datasets': {}},
    }
    with open(raster.with_suffix(".odc-dataset.json"), "w") as f:
        # json.dump(stac_transform(stac_dict), f, indent=2)
        json.dump(odc_dataset_doc, f, indent=2)

    return None

# def process_rasters(rasters, platform, band_name, cog_convert, default_date):


def process_rasters(product, rasters, cog_convert):
    def raster_to_cog(raster):
        try:
            if cog_convert:
                raster = convert_to_cog(raster)
            # raster = convert_to_cog(raster)
            # create_stac(raster, platform, band_name, default_date)
            # create_stac(product, raster)
        except Exception as e:
            print(f"Failed to process {raster} with exception {e}")

    if cog_convert:
        Parallel(n_jobs=-1)(delayed(raster_to_cog)(raster)
                            for raster in tqdm(rasters, desc='Converting rasters to COGs'))
    Parallel(n_jobs=-1)(delayed(create_stac)(product, raster)
                        for raster in tqdm(rasters, desc='Creating STAC and ODC metadata documents'))
    # [create_stac(product, raster) for raster in 
    #  tqdm(rasters, desc='Creating STAC item documents')]


@click.command("create-odc-stac")
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
# Name of the ODC product the data maps to
@click.argument("product",  type=str, required=True)
@click.argument("directory", type=str, nargs=1)
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
):
    # stac_template = jinja2.Template(
    # """
    # name: {{product_name}}
    # description: Auto-generated product example for {{product_name}}, {{platform}}
    # metadata_type: eo3

    # metadata:
    #     product:
    #         name: {{product_name}}
    #     platform:
    #         code: {{platform}}

    # measurements:
    # {% for band_name in band_names %}
    # - name: '{{band_name}}'
    # units: '1'
    # dtype: '{{band_type}}'
    # nodata: {{band_nodata}}
    # {% endfor %}
    # ...
    # """
    # )

    # if create_product:
    #     with open(pathlib.Path(directory) / f"{platform}.odc-product.yaml", "wt") as f:
    #         f.write(
    #             stac_template.render(
    #                 platform=platform,
    #                 band_name=band_name,
    #                 band_type=band_type,
    #                 band_nodata=band_nodata,
    #             )
    #         )
    rasters = list(pathlib.Path(directory).glob("**/*" + extension))
    # process_rasters(rasters, platform, band_name, cog_convert, default_date)
    process_rasters(product, rasters, cog_convert)


if __name__ == "__main__":
    cli()
