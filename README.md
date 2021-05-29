# ODC Manual Indexer

The purpose of this repository is to provide convenient means of indexing data for an [Open Data Cube](https://www.opendatacube.org/) installation.
<br><br>

## Contents

* [Starting the Indexer](#starting)
    * [Starting with Docker](#starting_docker)
    * [Starting with Kubernetes](#starting_k8s)
* [Indexing Data](#indexing)
    * [Overview](#indexing_overview)
    * [Obtaining Information](#info)
    * [Product Types](#info_product_types)
    * [Products](#info_products)
    * [Data Stores](#info_data)
    * [Indexing](#info_idx)
    * [Indexing Scripts](#info_idx_scr)
    * [Drone Data Indexing](#drone_data_indexing)
<br><br>

## <a name="starting"></a> Starting the Indexer
-----

The indexer can be run in Docker or in Kubernetes. Instructions for both are included below.
<br><br>

>### <a name="starting_docker"></a> Starting with Docker 
-----

In `docker/.env`, set `DB_HOSTNAME` to the hostname of the database server, set `DB_DATABASE` to the name of the ODC database, set `DB_USER` to the name of the user for the ODC database, set `DB_PASSWORD` to the password for the user, set `DB_PORT` to the port that the ODC database is aviailable on (default for Postgres is `5432`), set `AWS_ACCESS_KEY_ID` to your AWS access key ID, and set `AWS_SECRET_ACCESS_KEY` to your AWS secret access key.

Finally, run `make up` from the top-level directory to start the indexer and then run `make ssh` to connect to the container through a bash shell.

**Developers**: Run the **dev-\*** Make commands to run a development environment (e.g. **dev-up**, **dev-ssh**). The development environment uses a non-peristent ODC database tied to the lifecycle of the docker-compose collection, so Make targets like **dev-down** or **dev-restart** clears this database.
<br><br>

>### <a name="starting_k8s"></a> Starting with Kubernetes
-----

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
<br><br>

## <a name="indexing"></a> Indexing Data
-----

>### <a name="indexing_overview"></a> Overview
-----

There are 4 types of things involved in indexing: product types, products, indexing scripts, and data stores.

* Product types can have many products. An example product type is `Landsat 8 Collection 2 Level 2 (SR)` (note that `SR` stands for "surface reflectance").

* Products are particular instances of product types. They may vary from other products with the same product type by (1) which data stores they can index, (2) their resolution, (3) their projection, (4) their measurements (e.g. which spectral bands they index), or otherwise.

* Indexing scripts are Python scripts that allow some remote data stores to be indexed for compatible products. Every product maps to 1 indexing script.

* Data stores are paths (local or remote) that contain data that products may be able to index. There can be many remote data stores that contain data compatible with a product - whether directly or through its indexing script.

How to obtain information about products, indexing scripts, and compatible data stores is explained in the [Obtaining Information](#info) section.

Product definitions and indexing scripts are in directories in the starting directory for the container - `/Datacube/manual_indexer`. These directories are named for the satellites or constellations (collections) of satellites - such as Landsat. You can run `wget` to retrieve desired, missing product definition YAML files from [here](https://github.com/opendatacube/datacube-core/tree/develop/docs/config_samples/dataset_types).
<br><br>

>### <a name="info"></a> Obtaining Information
-----

The main script for obtaining information is `utils/show/show.py`. 

By default for this and all following commands, only rows which have at least 1 product with a compatible data store indexable through an indexing script are shown. To show all rows for a given command, a `--show_all_rows` or `-a` flag can be specified in the command.

To view more information about how to use this script, such as the available commands and the columns in their output tables, run `python3 utils/show/show.py`.

To view more information about a particular command in this script, including the calling format and example usage, run `python3 utils/show/show.py <command> --help`.
<br><br>

>#### <a name="info_product_types"></a> Product Types
-----

To start, try listing the Datacube product types. Run this command from the starting directory: `python3 utils/show/show.py show-product-types`.

Other show commands accept product types as the primary argument for narrowing results.
<br><br>

>#### <a name="info_products"></a> Products
-----

To view a table showing each product's product type, name, description, resolution, projection, and path to the product definition file, run this command from the starting directory: `python3 utils/show/show.py show-products`.

To add a product with a product definition at `<path>`, run `datacube product add <path>`.

You also can limit the output of many commands, including this command, with a `-p` argument, specifying the products to show in a list (e.g. `-p "['ls8_usgs_sr_scene']"`).
<br><br>

>#### <a name="info_data"></a> Data Stores
-----

To view a table showing each datastore's path, description, compatible products, and the metadata file suffix, run this command from the starting directory: `python3 utils/show/show.py show-data-stores`.
<br><br>

>#### <a name="info_idx"></a> Indexing
-----

**To view a table showing the command calling format for each combination of product and compatible data store**, run this command from the starting directory: `python3 utils/show/show.py show-indexing`.

The `IdxCmdFmt` column shows the indexing command to use. You must prefix this with `python3`. For example, a `IdxCmdFmt` value of `index_scripts/idx_scr.py <arguments>` will be `python3 index_scripts/idx_scr.py <arguments>`. Some arguments like `<product-type>` will be known from the product definition.

If there is no indexing script for a given pairing of a product and a compatible data store (whether recorded in this repository or not), you should still be able to index that data store if it already has Datacube metadata YAML documents by using a command like `datacube dataset add <path-to-dataset-documents>`. For example, commonly you will have a directory containing directories of scenes - 1 directory per scene - with each containing a dataset document. If this dataset document is called `metadata.yaml`, then run this command to index the data: `datacube dataset add <datastore-path>/**/metadata.yaml` where `<datastore-path>` is the directory containing scene directories.

For rows with no path (the `DsPath` column having the value `N/A`), you can use the indexing command to index the path `<datastore-path>`, which is a directory containing scene directories.
<br><br>

>#### <a name="info_idx_scr"></a> Indexing Scripts
-----

To view a table showing the indexing scripts' paths, calling formats, compatible products, and supported datastore origin types, run this command from the starting directory: `python3 utils/show/show.py show-idx-scr`.

>#### <a name="drone_data_indexing"></a> Drone Data Indexing
-----


