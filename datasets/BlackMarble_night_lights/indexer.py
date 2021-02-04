#!/usr/bin/env python3

# coding: utf-8

import os
from osgeo import osr
import uuid
import logging
import click
import datacube
from datacube.index.hl import Doc2Dataset
from datacube.utils import changes
import rasterio
import glob
import xarray as xr
import re
import datetime

from multiprocessing import Process, current_process, Queue, Manager, cpu_count
from time import sleep, time
from queue import Empty

import sys
sys.path.append(os.environ.get('WORKDIR'))
from utils.indexing_utils import get_coords, get_s3_url

GUARDIAN = "GUARDIAN_QUEUE_EMPTY"

def get_geo_ref_points(tif_path):
    ds = rasterio.open(tif_path)
    minx = ds.bounds.left
    maxx = ds.bounds.right
    miny = ds.bounds.bottom
    maxy = ds.bounds.top
    return {
        'ul': {'x': minx, 'y': maxy}, 
        'ur': {'x': maxx, 'y': maxy},
        'll': {'x': minx, 'y': miny}, 
        'lr': {'x': maxx, 'y': miny}
    }

def get_res(geo_ref_points, tif_path, src_crs):
    minx = geo_ref_points['ul']['x']
    maxx = geo_ref_points['ur']['x']
    miny = geo_ref_points['ll']['y']
    maxy = geo_ref_points['ul']['y']

    # Convert to EPSG:4326.
    (minx, maxx), (miny, maxy) = \
        rasterio.warp.transform(src_crs, 'EPSG:4326', [minx, maxx], [miny, maxy])

    data_np_arr = rasterio.open(tif_path).read(1)
    x_res = (maxx - minx) / data_np_arr.shape[1]
    y_res = (maxy - miny) / data_np_arr.shape[0]
    return x_res, y_res

def absolutify_paths(doc):
    for band in doc['image']['bands'].values():
        band['path'] = os.path.abspath(band['path'])
    return doc

def make_metadata_doc(path, product_name):
    tif_paths = [os.path.join(path, file_path) for file_path in os.listdir(path) if file_path.endswith('.tif')]
    data = xr.open_rasterio(tif_paths[0])

    start_time_str = data.attrs['StartTime']
    start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S.%f')
    end_time_str = data.attrs['EndTime']
    end_time = datetime.datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S.%f')
    center_dt = start_time + ((end_time - start_time) / 2)
    creation_dt_str = data.attrs['ProductionTime']
    creation_dt = datetime.datetime.strptime(creation_dt_str, '%Y-%m-%d %H:%M:%S.%f')

    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(4326)
    geo_ref_points = get_geo_ref_points(tif_paths[0])
    crs = spatial_ref.GetAttrValue("AUTHORITY", 0) + ":" + spatial_ref.GetAttrValue("AUTHORITY", 1)
    coordinates = get_coords(geo_ref_points, spatial_ref)

    doc_bands = {}
    data_var_file_str_map = \
        {'DNB_BRDF_corrected_NTL': 'DNB_BRDF-Corrected_NTL', 
        'DNB_Lunar_Irradiance': 'DNB_Lunar_Irradiance',
        'gap_filled_DNB_BRDF_corrected_NTL': 'Gap_Filled_DNB_BRDF-Corrected_NTL', 
        'latest_high_quality_retrieval': 'Latest_High_Quality_Retrieval',
        'mandatory_quality_flag': 'Mandatory_Quality_Flag', 
        'QF_cloud_mask': 'QF_Cloud_Mask', 
        'snow_flag': 'Snow_Flag'}
    for data_var, data_var_file_str in data_var_file_str_map.items():
        for tif_path in tif_paths:
            match = re.search(data_var_file_str, tif_path)
            if match:
                doc_bands[data_var] = {'path': tif_path}
                break

    doc = {
        'id': str(uuid.uuid5(uuid.NAMESPACE_URL, path)),
        'product': {'name': product_name},
        'instrument': {'name': 'VIIRS'},
        'product_type': 'SurfaceRadiance',
        'creation_dt': creation_dt,
        'platform': {'code': 'BlackMarble'},
        'extent': {
            'from_dt': start_time,
            'to_dt': end_time,
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
            'bands': doc_bands
        },
        'lineage': {'source_datasets': {}},
    }
    doc = absolutify_paths(doc)
    return doc

def add_dataset(doc, product_name, uri, index):
    doc_id = doc['id']
    logging.info("Indexing dataset: {} with URI: {}".format(doc_id, uri))

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

def worker(config, path, product_name, unsafe, queue):
    dc = datacube.Datacube(config=config)
    index = dc.index
    safety = 'safe' if not unsafe else 'unsafe'

    while True:
        try:
            path = queue.get(timeout=60)
            if path == GUARDIAN:
                break
            logging.info("Processing %s %s", path, current_process())

            data = make_metadata_doc(path, product_name)
            if data:
                uri = 'file:/' + data['image']['bands']['DNB_BRDF_corrected_NTL']['path']
                add_dataset(data, product_name, uri, index)
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
        finally:
            queue.task_done()

def iterate_datasets(path, product_name, config, unsafe):
    logging.info("Starting iterate datasets.")
    manager = Manager()
    queue = manager.Queue()

    worker_count = cpu_count() * 2

    processess = []
    for i in range(worker_count):
        proc = Process(target=worker, args=(config, path, product_name, unsafe, queue,))
        processess.append(proc)
        proc.start()

    # Search the leaf directories.
    count = 0
    for root,dirs,files in os.walk(path):
        if not dirs: # This is a leaf directory.
            count += 1
            queue.put(root)
    
    logging.info("Found {} items to investigate".format(count))

    for i in range(worker_count):
        queue.put(GUARDIAN)

    for proc in processess:
        proc.join()

@click.command(help='Enter the absolute or relative path to the data to index followed by the product name. ' \
                    'This script checks all lowest-level directories within the path.')
@click.argument('path')
@click.argument('product_name')
@click.option('--config','-c',help="Pass the configuration file to access a different ODC database",
        type=click.Path(exists=True))
@click.option('--unsafe', is_flag=True, help="If true, YAML will be parsed unsafely. Only use on trusted datasets. Only valid if suffix is yaml")
def main(path, product_name, config, unsafe):
    path = os.path.abspath(path)
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
    iterate_datasets(path, product_name, config, unsafe)

if __name__ == "__main__":
    main()