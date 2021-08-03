#!/usr/bin/env python3

# coding: utf-8

import os
import uuid
import logging
import click
import datacube
from datacube.index.hl import Doc2Dataset
from datacube.utils import changes
import rasterio
import glob
import xarray as xr

from multiprocessing import Process, current_process, Queue, Manager, cpu_count
from time import sleep, time
from queue import Empty

GUARDIAN = "GUARDIAN_QUEUE_EMPTY"

from utils.get_geo_ref_points import get_geo_ref_points_tiff_path

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

def make_metadata_doc(path, meas_to_file_paths, product_name, product_type, platform_code):
    sensing_time = '1970-01-01'
    
    # Select one of the files to get geospatial reference points for.
    first_meas_filepath = list(meas_to_file_paths.values())[0]
    geo_ref_points = get_geo_ref_points_tiff_path(first_meas_filepath)
    src_crs = 'EPSG:' + str(rasterio.open(first_meas_filepath).crs.to_epsg())

    from utils.index.indexing_utils import prod_type_meas_file_layers
    meas_file_layers = prod_type_meas_file_layers[product_type]
    
    doc_bands = {}
    for meas, file_path in meas_to_file_paths.items():
        doc_bands[meas] = {'path': file_path}
        layer_num = meas_file_layers.get(meas)
        if layer_num is not None:
            doc_bands[meas]['layer'] = layer_num

    doc = {
        'id': str(uuid.uuid5(uuid.NAMESPACE_URL, path)),
        'product': {'name': product_name},
        'product_type': product_type,
        'creation_dt': '1970-01-01', # TODO: How to determine creation_dt from the TIFs?
        'platform': {'code': platform_code},
        'extent': {
            'from_dt': sensing_time,
            'to_dt': sensing_time,
            'center_dt': sensing_time,
            'coord': geo_ref_points,
                  },
        'format': {'name': 'GeoTiff'},
        'grid_spatial': {
            'projection': {
                'geo_ref_points': geo_ref_points,
                'spatial_reference': src_crs, 
                            }
                        },
        'image': {
            'bands': doc_bands
        },
        'lineage': {'source_datasets': {}},
    }
    doc = absolutify_paths(doc)
    return doc

def get_s3_url(bucket_name, obj_key):
    return 's3://{bucket_name}/{obj_key}'.format(
        bucket_name=bucket_name, obj_key=obj_key)

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

def worker(config, path, product_name, product_type, platform_code, unsafe, queue):
    dc = datacube.Datacube(config=config)
    index = dc.index
    safety = 'safe' if not unsafe else 'unsafe'

    while True:
        try:
            data = queue.get(timeout=60)
            if data == GUARDIAN:
                break
            path, meas_to_file_paths = (*data,)
            logging.info("Processing %s %s", path, current_process())

            data = make_metadata_doc(path, meas_to_file_paths, product_name, product_type, platform_code)
            if data:
                uri = 'file:/' + os.path.abspath(path)
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

    dc = datacube.Datacube(config=config)
    prod_meas_set = set(dc.list_measurements().loc[product_name].name)
    prod_info = dc.list_products()
    product_type = prod_info[prod_info.name == product_name].product_type.values[0]
    platform_code = prod_info[prod_info.name == product_name].platform.values[0]

    worker_count = cpu_count() * 2

    processess = []
    for i in range(worker_count):
        proc = Process(target=worker, args=(config, path, product_name, product_type, platform_code, unsafe, queue,))
        processess.append(proc)
        proc.start()

    # Search the lowest-level directories with 'DEM-clip.tif' and 'Ortho-clip.tif' files.
    from utils.index.indexing_utils import prod_type_file_match_exprs, prod_type_meas_to_file_match_exprs
    from collections import ChainMap
    file_match_exprs_to_meas = prod_type_file_match_exprs[product_type]
    meas_to_file_match_exprs = \
        dict(ChainMap(*[{meas:expr for meas in meas_list} \
            for expr, meas_list in file_match_exprs_to_meas.items()]))
    file_match_exprs_remaining = set(meas_to_file_match_exprs[meas] for meas in prod_meas_set)
    count = 0
    for root,dirs,files in os.walk(path):
        if not dirs: # This is a lowest-level subdirectory.
            meas_to_file_paths = {}
            for file_str in files:
                for file_match_expr in file_match_exprs_remaining:
                    exprs_to_remove = []
                    if file_match_expr in file_str:
                        exprs_to_remove.append(file_match_expr)
                        for meas in file_match_exprs_to_meas[file_match_expr]:
                            meas_to_file_paths[meas] = os.path.join(root, file_str)
                for file_match_expr in exprs_to_remove:
                    file_match_exprs_remaining.remove(file_match_expr)
                if len(file_match_exprs_remaining) == 0:
                    count += 1
                    queue.put((root, meas_to_file_paths))
                    break
    
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
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
    iterate_datasets(path, product_name, config, unsafe)

if __name__ == "__main__":
    main()