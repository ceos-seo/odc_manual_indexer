# ODC Manual Indexer

This purpose of this repository is to provide convenient means of indexing data for an ODC installation.

## Contents

* [Starting the Indexer](#starting)
    * [Starting with Docker](#starting_docker)
    * [Starting with Kubernetes](#starting_k8s)
* [Indexing Data](#indexing)
    * [Products](#products)
    * [Indexable Remote Datasets](#indexable_remote_datasets)
    * [Indexing Scripts](#indexing_scripts)

## <a name="starting"></a> Starting the Indexer
-------
The indexer can be run in Docker or in Kubernetes. Instructions for both are included below.

>### <a name="starting_docker"></a> Starting with Docker 
-------

In `docker/.env`, set `DB_HOSTNAME` to the hostname of the database server, set `DB_DATABASE` to the name of the ODC database, set `DB_USER` to the name of the user for the ODC database, set `DB_PASSWORD` to the password for the user, set `DB_PORT` to the port that the ODC database is aviailable on (default for Postgres is `5432`), set `AWS_ACCESS_KEY_ID` to your AWS access key ID, and set `AWS_SECRET_ACCESS_KEY` to your AWS secret access key.

Finally, run `make up` from the top-level directory to start the indexer and then run `make ssh` to connect to the container through a bash shell.

**Developers**: Run the **dev-\*** Make commands to run a development environment (e.g. **dev-up**, **dev-ssh**). The development environment uses a non-peristent ODC database tied to the lifecycle of the docker-compose collection, so Make targets like **dev-down** or **dev-restart** clears this database.

>### <a name="starting_k8s"></a> Starting with Kubernetes
-------

Run these commands to create k8s secrets for your AWS and ODC database credentials:
```
kubectl -n <namespace> create secret generic database-credentials \
--from-literal=DB_DATABASE=<ODC database name> \
--from-literal=DB_HOSTNAME=<ODC database hostname> \
--from-literal=DB_USERNAME=<ODC database username> \
--from-literal=DB_PASSWORD=<ODC database password> \
--from-literal=DB_PORT=<ODC database port>
```
```
kubectl -n <namespace> create secret generic aws-credentials \
--from-literal=AWS_ACCESS_KEY_ID=<AWS access key id> \
--from-literal=AWS_SECRET_ACCESS_KEY=<AWS secret access key>
```

In the `k8s/manual-indexer.yaml` file, after `iam.amazonaws.com/role:`, put the IAM role name of the k8s indexer role. The role must be able to read from the S3 buckets that contain the data that will be indexed.

Tag and push the production version of the application:
`docker build . -f docker/prod/Dockerfile -t <tag>`
`docker push <tag>`

Now set `spec: containers: image` in `k8s/manual-indexer.yaml` to that tag.

Run this command to create the manual indexer pod: `kubectl apply -n <namespace> -f k8s/manual-indexer.yaml`. In this pod, any data we index for the Data Cube will be indexed on the Data Cube database defined by the secrets we set in the first command.

Run `kubectl -n <namespace> get pods` to check if the new pods are running.

Run `kubectl -n <namespace> exec -it <manual-indexer-pod-name> bash` to enter a bash shell on the manual indexer pod.

## <a name="indexing"></a> Indexing Data
-------

Product definitions and indexing scripts are in directories in the starting directory - `/Datacube/manual-indexer`. These directories are named for the satellites or constellations (collections) of satellites - such as Landsat. You can run `wget` to retrieve desired, missing product definition YAML files from [here](https://github.com/opendatacube/datacube-core/tree/develop/docs/config_samples/dataset_types).

Example: To index Landsat 8 data in the deafrica-data S3 bucket, run the following commands in the starting directory:
`datacube product add Landsat/prod_defs/ls8_usgs_sr_scene.yaml`
`python3 Landsat/index_scripts/ls8_public_bucket.py <bucket> -p usgs/c1/l8 --suffix=".xml"`.

To add a product with a product definition at `<path>`, run `datacube product add <path>`

If there is no indexing script for a product, you should be able to index the data with a command like `datacube dataset add <path-to-dataset-documents>`. For example, commonly you will have a directory containing directories of scenes - 1 directory per scene - which each contain a dataset document. If this dataset document is called `metadata.yaml`, then run `datacube dataset add **/metadata.yaml` in the directory containing these scene directories.

>### <a name="products"></a> Products
-------

Here is a table showing, for each product, a description, the resolution, the projection, the path to the product definition file, and the origin of this file.

| Product | <div style="width:200px"></div>Description | Resolution | Projection | Product Definition Path | Origin |
|-----|-----|-----|-----|-----|-----|
| ls5_usgs_sr_scene | Landsat 5 Collection 1 Level 2 (SR) | 30m | EPSG:4326 | Landsat<br>/prod_defs<br>/ls5_usgs_sr_scene | [Origin](https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml) |
| ls7_usgs_sr_scene | Landsat 7 Collection 1 Level 2 (SR) | 30m | EPSG:4326 | Landsat<br>/prod_defs<br>/ls7_usgs_sr_scene | [Origin](https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml) |
| ls8_usgs_sr_scene | Landsat 8 Collection 1 Level 2 (SR) | 30m | EPSG:4326 | Landsat<br>/prod_defs<br>/ls8_usgs_sr_scene | [Origin](https://github.com/opendatacube/datacube-dataset-config/blob/master/products/ls_usgs_sr_scene.yaml) |
| jers_sar_mosaic | JERS-1 SAR (HH) mosaics generated for use in the Data Cube | 25m | EPSG:4326 | JERS-1<br>/prod_defs<br>/jers_sar_mosaic | [Origin](https://github.com/digitalearthafrica/config/blob/master/products/jers_sar_mosaic.yaml) |
| s2_ard_scene | Sentinel-2 Level 2A | 10-20m | varies | Sentinel-2<br>/L2A<br>/prod_defs<br>/s2_ard_scene_prod_def.yaml | N/A |

>### <a name="indexable_remote_datasets"></a> Indexable Remote Datasets
-------

There are many sources of directly indexable data. For example, there are some data sources on S3 - such as the [Landsat 8 Level 1 data on AWS](https://registry.opendata.aws/landsat-8/) - that the Open Data Cube supports indexing, so that whenever data is loaded with `datacube.Datacube.load()`, it is downloaded into memory from the remote data source.
This is convenient because data is loaded as needed, no storage costs are incurred, and scenes do not need to be ordered from websites like [EarthExplorer](https://earthexplorer.usgs.gov/) or the [Copernicus Open Access Hub](https://scihub.copernicus.eu/). 

Here is a table showing, for each data source, the dataset type (e.g. Sentinel-2, Landsat 8, etc.), the path to the data, a description, commands for indexing the data, and the compatible products.

| Dataset Type | Path | <div style="width:100px"></div>Description | Command | Products |
|-----|-----|-----|-----|-----|
| Sentinel-2 Level 2 | s3://sentinel-s2-l1c/tiles | AWS Open Data Sentinel 2 Level 1C (Requester Pays) | N/A | N/A |
| Landsat 7 Level 2 | s3://deafrica-data/usgs/c1/l7 | Landsat 7 data for Africa (from GA - minimize queries) | python3 Landsat/index_scripts/ls7_public_bucket.py deafrica-data -p usgs/c1/l7 --suffix=".xml" | ls7_usgs_sr_scene |
| Landsat 8 Level 2 | s3://deafrica-data/usgs/c1/l8 | Landsat 8 data for Africa (from GA - minimize queries) | python3 Landsat/index_scripts/ls8_public_bucket.py deafrica-data -p usgs/c1/l8 --suffix=".xml" | ls8_usgs_sr_scene |

>### <a name="indexing_scripts"></a> Indexing Scripts
-------

Here is a table showing, for each indexing script, the dataset type, the path to the script and the calling format (e.g. parameter format), an example, and the origin for the script.

| Dataset Type | Path-Format | Example | Origin |
|-----|-----|-----|-----|
| Landsat 7 | Landsat/index_scripts/ls7_public_bucket.py <bucket (S3 bucket name)> -p <path (path in bucket in which to recursively search for Data Cube datasets to index)> --suffix=<string (The file suffix of dataset metadata documents)> | ls7_public_bucket.py data-bucket -p usgs/l7 --suffix=".xml" | [Origin](https://github.com/opendatacube/datacube-dataset-config/blob/master/old-prep-scripts/ls_public_bucket.py) |
| Landsat 8 | Landsat/index_scripts/ls8_public_bucket.py <bucket (S3 bucket name)> -p <path (path in bucket in which to recursively search for Data Cube datasets to index)> --suffix=<string (The file suffix of dataset metadata documents)> | ls8_public_bucket.py data-bucket -p usgs/l8 --suffix=".xml" | [Origin](https://github.com/opendatacube/datacube-dataset-config/blob/master/old-prep-scripts/ls_public_bucket.py) |