#!/usr/bin/env python3

# coding: utf-8
from xml.etree import ElementTree
from pathlib import Path
import os
from osgeo import osr
import dateutil
from dateutil import parser
from datetime import timedelta
import uuid
import yaml
import logging
import click
import re
import boto3
import datacube
from datacube.index.hl import Doc2Dataset
from datacube.utils import changes
from ruamel.yaml import YAML
import json
from bs4 import BeautifulSoup
from datetime import datetime

from multiprocessing import Process, current_process, Queue, Manager, cpu_count
from time import sleep, time
from queue import Empty

import sys
sys.path.append(os.environ.get('WORKDIR'))
from utils.indexing_utils import get_coords, get_s3_url

GUARDIAN = "GUARDIAN_QUEUE_EMPTY"
AWS_PDS_TXT_SUFFIX = "MTL.txt"
LANDSAT_XML_SUFFIX = 'T1.xml'
GENERAL_LANDSAT_XML_SUFFIX = '.xml'

MTL_PAIRS_RE = re.compile(r'(\w+)\s=\s(.*)')

bands_ls7_l2_c2 = [
    # Surface Reflectance Measurements #
    ('1', 'blue'),
    ('2', 'green'),
    ('3', 'red'),
    ('4', 'nir'),
    ('5', 'swir1'),
    ('6', 'tirs'),
    ('7', 'swir2'),
    ('QUALITY', 'pixel_qa'),
    ('RADSATQA', 'radsat_qa'),
    ('CLD_QUALITY', 'cloud_qa'),
    # Surface Temperature Measurements #
    # ('TEMP', 'surface_temp'),
    # ('ATRAN', 'atran'),
    # ('CDIST', 'cdist'),
    # ('DRAD', 'drad'),
    # ('URAD', 'urad'),
    # ('TRAD', 'trad'),
    # ('EMIS', 'emis'),
    # ('EMISSD', 'emissd'),
    # ('STQA', 'st_pixel_qa')
]

# bands_ls7 = [
#     ('1', 'blue'),
#     ('2', 'green'),
#     ('3', 'red'),
#     ('4', 'nir'),
#     ('5', 'swir1'),
#     ('7', 'swir2'),
#     ('QUALITY', 'quality')
# ]

# bands_ls57_usard = [
#     ('1', 'blue'),
#     ('2', 'green'),
#     ('3', 'red'),
#     ('4', 'nir'),
#     ('5', 'swir1'),
#     ('6', 'swir2'),
#     ('7', 'sr_atmos_opacity'),
#     ('8', 'pixel_qa'),
#     ('9', 'radsat_qa'),
#     ('10', 'sr_cloud_qa')
# ]

# bands_ls8_l2_usard = [
#     ('1', 'coastal_aerosol'),
#     ('2', 'blue'),
#     ('3', 'green'),
#     ('4', 'red'),
#     ('5', 'nir'),
#     ('6', 'swir1'),
#     ('7', 'swir2'),
#     ('8', 'pixel_qa'),
#     ('9', 'sr_aerosol'),
#     ('10', 'radsat_qa')
# ]

# band_file_map_l57 = {
#     'blue': 'sr_band1',
#     'green': 'sr_band2',
#     'red': 'sr_band3',
#     'nir': 'sr_band4',
#     'swir1': 'sr_band5',
#     'swir2': 'sr_band7',
#     'pixel_qa': 'pixel_qa',
#     'radsat_qa': 'radsat_qa',
#     'sr_cloud_qa': 'sr_cloud_qa',
#     'sr_atmos_opacity': 'sr_atmos_opacity'
# }

# band_file_map_l8 = {
#     'coastal_aerosol': 'sr_band1',
#     'blue': 'sr_band2',
#     'green': 'sr_band3',
#     'red': 'sr_band4',
#     'nir': 'sr_band5',
#     'swir1': 'sr_band6',
#     'swir2': 'sr_band7',
#     'pixel_qa': 'pixel_qa',
#     'radsat_qa': 'radsat_qa',
#     'sr_aerosol': 'sr_aerosol'
# }


def _parse_value(s):
    s = s.strip('"')
    for parser in [int, float]:
        try:
            return parser(s)
        except ValueError:
            pass
    return s


