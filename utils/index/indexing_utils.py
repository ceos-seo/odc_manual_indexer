from osgeo import osr
from collections import ChainMap

# Map of [product types] to (after processing) maps of [measurements] to 
# [file name expressions to match a file in each scene directory].
prod_type_file_match_exprs = \
        {'MavicMini': 
            {'Ortho-RGBA': ['red', 'green', 'blue', 'alpha'], 
             'DEM': ['elevation']}}
prod_type_meas_to_file_match_exprs = \
    {product_type: dict(ChainMap(*\
        [{meas:expr for meas in meas_list} for expr, meas_list in 
          prod_type_file_match_exprs[product_type].items()]))
     for product_type in prod_type_file_match_exprs}
# Map of product types to their layer numbers in their TIFFs.
prod_type_meas_file_layers = \
    {'MavicMini': 
        # 'elevation' is its own TIFF.
        {'red': 1, 'green': 2, 'blue': 3, 'alpha': 4}}

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