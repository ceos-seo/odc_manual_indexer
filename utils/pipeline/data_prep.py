#!/usr/bin/env python

"""
Utility for converting GeoTIFFs in a directory tree to COGs.
Modified from here: https://github.com/opendatacube/datacube-stac-example/blob/master/stac-simple.py
"""
import os
import re
import datetime
import json
import pathlib
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

from utils.get_geo_ref_points import get_geo_ref_points_tiff_path

output_profile = cog_profiles.get("deflate")
output_profile.update(crs="epsg:4326")

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


def raster_to_cog(raster):
    try:
        convert_to_cog(raster)
    except Exception as e:
        print(f"Failed to process {raster} with exception {e}")

def create_stac_odc_meta(product, scene_path, scene_raster_paths, s3_uri):
    transform = None
    shape = None
    epsg_code = None

    # Determine which raster paths map to which measurements.
    from utils.index.indexing_utils import products_meas_file_unq_substr_map
    meas_file_unq_substr_map = products_meas_file_unq_substr_map[product]
    meas_raster_map = {}
    for meas, meas_file_substr in meas_file_unq_substr_map.items():
        for raster_path in scene_raster_paths:
            match = re.search(meas_file_substr, str(raster_path))
            if match:
                meas_raster_map[meas] = raster_path
                break

    with rasterio.open(scene_raster_paths[0]) as dataset:
        transform = dataset.transform
        shape = dataset.shape
        epsg_code = dataset.crs.to_epsg()
        bounds = dataset.bounds
        tags = dataset.tags()
        # Read the data from the metadata
        if product in ['black_marble_night_lights']:
            date_string = tags['ProductionTime']

    # Read information about this product from its definition file.
    import os
    WORKDIR = os.environ['WORKDIR']
    prod_def_paths = {
        'black_marble_night_lights': f'{WORKDIR}/prod_defs/black_marble_night_lights.yaml'}
    import yaml
    with open(prod_def_paths[product], 'r') as prod_def_yaml_file:
        prod_def_info = yaml.safe_load(prod_def_yaml_file)
    platform = prod_def_info['metadata']['platform']['code']
    measurements = prod_def_info['measurements']
    product_instrument = prod_def_info['metadata']['instrument']['name']
    product_file_format = prod_def_info['metadata']['format']['name']
    product_type = prod_def_info['metadata']['product_type']
    metadata_type = prod_def_info['metadata_type']

    geometry, bbox = get_geometry(bounds, epsg_code)
    id = str(uuid.uuid5(uuid.NAMESPACE_URL, str(scene_path)))

    # Create the `assets` value.
    assets_map = {}
    for measurement in measurements:
        meas_name = measurement['name']
        raster_path = meas_raster_map[meas_name]
        assets_map[meas_name] = {
            "title": f"Data file for {meas_name}",
            "type": "image/tiff; application=geotiff; profile=cloud-optimized",
            "roles": ["data"],
            "href": raster_path.stem + raster_path.suffix,
            "proj:shape": shape,
            "proj:transform": transform
        }

    # Create the STAC metadata file in the scene directory.
    stac_dict = {
        "id": id,
        "type": "Feature",
        "stac_version": "1.0.0-beta.2",
        "stac_extensions": [
            "proj"
        ],
        "properties": {"platform": platform, "datetime": date_string, "proj:epsg": epsg_code},
        "bbox": bbox,
        "geometry": geometry,
        "assets":  assets_map,
    }
    metadata_file_base_path = f'{scene_path}/{scene_path.name}'
    with open(f'{metadata_file_base_path}.stac.json', "w") as f:
        json.dump(stac_dict, f, indent=2)

    # Create the ODC dataset metadata file.
    # Generate a metadata document matching the metadata
    # type associated with the product.
    if metadata_type == 'eo':
        from utils.get_geo_ref_points import get_geo_ref_points_tiff_path
        from utils.index.indexing_utils import get_coords
        spatial_ref = osr.SpatialReference()
        spatial_ref.ImportFromEPSG(epsg_code)
        geo_ref_points = get_geo_ref_points_tiff_path(raster_path)
        coordinates = get_coords(geo_ref_points, spatial_ref)
        crs = spatial_ref.GetAttrValue(
            "AUTHORITY", 0) + ":" + spatial_ref.GetAttrValue("AUTHORITY", 1)

        vsi_s3_uri = s3_uri.replace('s3://', '/vsis3/')
        doc_measurements = {}
        for measurement in measurements:
            meas_name = measurement['name']
            raster_path = meas_raster_map[meas_name]
            doc_measurements[meas_name] = {
                'path': f'{vsi_s3_uri}/{raster_path.parts[-2]}/{raster_path.name}'}

        odc_dataset_doc = {
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
    elif metadata_type == 'eo3':
        odc_dataset_doc = stac_transform(stac_dict)
        odc_dataset_doc_properties = odc_dataset_doc['properties']
        odc_dataset_doc_properties.update({
            'eo:instrument': product_instrument,
            'odc:file_format': product_file_format,
        })
        odc_dataset_doc.update({
            'product': {'name': product},
            'instrument': {'name': product_instrument},
            'properties': odc_dataset_doc_properties,
        })
    with open(f'{metadata_file_base_path}.odc-dataset.json', "w") as f:
        json.dump(odc_dataset_doc, f, indent=2)

    return None

def data_to_cog_stac_odc_meta(
        extension,
        cog_convert,
        product,
        directory,
        s3_uri):
    raster_paths = list(pathlib.Path(directory).glob("**/*" + extension))
    scene_paths = list(set(pathlib.Path(os.path.dirname(
        str(raster_path))) for raster_path in raster_paths))
    scenes_raster_paths_map = {scene_path: list(pathlib.Path(
        scene_path).glob("**/*" + extension)) for scene_path in scene_paths}

    if cog_convert:
        Parallel(n_jobs=-1)(delayed(raster_to_cog)(raster)
                            for raster in tqdm(raster_paths, desc='Converting rasters to COGs'))
    Parallel(n_jobs=-1)(delayed(create_stac_odc_meta)(product, scene, scenes_raster_paths_map[scene], s3_uri)
                        for scene in tqdm(scene_paths, desc='Creating STAC and ODC metadata documents'))