def _parse_group(lines):
    tree = {}
    for line in lines:
        match = MTL_PAIRS_RE.findall(line)
        if match:
            key, value = match[0]
            if key == 'GROUP':
                tree[value] = _parse_group(lines)
            elif key == 'END_GROUP':
                break
            else:
                tree[key] = _parse_value(value)
    return tree


def get_band_filenames(xmldoc):
    """ parse the xml metadata and return the band names in a dict """
    band_dict = {}
    bands = xmldoc.find('.//bands')
    for bandxml in bands:
        band_name = (bandxml.get('name'))
        file = bandxml.find('.//file_name')
        band_file_name = file.text
        band_dict[band_name] = band_file_name
    return (band_dict)


def get_geo_ref_points(info):
    return {
        'ul': {'x': float(info.projection_attributes.corner_ul_lon_product.text), 
               'y': float(info.projection_attributes.corner_ul_lat_product.text)},
        'ur': {'x': float(info.projection_attributes.corner_ur_lon_product.text), 
               'y': float(info.projection_attributes.corner_ur_lat_product.text)},
        'll': {'x': float(info.projection_attributes.corner_ll_lon_product.text), 
               'y': float(info.projection_attributes.corner_ll_lat_product.text)},
        'lr': {'x': float(info.projection_attributes.corner_lr_lon_product.text), 
               'y': float(info.projection_attributes.corner_lr_lat_product.text)},
    }

def satellite_ref(sat):
    """
    To load the band_names for referencing either LANDSAT8 or LANDSAT7 bands
    """
    if sat == 'LANDSAT_7':
        sat_img = bands_ls7_l2_c2
    # elif sat in ('LANDSAT_7', 'LANDSAT_5'):
        # sat_img = bands_ls7
    # elif sat in ('USGS/EROS/LANDSAT_7', 'USGS/EROS/LANDSAT_5'):
        # logging.info("We're working with the USGS supplied landsat 5 or 7.")
        # sat_img = bands_ls57_usard
    # elif sat == 'USGS/EROS/LANDSAT_8':
        # logging.info("We're working with the USGS supplied landsat 8.")
        # sat_img = bands_ls8_l2_usard
    else:
        raise ValueError('Satellite data Not Supported')
    return sat_img


def absolutify_paths(doc, bucket_name, obj_key):
    objt_key = format_obj_key(obj_key)
    for band in doc['image']['bands'].values():
        band['path'] = get_s3_url(bucket_name, objt_key + '/'+band['path'])
    return doc


