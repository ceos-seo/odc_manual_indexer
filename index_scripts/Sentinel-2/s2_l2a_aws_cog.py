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
import urllib3
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

bands_s2_l2a = [
    ('1', 'coastal_aerosol'),
    ('2', 'blue'),
    ('3', 'green'),
    ('4', 'red'),
    ('5', 'rededge1'),
    ('6', 'rededge2'),
    ('7', 'rededge3'),
    ('8', 'nir1'),
    ('8A', 'nir2'),
    ('9', 'water_vapor'),
    ('11', 'swir1'),
    ('12', 'swir2'),
    ('AOT', 'AOT'),
    ('SCL', 'SCL')
]

band_file_map = {
    'blue': 'sr_band1',
    'green': 'sr_band2',
    'red': 'sr_band3',
    'nir': 'sr_band4',
    'swir1': 'sr_band5',
    'swir2': 'sr_band7',
    'pixel_qa': 'pixel_qa',
    'radsat_qa': 'radsat_qa',
    'sr_cloud_qa': 'sr_cloud_qa',
    'sr_atmos_opacity': 'sr_atmos_opacity'
}


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
    'ul': {'x': float(info['bbox'][0]), 
           'y': float(info['bbox'][3])},
    'ur': {'x': float(info['bbox'][2]), 
           'y': float(info['bbox'][3])},
    'll': {'x': float(info['bbox'][0]), 
           'y': float(info['bbox'][1])},
    'lr': {'x': float(info['bbox'][2]), 
           'y': float(info['bbox'][1])},
    }

def absolutify_paths(doc, bucket_name, obj_key):
    objt_key = format_obj_key(obj_key)
    for band in doc['image']['bands'].values():
        band['path'] = get_s3_url(bucket_name, objt_key + '/'+band['path'])
    return doc

def make_metadata_doc(mtl_data, bucket_name, object_key):
    s3_dir_path_prefix = os.path.dirname(object_key)
    s3_dir_path = f's3://{bucket_name}/{s3_dir_path_prefix}'
    mtl_data = json.loads(mtl_data)

    instrument = 'MSI'
    processing_level = 'L2A'
    center_dt = mtl_data['properties']['datetime']
    creation_dt = center_dt
    
    geo_ref_points = get_geo_ref_points(mtl_data)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(4326)
    crs = spatial_ref.GetAttrValue("AUTHORITY", 0) + ":" + spatial_ref.GetAttrValue("AUTHORITY", 1)
    coordinates = get_coords(geo_ref_points, spatial_ref)

    satellite = 'SENTINEL_2'
    bands = bands_s2_l2a
    doc_bands = {}
    band_data = {'layer': 1}
    unique_band_filename_map = \
        {'nir2': 'B8A',
         'AOT': 'AOT',
         'SCL': 'SCL'}
    for i, band in bands:
        import copy
        band_data_current = copy.deepcopy(band_data)
        try:
            int_i = int(i)
        except:
            int_i = None
        if int_i and int_i <= 12:
            band_data_current['path'] = f'{s3_dir_path}/B{i.zfill(2)}.tif'
        else:
            band_data_current_path = f'{s3_dir_path}/{unique_band_filename_map[band]}.tif'
            band_data_current['path'] = band_data_current_path if band_data_current_path is not None else ""
        doc_bands[band] = band_data_current
    doc = {
        'id': str(uuid.uuid5(uuid.NAMESPACE_URL, get_s3_url(bucket_name, object_key))),
        'product': {'name': 's2_l2a_aws_cog'},
        'processing_level': processing_level,
        'creation_dt': str(creation_dt),
        'platform': {'code': satellite},
        'instrument': {'name': instrument},
        'extent': {
            'from_dt': center_dt,
            'to_dt': center_dt,
            'center_dt': center_dt,
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
            'bands': doc_bands, 
        },
        'lineage': {'source_datasets': {}},
    }
    return doc


def format_obj_key(obj_key):
    obj_key ='/'.join(obj_key.split("/")[:-1])
    return obj_key


def archive_document(doc, uri, index, sources_policy):
    def get_ids(dataset):
        ds = index.datasets.get(dataset.id, include_sources=True)
        for source in ds.sources.values():
            yield source.id
        yield dataset.id

    resolver = Doc2Dataset(index)
    dataset, err = resolver(doc, uri)
    index.datasets.archive(get_ids(dataset))
    logging.info("Archiving %s and all sources of %s", dataset.id, dataset.id)


def add_dataset(doc, uri, index, sources_policy):
    doc_id = doc['id']

    resolver = Doc2Dataset(index)
    dataset, err  = resolver(doc, uri)
    existing_dataset = index.datasets.get(doc_id)

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

