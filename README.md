# ODC Manual Indexer

This purpose of this repository is to provide convenient means of indexing data for an ODC installation.

## Starting with Docker 

In `docker/.env`, set `DB_HOSTNAME` to the hostname of the database server, set `DB_DATABASE` to the name of the ODC database, set `DB_USER` to the name of the user for the ODC database, set `DB_PASSWORD` to the password for the user, set `DB_PORT` to the port that the ODC database is aviailable on (default for Postgres is `5432`), set `AWS_ACCESS_KEY_ID` to your AWS access key ID, and set `AWS_SECRET_ACCESS_KEY` to your AWS secret access key.

Finally, run `make up` from the top-level directory to start the indexer and then run `make ssh` to connect to the container through a bash shell.

## Starting with Kubernetes

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

Run this command to create the manual indexer pod: `kubectl apply -n <namespace> -f k8s/manual-indexer.yaml`. In this pod, any data we index for the Data Cube will be indexed on the Data Cube database defined by the secrets we set in the first command.

Run `kubectl -n odchub get pods` to check if the new pods are running.

Run `kubectl -n odchub exec -it <manual-indexer-pod-name> /bin/bash` to enter a bash shell on the manual indexer pod.

## Indexing data

Product definitions and indexing scripts are in directories in the starting directory - `/Datacube/S3_scripts`. These directories are named for the satellites - such as Landsat. You can run `wget` to retrieve desired, missing product definition YAML files from [here](https://github.com/opendatacube/datacube-core/tree/develop/docs/config_samples/dataset_types).

Example: To index Landsat 8 data in the deafrica-data S3 bucket, run the following commands in the `S3_scripts` directory:
`datacube product add Landsat/prod_defs/ls8_usgs_sr_scene.yaml`
`python3 Landsat/index_scripts/ls8_public_bucket.py <bucket> -p usgs/c1/l8 --suffix=".xml"`.

Here is a table of products.
To add a product with a product definition at `<path>`, run `datacube product add <path>`

| Product | <div style="width:200px"></div>Description | Path |
|---------|---------------|------|
| ls5_usgs_sr_scene | Landsat 5 Collection 1 Level 2 (SR), 30m Resolution, UTM Projection (EPSG:4326) | Landsat<br>/prod_defs<br>/ls5_usgs_sr_scene |
| ls7_usgs_sr_scene | Landsat 7 Collection 1 Level 2 (SR), 30m Resolution, UTM Projection (EPSG:4326) | Landsat<br>/prod_defs<br>/ls7_usgs_sr_scene |
| ls8_usgs_sr_scene | Landsat 8 Collection 1 Level 2 (SR), 30m Resolution, UTM Projection (EPSG:4326) | Landsat<br>/prod_defs<br>/ls8_usgs_sr_scene |

Here is a table showing, for each product, the paths, descriptions, and commands for indexing data on remote data sources.

| Data Path | <div style="width:100px"></div>Description | Command |
|------|-------------|---------|
| s3://sentinel-s2-l1c/tiles | AWS Open Data Sentinel 2 Level 1C (Requester Pays) |  |
| s3://deafrica-data/usgs/c1/l7 | Landsat 7 data for Africa (from GA - minimize queries) | python3 ls7_public_bucket.py deafrica-data -p usgs/c1/l7 --suffix=".xml"
| s3://deafrica-data/usgs/c1/l8 | Landsat 8 data for Africa (from GA - minimize queries) | python3 Landsat/index_scripts/ls8_public_bucket.py deafrica-data -p usgs/c1/l8 --suffix=".xml" |