def make_metadata_doc(mtl_data, bucket_name, object_key):
    
    mtl_data = BeautifulSoup(mtl_data, "lxml")
    # print(f"mtl_data: {mtl_data}")

    # mtl_product_info = mtl_data['PRODUCT_METADATA']
    # mtl_metadata_info = mtl_data['METADATA_FILE_INFO']
    # satellite = mtl_product_info['SPACECRAFT_ID']
    satellite = 'LANDSAT_7' #mtl_data.image_attributes.spacecraft_id.text
    # instrument = mtl_product_info['SENSOR_ID']
    instrument = mtl_data.image_attributes.sensor_id.text
    # acquisition_date = mtl_product_info['DATE_ACQUIRED']
    acquisition_date = mtl_data.image_attributes.date_acquired.text
    # scene_center_time = mtl_product_info['SCENE_CENTER_TIME']
    scene_center_time = mtl_data.image_attributes.scene_center_time.text
    # level = mtl_product_info['DATA_TYPE']
    processing_level = mtl_data.product_contents.processing_level.text
    if processing_level != 'L2SR':
        return None # The data must be level 2 (surface reflectance).
    sensing_time = acquisition_date + ' ' + scene_center_time
    # cs_code = 32600 + mtl_data['PROJECTION_PARAMETERS']['UTM_ZONE']
    # cs_code = 32600 + mtl_data.projection_attributes.utm_zone.text
    # label = mtl_metadata_info['LANDSAT_SCENE_ID']
    # TODO: Ensure `label` is correct as in L8 C1 indexing script?
    label = mtl_data.level1_processing_record.landsat_scene_id.text
    # print(f"satellite, instrument: {satellite}, {instrument}")
    # print(f"acquisition_date, scene_center_time: {acquisition_date}, {scene_center_time}")
    # print(f"processing_level, sensing_time: {processing_level}, {sensing_time}")
    spatial_ref = osr.SpatialReference()
    # spatial_ref.ImportFromEPSG(cs_code)
    spatial_ref.ImportFromEPSG(4326)
    geo_ref_points = get_geo_ref_points(mtl_data)
    # print(f'geo_ref_points: {geo_ref_points}')
    crs = spatial_ref.GetAttrValue("AUTHORITY", 0) + ":" + spatial_ref.GetAttrValue("AUTHORITY", 1)
    # print(f'crs: {crs}')
    coordinates = get_coords(geo_ref_points, spatial_ref)
    # print(f'coordinates: {coordinates}')
    bands = satellite_ref(satellite)
    # print('bands:', bands)
    # print("mtl_data.product_contents:", mtl_data.product_contents)
    # print(f"mtl_data.product_contents.file_name_band_1: {mtl_data.product_contents.file_name_band_1}," \
        #   f"{getattr(mtl_data.product_contents, f'file_name_band_1').text}")
    doc_bands = {}
    band_data = {'layer': 1}
    # Bands 1-5 and 7 have a templated file name based on thier band number. Others do not.
    unique_band_filename_map = \
        {'pixel_qa': 'file_name_quality_l1_pixel',
         'tirs': 'file_name_band_st_b10',
         'radsat_qa': 'file_name_quality_l1_radiometric_saturation',
         'cloud_qa': 'file_name_quality_l2_surface_reflectance_cloud'}
    for i, band in bands:
        import copy
        band_data_current = copy.deepcopy(band_data)
        try:
            int_i = int(i)
        except:
            int_i = None
        if int_i and (int_i < 6 or int_i == 7):
            # print('here1')
            band_data_current['path'] = getattr(mtl_data.product_contents, f"file_name_band_{int(i)}").text
        # if band == 'pixel_qa': 
            # band_data['path'] = mtl_data.product_contents.file_name_quality_l1_pixel.text
        else:
            # print('here2')
            # print(f'mtl_data.product_contents: {mtl_data.product_contents}')
            # print(f'unique_band_filename_map[band]: {unique_band_filename_map[band]}')
            band_data_current_path = getattr(mtl_data.product_contents, unique_band_filename_map[band])
            band_data_current['path'] = band_data_current_path.text if band_data_current_path is not None else ""
        doc_bands[band] = band_data_current
    # print("doc_bands:", doc_bands)
    # TODO: Remove `region_code` as in L8 C1 indexing script?
    doc = {
        'id': str(uuid.uuid5(uuid.NAMESPACE_URL, get_s3_url(bucket_name, object_key))),
        'processing_level': processing_level,
        'product_type': 'LaSRCollection2',
        'creation_dt': str(acquisition_date),
        'label': label,
        'platform': {'code': satellite},
        'instrument': {'name': instrument},
        'extent': {
            'from_dt': sensing_time,
            'to_dt': sensing_time,
            'center_dt': sensing_time,
            'coord': coordinates,
                  },
        'format': {'name': 'GeoTiff'},
        'grid_spatial': {
            'projection': {
                'geo_ref_points': geo_ref_points,
                'spatial_reference': crs, 
                #'EPSG:%s' % cs_code,
                            }
                        },
        'image': {
            'bands': doc_bands, 
            #{
                # band: {
                #     'path': getattr(mtl_data.product_contents, f"file_name_band_{int(i)}").text,
                #     #mtl_product_info['FILE_NAME_BAND_' + band[0]],
                #     'layer': 1,
                # } for i, band in bands
            # }
        },
        'lineage': {'source_datasets': {}},
    }
    doc = absolutify_paths(doc, bucket_name, object_key)
    # print("doc:", doc)
    return doc


def format_obj_key(obj_key):
    obj_key ='/'.join(obj_key.split("/")[:-1])
    return obj_key


def archive_document(doc, uri, index):
    def get_ids(dataset):
        ds = index.datasets.get(dataset.id, include_sources=True)
        for source in ds.sources.values():
            yield source.id
        yield dataset.id

    resolver = Doc2Dataset(index)
    dataset, err = resolver(doc, uri)
    index.datasets.archive(get_ids(dataset))
    logging.info("Archiving %s and all sources of %s", dataset.id, dataset.id)


