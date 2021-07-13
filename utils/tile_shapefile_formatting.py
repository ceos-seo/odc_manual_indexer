import os

import geopandas as gpd

def path_row_geojson_to_min_max_xy_fmt():
    old_cwd = os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    path_row_data = gpd.read_file('USGS_path_rows.geojson')
    os.chdir(old_cwd)
    
    def extract_path_rows(path_row_str):
        path_str, row_str = path_row_str.split('_')
        return path_str, row_str
    path_row_data['Path'], path_row_data['Row'] = \
        zip(*path_row_data['Name'].map(lambda path_row_str: extract_path_rows(path_row_str)))
    
    def get_min_max_x_y(geom):
        x, y = geom.exterior.coords.xy
        return min(x), max(x), min(y), max(y)
    path_row_data['min_x'], path_row_data['max_x'], \
    path_row_data['min_y'], path_row_data['max_y'] = \
        zip(*path_row_data.geometry.map(lambda geom: get_min_max_x_y(geom)))
    
    return path_row_data[['Path', 'Row', 'min_x', 'max_x', 'min_y', 'max_y', 'geometry']]