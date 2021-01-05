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
import rasterio
import gdal
from gdalconst import GA_ReadOnly
import glob
import xarray as xr

from multiprocessing import Process, current_process, Queue, Manager, cpu_count
from time import sleep, time
from queue import Empty

GUARDIAN = "GUARDIAN_QUEUE_EMPTY"
AWS_PDS_TXT_SUFFIX = "MTL.txt"
LANDSAT_XML_SUFFIX = 'T1.xml'
GENERAL_LANDSAT_XML_SUFFIX = '.xml'

MTL_PAIRS_RE = re.compile(r'(\w+)\s=\s(.*)')

bands_ls8_l2 = [
    ('1', 'coastal_aerosol'),
    ('2', 'blue'),
    ('3', 'green'),
    ('4', 'red'),
    ('5', 'nir'),
    ('6', 'swir1'),
    ('7', 'swir2'),
    ('10', 'tirs'),
    ('QUALITY', 'pixel_qa')
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

band_file_map_l57 = {
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

band_file_map_l8 = {
    'coastal_aerosol': 'sr_band1',
    'blue': 'sr_band2',
    'green': 'sr_band3',
    'red': 'sr_band4',
    'nir': 'sr_band5',
    'swir1': 'sr_band6',
    'swir2': 'sr_band7',
    'pixel_qa': 'pixel_qa',
    'radsat_qa': 'radsat_qa',
    'sr_aerosol': 'sr_aerosol'
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

def get_geo_ref_points(tif_path):
    # data = gdal.Open(tif_path, GA_ReadOnly)
    # geoTransform = data.GetGeoTransform()
    # print(f'geoTransform: {geoTransform}')
    # minx = geoTransform[0]
    # maxy = geoTransform[3]
    # maxx = minx + geoTransform[1] * data.RasterXSize
    # miny = maxy + geoTransform[5] * data.RasterYSize
    # miny = geoTransform[0]
    # maxx = geoTransform[3]
    # maxy = miny + geoTransform[1] * data.RasterXSize
    # minx = maxx + geoTransform[5] * data.RasterYSize
    ds = rasterio.open(tif_path)
    minx = ds.bounds.left
    maxx = ds.bounds.right
    miny = ds.bounds.bottom
    maxy = ds.bounds.top
    # print(f'minx, maxx, miny, maxy: {minx, maxx, miny, maxy}')
    return {
        'ul': {'x': minx, 'y': maxy}, 
        'ur': {'x': maxx, 'y': maxy},
        'll': {'x': minx, 'y': miny}, 
        'lr': {'x': maxx, 'y': miny}
    }

def get_coords(geo_ref_points, tif_path, dst_crs):
    DEM_ds = xr.open_rasterio(tif_path)
    src_crs = DEM_ds.crs
    from pyproj import Transformer
    # src_crs = CRS.from_string(src_crs)
    # print(f'src_crs: {src_crs}')
    transformer = Transformer.from_crs(src_crs, dst_crs)
    import copy
    coords = copy.deepcopy(geo_ref_points)
    for corner in coords:
        coords[corner]['y'], coords[corner]['x'] = \
            transformer.transform(coords[corner]['x'], coords[corner]['y'])
    return coords
    # from pyproj import Proj, transform
    # t = osr.CoordinateTransformation(spatial_ref, spatial_ref.CloneGeogCS())

    # def transform(p):
        # lon, lat, z = t.TransformPoint(p['x'], p['y'])
        # print("transform lon lat:", lon, lat, type(lon))
        # return {'lon': str(lon), 'lat': str(lat)}

    # return {key: transform(p) for key, p in geo_ref_points.items()}

def get_res():


def satellite_ref(sat):
    """
    To load the band_names for referencing either LANDSAT8 or LANDSAT7 bands
    """
    if sat == 'LANDSAT_8':
        sat_img = bands_ls8_l2
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


def absolutify_paths(doc):
    # objt_key = format_obj_key(obj_key)
    for band in doc['image']['bands'].values():
        # print(f"band['path']: {band['path']}")
        # band['path'] = get_s3_url(bucket_name, objt_key + '/'+band['path'])
        band['path'] = os.path.abspath(band['path'])
        # print(f"band['path']: {band['path']}")
    return doc


def make_xml_doc(xmlstring, bucket_name, object_key):
    """ principle function to convert xml metadata into a JSON doc 
        need to document each section here...
    """

    xmlstring = re.sub(r'\sxmlns="[^"]+"', '', xmlstring, count=1)
    doc = ElementTree.fromstring(xmlstring)

    satellite = doc.find('.//satellite').text
    data_provider = doc.find('.//data_provider').text
    instrument = doc.find('.//instrument').text
    path = doc.find('.//wrs').attrib['path']
    row = doc.find('.//wrs').attrib['row']
    region_code = f"{int(path):03d}{int(row):03d}"

    # other params like cloud_shadow, snow_ice, tile_grid, orientation_angle are also available

    acquisition_date = doc.find('.//acquisition_date').text
    scene_center_time = doc.find('.//scene_center_time').text
    center_dt = acquisition_date + " " + scene_center_time
    level = doc.find('.//product_id').text.split('_')[1]
    start_time = center_dt
    end_time = center_dt

    satellite_string = "{}/{}".format(data_provider, satellite)
    images = satellite_ref(satellite_string)
    if satellite_string == 'USGS/EROS/LANDSAT_8':
        band_file_map = band_file_map_l8
    else:
        band_file_map = band_file_map_l57
    
    logging.info("Working on data for satellite: {}".format(satellite_string))

    # cs_code = '5072'
    utm_zone = doc.find('.//projection_information/utm_proj_params/zone_code').text
    spatial_ref = 'epsg:326' + utm_zone
    west = doc.find('.//bounding_coordinates/west').text
    east = doc.find('.//bounding_coordinates/east').text
    north = doc.find('.//bounding_coordinates/north').text
    south = doc.find('.//bounding_coordinates/south').text

    if float(west) < -179:
        west = str(float(west) + 360)

    if float(east) < -179:
        east = str(float(east) + 360)

    coord = {
          'ul':
             {'lon': west,
              'lat': north},
          'ur':
             {'lon': east,
              'lat': north},
          'lr':
             {'lon': east,
              'lat': south},
          'll':
             {'lon': west,
              'lat': south}}

    projection_parameters = doc.find('.//projection_information')
    for corner_point in projection_parameters.findall('corner_point'):
        if corner_point.attrib['location'] in 'UL':
           westx = corner_point.attrib['x']
           northy = corner_point.attrib['y']
        if corner_point.attrib['location'] in 'LR':
           eastx = corner_point.attrib['x']
           southy = corner_point.attrib['y']

    westxf = float(westx) * 1.0
    eastxf = float(eastx) * 1.0
    northyf = float(northy) * 1.0
    southyf = float(southy) * 1.0

    geo_ref_points = {
          'ul':
             {'x': westxf,
              'y': northyf},
          'ur':
             {'x': eastxf,
              'y': northyf},
          'lr':
             {'x': eastxf,
              'y': southyf},
          'll':
             {'x': westxf,
              'y': southyf}}

    band_dict =  get_band_filenames(doc)
    try:
        docdict = {
            'id': str(uuid.uuid5(uuid.NAMESPACE_URL, get_s3_url(bucket_name, object_key))),
            # 'cloud_cover': cloud_cover,
            # 'fill': fill,
            'processing_level': str(level),
            # This is hardcoded now... needs to be not hardcoded!
            'product_type': 'LaSRCollection2',
            'creation_dt': acquisition_date,
            'region_code': region_code,
            'platform': {'code': satellite},
            'instrument': {'name': instrument},
            'extent': {
                'from_dt': str(start_time),
                'to_dt': str(end_time),
                'center_dt': str(center_dt),
                'coord': coord,
            },
            'format': {'name': 'GeoTiff'},
            'grid_spatial': {
                'projection': {
                    'geo_ref_points': geo_ref_points,
                    'spatial_reference': spatial_ref,
                }
            },
            'image': {
                'bands': {
                    image[1]: {
                        'path': band_dict[band_file_map[image[1]]],
                        # 'layer': 1,
                    } for image in images
                }
            },
            'lineage': {'source_datasets': {}}
        }
    except KeyError as e:
        logging.error("Failed to handle metadata file: {} with error: {}".format(object_key, e))
        return None
    docdict = absolutify_paths(docdict, bucket_name, object_key)

    logging.info("Prepared docdict for metadata file: {}".format(object_key))
    # print(json.dumps(docdict, indent=2))

    return docdict

def make_metadata_doc(path):
    # mtl_data = BeautifulSoup(mtl_data, "lxml")
    # print(f"mtl_data: {mtl_data}")

    # for DEM_tif_file in glob.glob(path + '/DEM-*.tif'):
    #     # print(f'DEM_tif_file: {DEM_tif_file}')
    #     data = gdal.Open(DEM_tif_file, GA_ReadOnly)
    #     geoTransform = data.GetGeoTransform()
    #     minx = geoTransform[0]
    #     maxy = geoTransform[3]
    #     maxx = minx + geoTransform[1] * data.RasterXSize
    #     miny = maxy + geoTransform[5] * data.RasterYSize
        # CRS = rasterio.open(DEM_tif_file).crs
        # print(f'CRS: {CRS, type(CRS)}')
        # print(f'DEM minx, miny, maxx, maxy: {minx, miny, maxx, maxy}')
    # for ortho_tif_file in glob.glob(path + '/Ortho-*.tif'):
    #     data = gdal.Open(ortho_tif_file, GA_ReadOnly)
    #     geoTransform = data.GetGeoTransform()
    #     minx = geoTransform[0]
    #     maxy = geoTransform[3]
    #     maxx = minx + geoTransform[1] * data.RasterXSize
    #     miny = maxy + geoTransform[5] * data.RasterYSize
    #     print(f'Ortho minx, miny, maxx, maxy: {minx, miny, maxx, maxy}')

    # del data

    # mtl_product_info = mtl_data['PRODUCT_METADATA']
    # mtl_metadata_info = mtl_data['METADATA_FILE_INFO']
    # satellite = mtl_product_info['SPACECRAFT_ID']
    # satellite = mtl_data.image_attributes.spacecraft_id.text
    # instrument = mtl_product_info['SENSOR_ID']
    # instrument = mtl_data.image_attributes.sensor_id.text
    # acquisition_date = mtl_product_info['DATE_ACQUIRED']
    # acquisition_date = mtl_data.image_attributes.date_acquired.text
    # scene_center_time = mtl_product_info['SCENE_CENTER_TIME']
    # scene_center_time = mtl_data.image_attributes.scene_center_time.text
    # level = mtl_product_info['DATA_TYPE']
    # sensing_time = acquisition_date + ' ' + scene_center_time
    sensing_time = '1970-01-01'
    # cs_code = 32600 + mtl_data['PROJECTION_PARAMETERS']['UTM_ZONE']
    # cs_code = 32600 + mtl_data.projection_attributes.utm_zone.text
    # label = mtl_metadata_info['LANDSAT_SCENE_ID']
    # label = mtl_data.level1_processing_record.landsat_scene_id.text
    # print(f"satellite, instrument: {satellite}, {instrument}")
    # print(f"acquisition_date, scene_center_time: {acquisition_date}, {scene_center_time}")
    # print(f"processing_level, sensing_time: {processing_level}, {sensing_time}")
    # spatial_ref = osr.SpatialReference()
    # spatial_ref.ImportFromEPSG(cs_code)
    # spatial_ref.ImportFromEPSG(4326)
    # print(f'spatial_ref: {spatial_ref, type(spatial_ref)}')
    for DEM_tif_file_path in glob.glob(path + '/DEM-*.tif'):
        geo_ref_points = get_geo_ref_points(DEM_tif_file_path)
        # print(f'geo_ref_points: {geo_ref_points}')
        # crs = spatial_ref.GetAttrValue("AUTHORITY", 0) + ":" + spatial_ref.GetAttrValue("AUTHORITY", 1)
        # dst_crs = 'epsg:4326'
        # coords = get_coords(geo_ref_points, DEM_tif_file_path, dst_crs)
        # print(f'coords: {coords}')
        get_res(geo)
    for ortho_tif_file_path in glob.glob(path + '/Ortho-*.tif'):
        pass
    # print(f'src_crs: {src_crs, type(src_crs)}')
    # bands = satellite_ref(satellite)
    # print('bands:', bands)
    # print("mtl_data.product_contents:", mtl_data.product_contents)
    # print(f"mtl_data.product_contents.file_name_band_1: {mtl_data.product_contents.file_name_band_1}," \
        #   f"{getattr(mtl_data.product_contents, f'file_name_band_1').text}")
    
    # TODO: Delete block.
    # ds = rasterio.open(DEM_tif_file_path)
    # minx = ds.bounds.left
    # maxx = ds.bounds.right
    # miny = ds.bounds.bottom
    # maxy = ds.bounds.top
    # x_rng, y_rng = maxx - minx, maxy - miny
    # pixelSizeX, pixelSizeY = ds.res
    # print(f'pixelSizeX, pixelSizeY: {pixelSizeX, pixelSizeY}')

    doc_bands = {}
    band_data = {'layer': 1}
    doc = {
        'id': str(uuid.uuid5(uuid.NAMESPACE_URL, path)),
        # 'processing_level': processing_level,
        'product_name': product_name
        'product_type': 'CivilTrackerDrone',
        'creation_dt': '1970-01-01', # TODO: How to determine creation_dt from the TIFs?
        # 'label': label,
        'platform': {'code': 'CivilTracker'},
        # 'instrument': {'name': 'CivilTrackerDrone'},
        'extent': {
            'from_dt': sensing_time,
            'to_dt': sensing_time,
            'center_dt': sensing_time,
            'coord': coords,
                  },
        'format': {'name': 'GeoTiff'},
        'grid_spatial': {
            'projection': {
                'geo_ref_points': coords,
                'spatial_reference': dst_crs, 
                #'EPSG:%s' % cs_code,
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
    doc = absolutify_paths(doc)
    print("doc:", doc)
    return doc


def format_obj_key(obj_key):
    obj_key ='/'.join(obj_key.split("/")[:-1])
    return obj_key


def get_s3_url(bucket_name, obj_key):
    return 's3://{bucket_name}/{obj_key}'.format(
        bucket_name=bucket_name, obj_key=obj_key)


def add_dataset(doc, product_name, uri, index):
    # print("add_dataset doc:", doc)
    # print("add_dataset index:", index, type(index))
    doc_id = doc['id']
    logging.info("Indexing dataset: {} with URI:  {}".format(doc_id, uri))

    resolver = Doc2Dataset(index)
    # print(f"resolver: {resolver}")
    # print(f'uri: {uri}')
    dataset, err  = resolver(doc, uri)
    print(f"dataset, err: {dataset}, {err}")
    existing_dataset = index.datasets.get(doc_id)
    print(f"existing_dataset: {existing_dataset}")

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
            # obj = s3.Object(bucket_name, key).get(ResponseCacheControl='no-cache', RequestPayer='requester')
            # raw = obj['Body'].read()
            # raw_string = raw.decode('utf8')

            data = make_metadata_doc(path)
            # print(f'data: {data}')
            if data:
                uri = data['id']
                # uri = get_s3_url(bucket_name, key)
                
                # print("data:", data)
                # print(f"data: {type(data)}")
                # data = BeautifulSoup(data, "lxml")
                # print(f'data: {data}')
                # print(f"data.landsat_metadata_file.image_attributes.date_acquired.text:"
                    #   f"{data.landsat_metadata_file.image_attributes.date_acquired.text}")
                # cdt = data['creation_dt']

                # print(f"cdf:", cdt)
                # Only do the date check if we have dates set.
                # if cdt and start_date and end_date:
                    # Use the fact lexicographical ordering matches the chronological ordering
                    # if cdt >= start_date and cdt < end_date:
                        # add_dataset(data, uri, index, sources_policy)
                add_dataset(data, product_name, uri, index)
                # else:
                    # add_dataset(data, uri, index, sources_policy)
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

    # s3 = boto3.resource('s3')
    # bucket = s3.Bucket(bucket_name)
    # print(f"Bucket: {bucket_name} prefix: {str(prefix)}")
    # logging.info("Bucket: %s prefix: %s ", bucket_name, str(prefix))
    # safety = 'safe' if not unsafe else 'unsafe'
    worker_count = cpu_count() * 2

    processess = []
    for i in range(worker_count):
        proc = Process(target=worker, args=(config, path, product_name, unsafe, queue,))
        processess.append(proc)
        proc.start()

    # Search the lowest-level directories with 'DEM-clip.tif' and 'Ortho-clip.tif' files.
    count = 0
    for root,dirs,files in os.walk(path):
        if not dirs: # This is a lowest-level subdirectory.
            # print(f'files: {files}')
            DEM_match, Ortho_match = False, False
            for file_str in files:
                # print(f'file_str: {file_str}')
                DEM_match = 'DEM-' in file_str if not DEM_match else True
                Ortho_match = 'Ortho-' in file_str if not Ortho_match else True
                if DEM_match and Ortho_match: 
                    break
            if DEM_match and Ortho_match:
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
# @click.option('--path', '-p', help="Pass the prefix of the object to the bucket")
# @click.option('--suffix', '-s', default=".yaml", help="Defines the suffix of the metadata_docs that will be used to load datasets. For AWS PDS bucket use MTL.txt")
# @click.option('--start_date', help="Pass the start acquisition date, in YYYY-MM-DD format")
# @click.option('--end_date', help="Pass the end acquisition date, in YYYY-MM-DD format")
# @click.option('--lat1', help="Pass the lower latitude")
# @click.option('--lat2', help="Pass the upper latitude")
# @click.option('--lon1', help="Pass the lower longitude")
# @click.option('--lon2', help="Pass the upper longitude")
@click.option('--unsafe', is_flag=True, help="If true, YAML will be parsed unsafely. Only use on trusted datasets. Only valid if suffix is yaml")
def main(path, product_name, config, unsafe):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
    # start_date = "2013-02-11" if start_date is None else start_date
    # end_date = "2029-12-31" if end_date is None else end_date
    # lat1 = -90 if lat1 is None else float(lat1)
    # lat2 = 90 if lat2 is None else float(lat2)
    # lon1 = -180 if lon1 is None else float(lon1)
    # lon2 = 180 if lon2 is None else float(lon2)
    # logging.info(f"lat1, lat2, lon1, lon2: {lat1, lat2, lon1, lon2}")
    iterate_datasets(path, product_name, config, unsafe)
   
if __name__ == "__main__":
    main()