def add_dataset(doc, uri, index):
    # print("add_dataset doc:", doc)
    # print("add_dataset index:", index, type(index))
    doc_id = doc['id']
    # logging.info("Indexing dataset: {} with URI:  {}".format(doc_id, uri))
    # print(f'type(doc_id): {type(doc_id)}')
    # print(f'type(uri): {type(uri)}')

    resolver = Doc2Dataset(index)
    # print(f"resolver: {resolver}")
    # print(f'uri: {uri}')
    dataset, err  = resolver(doc, uri)
    # print(f"dataset, err: {dataset}, {err}")
    existing_dataset = index.datasets.get(doc_id)
    # print(f"existing_dataset: {existing_dataset}")

    # print('here in add_dataset()')

    if not existing_dataset:
        logging.info("Trying to index")
        if err is not None:
            logging.error("%s", err)
        else:
            try:
                index.datasets.add(dataset, with_lineage=False) # Source policy to be checked in sentinel 2 dataset types
            except Exception as e:
                logging.error("Unhandled exception %s", e)
    else:
        logging.info("Updating dataset instead.")
        try:
            index.datasets.update(dataset, {tuple(): changes.allow_any})
        except Exception as e:
            logging.error("Unhandled exception %s", e)

    return dataset, err

def worker(config, bucket_name, prefix, suffix, start_date, end_date, func, unsafe, queue):
    dc=datacube.Datacube(config=config)
    index = dc.index
    s3 = boto3.resource("s3")
    safety = 'safe' if not unsafe else 'unsafe'

    while True:
        try:
            # print(f"queue: {queue}")
            key = queue.get(timeout=60)
            if key == GUARDIAN:
                break
            logging.info("Processing %s %s", key, current_process())
            # print(f"bucket_name, key: {bucket_name}, {key}")
            obj = s3.Object(bucket_name, key).get(ResponseCacheControl='no-cache', RequestPayer='requester')
            raw = obj['Body'].read()
            raw_string = raw.decode('utf8')

            # print(f"suffix: {suffix}")
            # Attempt to process text document
            # txt_doc = _parse_group(iter(raw_string.split("\n")))['L1_METADATA_FILE']
            data = make_metadata_doc(raw_string, bucket_name, key)
            # else:
            #     yaml = YAML(typ=safety, pure=False)
            #     yaml.default_flow_style = False
            #     data = yaml.load(raw)
            if data:
                uri = get_s3_url(bucket_name, key)
                # print(f'uri: {uri}')

                # print("data:", data)
                # print(f"data: {type(data)}")
                # data = BeautifulSoup(data, "lxml")
                # print(f'data: {data}')
                # print(f"data.landsat_metadata_file.image_attributes.date_acquired.text:"
                    #   f"{data.landsat_metadata_file.image_attributes.date_acquired.text}")
                cdt = data['creation_dt']

                # print(f"cdf:", cdt)
                # Only do the date check if we have dates set.
                # print(f'cdt, start_date, end_date: {cdt, start_date, end_date}')
                if cdt and start_date and end_date:
                    # print(f"cdt, start_date, end_date: {cdt, start_date, end_date}")
                    # print(f"cdt >= start_date: {cdt >= start_date}")
                    # print(f"cdt < end_date: {cdt < end_date}")
                    # Use the fact lexicographical ordering matches the chronological ordering
                    if cdt >= start_date and cdt < end_date:
                        # logging.info("calling %s", func)
                        # print('here1')
                        func(data, uri, index)
                else:
                    # print('here2')
                    func(data, uri, index)
            else:
                logging.error("Failed to get data returned... skipping file.")
        except Empty:
            logging.error("Empty exception hit.")
            break
        except EOFError:
            logging.error("EOF Error hit.")
            break
        except ValueError as e:
            logging.error("Found data for a satellite that we can't handle: {}".format(e))
            import traceback
            traceback.print_exc()
        finally:
            queue.task_done()


