#!/usr/bin/env python3
"""
Build S3 iterators using odc-tools
and index datasets found into RDS
Modified from original here: https://github.com/opendatacube/odc-tools/blob/develop/apps/dc_tools/odc/apps/dc_tools/s3_to_dc.py
"""
import logging
from os import path
import sys
from typing import Tuple
import inspect

import pathlib
import click
from tqdm import tqdm

from datacube import Datacube
from datacube.index.hl import Doc2Dataset
from odc.aio import S3Fetcher, s3_find_glob
from odc.apps.dc_tools.utils import (IndexingException, allow_unsafe,
                                     fail_on_missing_lineage,
                                     index_update_dataset,
                                     request_payer, skip_lineage,
                                     update, update_if_exists, verify_lineage)
# from odc.apps.dc_tools.utils import (no_sign_request, skip_check, 
#                                      transform_stac, transform_stac_absolute)
from odc.index import parse_doc_stream
# from odc.index.stac import stac_transform, stac_transform_absolute

dc = Datacube()
index = dc.index

# Grab the URL from the resulting S3 item
def stream_urls(urls):
    for url in urls:
        yield url.url


# Parse documents as they stream through from S3
def stream_docs(documents):
    for document in documents:
        yield (document.url, document.data)


# Log the internal errors parsing docs
def doc_error(s3_uri, doc, e):
    logging.exception(f"Failed to parse doc {s3_uri} with error {e}")


def dump_to_odc(
    document_stream,
    dc: Datacube,
    products: list,
    update=False,
    update_if_exists=False,
    allow_unsafe=False,
    **kwargs,
) -> Tuple[int, int]:
    doc2ds = Doc2Dataset(dc.index, products=products, **kwargs)

    ds_added = 0
    ds_failed = 0
    
    uris_docs = list(parse_doc_stream(stream_docs(document_stream), on_error=doc_error, transform=None))

    for s3_uri, metadata in tqdm(uris_docs, desc='Indexing scenes on S3'):
        try:
            # If this product is one we generate metadata for, try to find the ODC metadata document.
            if len({'black_marble_night_lights'}.intersection(products)) > 0:
                if 'odc-dataset' not in s3_uri:
                    continue
            index_update_dataset(metadata, s3_uri, dc, doc2ds, update, update_if_exists, allow_unsafe)
            ds_added += 1
        except (IndexingException) as e:
            logging.exception(f"Failed to index dataset {s3_uri} with error {e}")
            ds_failed += 1

    return ds_added, ds_failed


def s3_to_dc(s3_uri, s3_region, product):
    """
    Add data for a datacube product in an S3 path to the datacube

    s3_uri: str
    
        The S3 path, excluding the scheme. For the bucket mybucket and prefix mydata, this should be mybucket/mydata, not s3://mybucket/mydata.
    
    s3_region: str

        The AWS region the bucket is in (e.g. us-west-2).
    
    product: str

        The name of the datacube product to index data for (e.g. black_marble_night_lights).

    """
    candidate_products = product.split()

    opts = {}
    if request_payer:
        opts["RequestPayer"] = "requester"

    # Check datacube connection and products
    odc_products = dc.list_products().name.values

    odc_products = set(odc_products)
    if not set(candidate_products).issubset(odc_products):
        missing_products = list(set(candidate_products) - odc_products)
        print(
            f"Error: Requested Product/s {', '.join(missing_products)} {'is' if len(missing_products) == 1 else 'are'} "
            "not present in the ODC Database",
            file=sys.stderr,
        )
        sys.exit(1)

    # Get a generator from supplied S3 Uri for candidate documents
    fetcher = S3Fetcher(region_name=s3_region, aws_unsigned=False)
    # If no extension is specified, look for JSON files.
    s3_uri_pathlib = pathlib.Path(s3_uri)
    s3_uri_no_extension = s3_uri_pathlib.suffix == ''
    s3_uri = str(s3_uri_pathlib)
    if s3_uri_no_extension:
        s3_uri = f'{s3_uri}/**/*.json'
    s3_uri = f's3://{s3_uri}'
    document_stream = stream_urls(s3_find_glob(s3_uri, skip_check=False, s3=fetcher, **opts))

    added, failed = dump_to_odc(
        fetcher(document_stream),
        dc,
        candidate_products,
        skip_lineage=skip_lineage,
        fail_on_missing_lineage=fail_on_missing_lineage,
        verify_lineage=verify_lineage,
        # update=update,
        update_if_exists=True,
        allow_unsafe=allow_unsafe,
    )

    print(f"Added {added} Datasets, Failed {failed} Datasets")

    if failed > 0:
        sys.exit(failed)