def worker(config, bucket_name, prefix, suffix, start_date, end_date, func, unsafe, sources_policy, queue):
    dc=datacube.Datacube(config=config)
    index = dc.index
    s3 = boto3.resource("s3")
    safety = 'safe' if not unsafe else 'unsafe'

    while True:
        try:
            key = queue.get(timeout=60)
            if key == GUARDIAN:
                break
            logging.info("Processing %s %s", key, current_process())
            obj = s3.Object(bucket_name, key).get(ResponseCacheControl='no-cache', RequestPayer='requester')
            raw = None
            while raw is None:
                try:
                    raw = obj['Body'].read()
                except urllib3.exceptions.ProtocolError: 
                    print(f'Connection to bucket {bucket_name} lost.')
                    sleep(5) # Wait for connection problems to resolve.
            raw_string = raw.decode('utf8')

            # Attempt to process text document
            data = make_metadata_doc(raw_string, bucket_name, key)
            if data:
                uri = get_s3_url(bucket_name, key)
                cdt = data['creation_dt']

                # Only do the date check if we have dates set.
                if cdt and start_date and end_date:
                    # Use the fact lexicographical ordering matches the chronological ordering
                    if cdt >= start_date and cdt < end_date:
                        func(data, uri, index, sources_policy)
                else:
                    func(data, uri, index, sources_policy)
            else:
                logging.error("Failed to get data returned... skipping file.")
            queue.task_done()
        except Empty:
            sleep(1) # Queue is empty
        except EOFError:
            logging.error("EOF Error hit.")
            queue.task_done()
        except ValueError as e:
            logging.error("Found data for a satellite that we can't handle: {}".format(e))
            import traceback
            traceback.print_exc()
            queue.task_done()


def iterate_datasets(bucket_name, config, prefix, suffix, start_date, end_date, lat1, lat2, lon1, lon2, func, unsafe, sources_policy):
    logging.info("Starting iterate datasets.")
    manager = Manager()
    queue = manager.Queue()

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    logging.info("Bucket: %s prefix: %s ", bucket_name, str(prefix))
    worker_count = cpu_count() * 2

    processess = []
    for i in range(worker_count):
        proc = Process(target=worker, args=(config, bucket_name, prefix, suffix, start_date, end_date, func, unsafe, sources_policy, queue,))
        processess.append(proc)
        proc.start()

    # Determine the UTM tiles to load data for.
    ## 1. Get the zone number/letter bounds.
    import utm
    _, _, zone_num_ll, zone_letter_ll = utm.from_latlon(lat1, lon1)
    _, _, zone_num_ur, zone_letter_ur = utm.from_latlon(lat2, lon2)
    ## 2. Determine the zone number and letter ranges.
    def char_range(c1, c2):
        """Generates the characters from `c1` to `c2`, inclusive."""
        for c in range(ord(c1), ord(c2)+1):
            yield chr(c)
    zone_num_range = list(range(zone_num_ll, zone_num_ur+1))
    zone_letter_range = list(char_range(zone_letter_ll, zone_letter_ur))

    # Subset the years based on the requested time range (`start_date`, `end_date`).
    years = list(range(datetime.strptime(start_date, "%Y-%m-%d").year, \
                       datetime.strptime(end_date, "%Y-%m-%d").year+1))
    
    count = 0
    # (Old code)
    for year in years:
        for zone_num in zone_num_range:
            for zone_letter in zone_letter_range:
                zone_num_letter_prefix = f"{prefix}/{zone_num}/{zone_letter}"
                for obj in bucket.objects.filter(Prefix = zone_num_letter_prefix, 
                                                 RequestPayer='requester'):
                    if (obj.key.endswith(suffix)):
                        while queue.qsize() > 100:
                            sleep(1)
                        count += 1
                        queue.put(obj.key)
    
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
@click.option('--sources_policy', default="verify", help="verify, ensure, skip")
def main(bucket_name, config, prefix, suffix, start_date, end_date, lat1, lat2, lon1, lon2, archive, unsafe, sources_policy):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
    start_date = "2015-06-23" if start_date is None else start_date
    end_date = "2029-12-31" if end_date is None else end_date
    lat1 = -90 if lat1 is None else float(lat1)
    lat2 = 90 if lat2 is None else float(lat2)
    # latitude must be in range (-80, 84) for `utm.from_latlon()`.
    lat1 = max(-80, min(lat1, 84))
    lat2 = max(-80, min(lat2, 84))
    lon1 = -180 if lon1 is None else float(lon1)
    lon2 = 180 if lon2 is None else float(lon2)
    logging.info(f"lat1, lat2, lon1, lon2: {lat1, lat2, lon1, lon2}")
    action = archive_document if archive else add_dataset
    iterate_datasets(bucket_name, config, prefix, suffix, start_date, end_date, lat1, lat2, lon1, lon2, action, unsafe, sources_policy)
   
if __name__ == "__main__":
    main()
