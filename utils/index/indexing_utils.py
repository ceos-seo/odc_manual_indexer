from osgeo import osr
from collections import ChainMap
import yaml
import os

prod_names_to_types = {}
prod_names_to_platforms = {}
for root, _, files in os.walk(f"{os.environ['WORKDIR']}/prod_defs"):
    for file in files:
        if file.endswith('.yaml'):
            yaml_path = os.path.join(root, file)
            prod_info = yaml.safe_load(open(yaml_path))
            prod_name = prod_info['name']
            # Product type
            prod_type = prod_info['metadata'].get('product_type', '')
            prod_names_to_types[prod_name] = prod_type
            # Product platform
            try:
                prod_plat = prod_info['metadata']['platform']['code']
            except:
                prod_plat = ''
            prod_names_to_platforms[prod_name] = prod_plat

# TODO
# prod_type_meas_file_layers = \
#     {}

# A mapping of product types to file match expressions to measurements in those files.
prod_type_file_match_exprs = \
    {'MavicMini': {
        'Ortho*.tif': ['red', 'green', 'blue', 'alpha']
    }}

# A map of products to maps of measurement names 
# to substrings uniquely contained in corresponding file names.
products_meas_file_unq_substr_map = \
    {'black_marble_night_lights':
     {'DNB_BRDF_corrected_NTL': 'DNB_BRDF-Corrected_NTL',
      'DNB_Lunar_Irradiance': 'DNB_Lunar_Irradiance',
      'gap_filled_DNB_BRDF_corrected_NTL': 'Gap_Filled_DNB_BRDF-Corrected_NTL',
      'latest_high_quality_retrieval': 'Latest_High_Quality_Retrieval',
      'mandatory_quality_flag': 'Mandatory_Quality_Flag',
      'QF_cloud_mask': 'QF_Cloud_Mask',
      'snow_flag': 'Snow_Flag'}
     }


def get_coords(geo_ref_points, spatial_ref):
    t = osr.CoordinateTransformation(spatial_ref, spatial_ref.CloneGeogCS())

    def transform(p):
        lon, lat, z = t.TransformPoint(p['x'], p['y'])
        # print("transform lon lat:", lon, lat, type(lon))
        return {'lon': str(lon), 'lat': str(lat)}

    return {key: transform(p) for key, p in geo_ref_points.items()}


def get_s3_url(bucket_name, obj_key):
    return 's3://{bucket_name}/{obj_key}'.format(
        bucket_name=bucket_name, obj_key=obj_key)
