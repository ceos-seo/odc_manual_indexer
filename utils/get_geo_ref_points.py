import rasterio

def get_geo_ref_points_tiff_path(tiff_path):
    ds = rasterio.open(tiff_path)
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

def get_geo_ref_points_info_landsat_c1_l2(info):
    return {
        'ul': {'x': info['CORNER_UL_PROJECTION_X_PRODUCT'], 'y': info['CORNER_UL_PROJECTION_Y_PRODUCT']},
        'ur': {'x': info['CORNER_UR_PROJECTION_X_PRODUCT'], 'y': info['CORNER_UR_PROJECTION_Y_PRODUCT']},
        'll': {'x': info['CORNER_LL_PROJECTION_X_PRODUCT'], 'y': info['CORNER_LL_PROJECTION_Y_PRODUCT']},
        'lr': {'x': info['CORNER_LR_PROJECTION_X_PRODUCT'], 'y': info['CORNER_LR_PROJECTION_Y_PRODUCT']},
    }