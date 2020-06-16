# ODC Manual Indexer

This purpose of this repository is to provide convenient means of indexing data for an ODC installation.

# Indexing with Docker 

`docker run -e DB_DATABASE=DB_DATABASE -e DB_HOSTNAME`

# Indexing with Kubernetes.

First, run these commands:
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

Index the data.
Product definitions and indexing scripts are in directories in the starting directory - `/Datacube/S3_scripts`. These directories are named for the satellites - such as Landsat. You can run `wget` to retrieve desired, missing product definition YAML files from [here](https://github.com/opendatacube/datacube-core/tree/develop/docs/config_samples/dataset_types).

Example: To index Landsat 8 data in the deafrica-data S3 bucket, run the following command in the `S3_scripts` directory:
`python3 Landsat/index_scripts/ls8_public_bucket.py <bucket> -p usgs/c1/l8 --suffix=".xml"`.

Here is a table showing the paths, descriptions, and commands for indexing data on remote data sources.

| Path                       | Description                               | Command                                                              |
|----------------------------|-------------------------------------------|----------------------------------------------------------------------|
| s3://sentinel-s2-l1c/tiles | AWS Open Data Sentinel 2 (Requester Pays) | python3 ls_public_bucket.py sentinel-s2-l1c -p tiles --suffix=".xml" |