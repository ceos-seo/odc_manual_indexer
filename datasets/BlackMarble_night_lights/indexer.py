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
import re

from multiprocessing import Process, current_process, Queue, Manager, cpu_count
from time import sleep, time
from queue import Empty

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
    # print(f'(minx, maxx), (miny, maxy): {(minx, maxx), (miny, maxy)}')

    data_np_arr = rasterio.open(tif_path).read(1)
    x_res = (maxx - minx) / data_np_arr.shape[1]
    y_res = (maxy - miny) / data_np_arr.shape[0]
    return x_res, y_res

def absolutify_paths(doc):
    for band in doc['image']['bands'].values():
        band['path'] = os.path.abspath(band['path'])
    return doc

def make_metadata_doc(path, product_name):
    sensing_time = '1970-01-01'
    for DEM_tif_file_path in glob.glob(path + '/DEM-*.tif'):
        geo_ref_points = get_geo_ref_points(DEM_tif_file_path)
        src_crs = 'EPSG:' + str(rasterio.open(DEM_tif_file_path).crs.to_epsg())
        DEM_x_res, DEM_y_res = get_res(geo_ref_points, DEM_tif_file_path, src_crs)
    for ortho_tif_file_path in glob.glob(path + '/Ortho-*.tif'):
        ortho_x_res, ortho_y_res = get_res(geo_ref_points, ortho_tif_file_path, src_crs)
        # pass
    x_res = min(DEM_x_res, ortho_x_res)
    y_res = min(DEM_y_res, ortho_y_res)
    print(f'x_res, y_res: {x_res, y_res}')
    print(f'src_crs: {src_crs}')
    
    doc_bands = {}
    band_data = {'layer': 1}
    # print(f'band_data: {band_data}')
    doc = {
        'id': str(uuid.uuid5(uuid.NAMESPACE_URL, path)),
        'product': {'name': product_name},
        'product_type': 'SurfaceRadiance',
        'creation_dt': '1970-01-01', # TODO: How to determine creation_dt from the TIFs?
        'platform': {'code': 'BlackMarble'},
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
            'bands': {
                'elevation': {'path': DEM_tif_file_path},
                'red':       {'path': ortho_tif_file_path, 'layer': 1},
                'green':     {'path': ortho_tif_file_path, 'layer': 2},
                'blue':      {'path': ortho_tif_file_path, 'layer': 3},
                'alpha':     {'path': ortho_tif_file_path, 'layer': 4},
            } 
        },
        'lineage': {'source_datasets': {}},
    }
    doc = absolutify_paths(doc)
    print(f'doc: {doc}')
    return doc

def get_s3_url(bucket_name, obj_key):
    return 's3://{bucket_name}/{obj_key}'.format(
        bucket_name=bucket_name, obj_key=obj_key)

def add_dataset(doc, product_name, uri, index):
    doc_id = doc['id']
    logging.info("Indexing dataset: {} with URI: {}".format(doc_id, uri))
    print(f'type(doc_id): {type(doc_id)}')
    print(f'type(uri): {type(uri)}')

    resolver = Doc2Dataset(index)
    dataset, err  = resolver(doc, uri)
    print(f'dataset: {dataset}')
    print(f'err: {err}')
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
            # print(f'path in worker(): {path}')
            if path == GUARDIAN:
                break
            logging.info("Processing %s %s", path, current_process())

            data = make_metadata_doc(path, product_name)
            if data:
                uri = 'file:/' + data['image']['bands']['elevation']['path']
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
        # print(f'path: {path}')
        if not dirs: # This is a leaf directory.
            # DEM_match, Ortho_match = False, False
            for file_str in files:
                # print(f'file_str: {file_str}')
                # Every .h5 file in a leaf directory 
                # constitutes a scene.
                if re.search('.*.h5$', file_str) is not None:
                    count += 1
                    queue.put(os.path.join(root, file_str))
                # DEM_match = 'DEM-' in file_str if not DEM_match else True
                # Ortho_match = 'Ortho-' in file_str if not Ortho_match else True
                # if DEM_match and Ortho_match: 
                    # break
            # if DEM_match and Ortho_match:
                # count += 1
                # queue.put(root)
    
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