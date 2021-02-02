# Derived from https://blackmarble.gsfc.nasa.gov/tools/OpenHDF5.py
import gdal, os, re
from pathlib import Path

import click

@click.command(help='Enter the absolute or relative input and output paths to data to convert from HDF5 to GeoTIFFs.')
@click.argument('input_path')
@click.argument('output_path')
def main(input_path, output_path):
    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)

    ## List input raster files
    os.chdir(input_path)
    hdf5_files = [file_str for file_str in os.listdir(os.getcwd()) if re.search('.*.h5$', file_str)]
    # rasterFiles = os.listdir(os.getcwd())
    # print(hdf5_files)

    fileExtension = "_BBOX.tif"

    for hdf5_file in hdf5_files:
        # Get file name prefix
        # hdf5_path = Path(os.path.join(input_path, hdf5_file))
        # base_file_path = hdf5_path.with_suffix('')
        base_file_name = Path(hdf5_file).with_suffix('')
        output_file_path = os.path.join(output_path, base_file_name)        
        os.mkdir(output_file_path)
        # base_file_name = os.path.basename(base_file_path)
        # print(f'base_file_name: {base_file_name}')
        # rasterFilePre = hdf5_file[:-3]
        # print(f'rasterFilePre: {rasterFilePre}')

        ## Open HDF file
        hdflayer = gdal.Open(hdf5_file, gdal.GA_ReadOnly)

        # print (f'hdflayer: " {hdflayer}')
        # print (f'hdflayer.GetSubDatasets(): " {hdflayer.GetSubDatasets()}')

        # Open raster layer
        #hdflayer.GetSubDatasets()[0][0] - for first layer
        #hdflayer.GetSubDatasets()[1][0] - for second layer ...etc
        subhdflayers = hdflayer.GetSubDatasets()
        for subhdflayer in subhdflayers:
            subhdflayer = subhdflayer[0]
            rlayer = gdal.Open(subhdflayer, gdal.GA_ReadOnly)
            #outputName = rlayer.GetMetadata_Dict()['long_name']

            #Subset the Long Name
            outputName = subhdflayer[92:]
            # print(f'outputName: {outputName}')
            outputNameNoSpace = outputName.strip().replace(" ","_").replace("/","_")
            # print(f'outputNameNoSpace: {outputNameNoSpace}')
            outputNameFinal = outputNameNoSpace + str(base_file_name) + fileExtension
            # print(f'outputNameFinal: {outputNameFinal}')

            outputRaster = os.path.join(output_file_path, outputNameFinal)
            # print(f'outputRaster: {outputRaster}')

            #collect bounding box coordinates
            HorizontalTileNumber = int(rlayer.GetMetadata_Dict()["HorizontalTileNumber"])
            VerticalTileNumber = int(rlayer.GetMetadata_Dict()["VerticalTileNumber"])
                
            WestBoundCoord = (10*HorizontalTileNumber) - 180
            NorthBoundCoord = 90-(10*VerticalTileNumber)
            EastBoundCoord = WestBoundCoord + 10
            SouthBoundCoord = NorthBoundCoord - 10

            EPSG = "-a_srs EPSG:4326" #WGS84

            translateOptionText = EPSG + " -a_ullr " + str(WestBoundCoord) + " " + str(NorthBoundCoord) + " " + str(EastBoundCoord) + " " + str(SouthBoundCoord)
            # print(f'translateOptionText: {translateOptionText}')

            translateoptions = gdal.TranslateOptions(gdal.ParseCommandLine(translateOptionText))
            gdal.Translate(outputRaster, rlayer, options=translateoptions)

            # hdf5_path = Path(os.path.join(input_path, hdf5_file))
            # base_file_path = hdf5_path.with_suffix('')
            # output_file_path = base_file_path.with_suffix('.tif')

            # print('gdal_translate -a_srs "EPSG:4326" '\
                    #   f'\'HDF5:"{hdf5_path}"\' {base_file_path}.tiff')

            # os.system('gdal_translate -a_srs "EPSG:4326" '\
                    #   f'\'HDF5:"{hdf5_path}"\' {base_file_path}.tiff')

            # gdal.Translate(output_file_path, hdf5_path, options=gdal.TranslateOptions(gdal.ParseCommandLine(translateOptionText)))

            #Display image in QGIS (run it within QGIS python Console) - remove comment to display
            #iface.addRasterLayer(outputRaster, outputNameFinal)

if __name__ == "__main__":
    main()