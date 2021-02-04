from osgeo import osr

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