def iterate_datasets(bucket_name, config, prefix, suffix, start_date, end_date, lat1, lat2, lon1, lon2, func, unsafe):
    logging.info("Starting iterate datasets.")
    manager = Manager()
    queue = manager.Queue()

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    # print(f"Bucket: {bucket_name} prefix: {str(prefix)}")
    logging.info("Bucket: %s prefix: %s ", bucket_name, str(prefix))
    # safety = 'safe' if not unsafe else 'unsafe'
    worker_count = cpu_count() * 2

    processess = []
    for i in range(worker_count):
        proc = Process(target=worker, args=(config, bucket_name, prefix, suffix, start_date, end_date, func, unsafe, queue,))
        processess.append(proc)
        proc.start()

    # Determine the path-rows to load data for.
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from tile_shapefile_formatting import path_row_geojson_to_min_max_xy_fmt
    path_row_data = path_row_geojson_to_min_max_xy_fmt()
    path_rows_to_index = (lat1 < path_row_data.max_y) & (path_row_data.min_y < lat2) & \
                         (lon1 < path_row_data.max_x) & (path_row_data.min_x < lon2)
    path_rows_to_index = path_row_data.loc[path_rows_to_index, ['Path', 'Row']]

    # Subset the years based on the requested time range (`start_date`, `end_date`).
    years = list(range(datetime.strptime(start_date, "%Y-%m-%d").year, \
                       datetime.strptime(end_date, "%Y-%m-%d").year+1))
    
    count = 0
    # (Old code)
    for year in years:
        for path, row in path_rows_to_index.values:
            year_path_row_prefix = f"{prefix}/{year}/{path.zfill(3)}/{row.zfill(3)}"
            for obj in bucket.objects.filter(Prefix = year_path_row_prefix, 
                                             RequestPayer='requester'):
                if (obj.key.endswith(suffix)):
                    count += 1
                    queue.put(obj.key)
    # for obj in bucket.objects.filter(Prefix = str(prefix), RequestPayer='requester'):
        # print(f"obj: {obj}")
        # if (obj.key.endswith(suffix)):
            # count += 1
            # queue.put(obj.key)
    # (New code)
    # s3_client = boto3.client('s3')
    # bucket_objs = s3_client.list_objects(Bucket=bucket_name, Prefix = str(prefix), RequestPayer='requester')
    # print(f"bucket_objs['Contents']: {bucket_objs['Contents']}")
    # for obj in bucket_objs['Contents']:
    #     print(f"obj: {obj}")
    #     # if (obj.key.endswith(suffix)):
    #     if obj['Key'].endswith(suffix):
    #         count += 1
    #         queue.put(obj['Key'])
    
    logging.info("Found {} items to investigate".format(count))

    for i in range(worker_count):
        queue.put(GUARDIAN)

    for proc in processess:
        proc.join()


@click.command(help= "Enter Bucket name. Optional to enter configuration file to access a different database")
@click.argument('bucket_name')
@click.option('--config','-c',help="Pass the configuration file to access the database",
        type=click.Path(exists=True))
@click.option('--prefix', '-p', help="Pass the prefix of the object to the bucket")
@click.option('--suffix', '-s', default=".yaml", help="Defines the suffix of the metadata_docs that will be used to load datasets. For AWS PDS bucket use MTL.txt")
@click.option('--start_date', help="Pass the start acquisition date, in YYYY-MM-DD format")
@click.option('--end_date', help="Pass the end acquisition date, in YYYY-MM-DD format")
@click.option('--lat1', help="Pass the lower latitude")
@click.option('--lat2', help="Pass the upper latitude")
@click.option('--lon1', help="Pass the lower longitude")
@click.option('--lon2', help="Pass the upper longitude")
@click.option('--archive', is_flag=True, help="If true, datasets found in the specified bucket and prefix will be archived")
@click.option('--unsafe', is_flag=True, help="If true, YAML will be parsed unsafely. Only use on trusted datasets. Only valid if suffix is yaml")
def main(bucket_name, config, prefix, suffix, start_date, end_date, lat1, lat2, lon1, lon2, archive, unsafe):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
    start_date = "1999-04-15" if start_date is None else start_date
    end_date = "2029-12-31" if end_date is None else end_date
    lat1 = -90 if lat1 is None else float(lat1)
    lat2 = 90 if lat2 is None else float(lat2)
    lon1 = -180 if lon1 is None else float(lon1)
    lon2 = 180 if lon2 is None else float(lon2)
    logging.info(f"lat1, lat2, lon1, lon2: {lat1, lat2, lon1, lon2}")
    action = archive_document if archive else add_dataset
    iterate_datasets(bucket_name, config, prefix, suffix, start_date, end_date, lat1, lat2, lon1, lon2, action, unsafe)
   
if __name__ == "__main__":
    main()
