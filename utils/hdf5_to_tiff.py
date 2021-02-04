# Derived from https://blackmarble.gsfc.nasa.gov/tools/OpenHDF5.py
import gdal, os, re
from pathlib import Path
from multiprocessing import Process, Queue, Manager, cpu_count

import click

GUARDIAN = "GUARDIAN_QUEUE_EMPTY"

@click.command(help='Enter the absolute or relative input and output paths to data to convert from HDF5 to GeoTIFFs.')
@click.argument('input_path')
@click.argument('output_path')
def main(input_path, output_path):
    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)

    # List input raster files.
    os.chdir(input_path)
    hdf5_files = [file_str for file_str in os.listdir(os.getcwd()) if re.search('.*.h5$', file_str)]

    fileExtension = ".tif"

    def worker(queue):
        while True:
            hdf5_file = queue.get(timeout=60)

            if hdf5_file == GUARDIAN:
                break

            # Create a directory to hold the TIFFs.
            base_file_name = Path(hdf5_file).with_suffix('')
            output_file_path = os.path.join(output_path, base_file_name)
            os.makedirs(output_file_path, exist_ok=True)

            ## Open the HDF file.
            hdflayer = gdal.Open(hdf5_file, gdal.GA_ReadOnly)

            # Open raster layers.
            subhdflayers = hdflayer.GetSubDatasets()
            for subhdflayer in subhdflayers:
                subhdflayer = subhdflayer[0]
                rlayer = gdal.Open(subhdflayer, gdal.GA_ReadOnly)

                # Subset the long name.
                outputName = subhdflayer[92:]
                outputNameNoSpace = outputName.strip().replace(" ","_").replace("/","_")
                outputNameFinal = outputNameNoSpace + '_' + str(base_file_name) + fileExtension

                outputRaster = os.path.join(output_file_path, outputNameFinal)

                # Collect bounding box coordinates.
                HorizontalTileNumber = int(rlayer.GetMetadata_Dict()["HorizontalTileNumber"])
                VerticalTileNumber = int(rlayer.GetMetadata_Dict()["VerticalTileNumber"])
                    
                WestBoundCoord = (10*HorizontalTileNumber) - 180
                NorthBoundCoord = 90-(10*VerticalTileNumber)
                EastBoundCoord = WestBoundCoord + 10
                SouthBoundCoord = NorthBoundCoord - 10

                EPSG = "-a_srs EPSG:4326" #WGS84

                translateOptionText = EPSG + " -a_ullr " + str(WestBoundCoord) + " " + str(NorthBoundCoord) + " " + str(EastBoundCoord) + " " + str(SouthBoundCoord)

                translateoptions = gdal.TranslateOptions(gdal.ParseCommandLine(translateOptionText))
                gdal.Translate(outputRaster, rlayer, options=translateoptions)

                #Display image in QGIS (run it within QGIS python Console) - remove comment to display
                #iface.addRasterLayer(outputRaster, outputNameFinal)
            queue.task_done()

            # Print progress.
            num_items_in_queue = queue.qsize()
            num_items_to_process = len(hdf5_files)
            num_items_processed = num_items_to_process-num_items_in_queue
            print(f'Processed {num_items_processed} of {num_items_to_process} files ({num_items_processed/num_items_to_process:.2%})')

    manager = Manager()
    queue = manager.Queue()
    worker_count = cpu_count()
    processess = []

    for i in range(worker_count):
        proc = Process(target=worker, args=(queue,))
        processess.append(proc)
        proc.start()

    for i, hdf5_file in enumerate(hdf5_files):
        queue.put(hdf5_file)

    for i in range(worker_count):
        queue.put(GUARDIAN)

    for proc in processess:
        proc.join()
    
if __name__ == "__main__":
    main()