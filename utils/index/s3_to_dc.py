#!/usr/bin/env python3
"""
Build S3 iterators using odc-tools
and index datasets found into RDS
Modified from original here: https://github.com/opendatacube/odc-tools/blob/develop/apps/dc_tools/odc/apps/dc_tools/s3_to_dc.py
"""
import logging
import sys
from typing import Tuple

import click
from datacube import Datacube
from datacube.index.hl import Doc2Dataset
from odc.aio import S3Fetcher, s3_find_glob
from odc.apps.dc_tools.utils import (IndexingException, allow_unsafe,
                                     fail_on_missing_lineage,
                                     index_update_dataset, no_sign_request,
                                     request_payer, skip_check, skip_lineage,
                                     transform_stac, transform_stac_absolute,
                                     update, update_if_exists, verify_lineage)
from odc.index import parse_doc_stream
from odc.index.stac import stac_transform, stac_transform_absolute


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
    transform=None,
    update=False,
    update_if_exists=False,
    allow_unsafe=False,
    **kwargs,
) -> Tuple[int, int]:
    doc2ds = Doc2Dataset(dc.index, products=products, **kwargs)

    ds_added = 0
    ds_failed = 0
    uris_docs = parse_doc_stream(stream_docs(document_stream), on_error=doc_error, transform=transform)
    # print(f'uris_docs: {list(uris_docs)}')

    for s3_uri, metadata in uris_docs:
        try:
            # If this product 
            # if len({'black_marble_night_lights'}.intersection(products)) > 0:
                # if 'odc-dataset' not in s3_uri:
                    # continue
            print(f'metadata: {metadata}')
            print(f's3_uri: {s3_uri}')
            index_update_dataset(metadata, s3_uri, dc, doc2ds, update, update_if_exists, allow_unsafe)
            ds_added += 1
        except (IndexingException) as e:
            logging.exception(f"Failed to index dataset {s3_uri} with error {e}")
            ds_failed += 1

    return ds_added, ds_failed


@click.command("s3-to-dc")
@skip_lineage
@fail_on_missing_lineage
@verify_lineage
@transform_stac
@transform_stac_absolute
@update
@update_if_exists
@allow_unsafe
@skip_check
@no_sign_request
@request_payer
@click.argument("s3_uri", type=str, nargs=1)
@click.argument("s3_region", type=str, nargs=1)
@click.argument("product", type=str, nargs=1)
def cli(
    skip_lineage,
    fail_on_missing_lineage,
    verify_lineage,
    stac,
    absolute,
    update,
    update_if_exists,
    allow_unsafe,
    skip_check,
    no_sign_request,
    request_payer,
    s3_uri,
    s3_region,
    product,
):
    """ Iterate through files in an S3 bucket and add them to datacube"""

    transform = None
    if stac:
        if absolute:
            transform = stac_transform_absolute
        else:
            transform = stac_transform

    candidate_products = product.split()

    opts = {}
    if request_payer:
        opts["RequestPayer"] = "requester"

    # Check datacube connection and products
    dc = Datacube()
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
    import inspect
    print(f'signature: {inspect.signature(S3Fetcher)}')
    
    fetcher = S3Fetcher(region_name=s3_region, aws_unsigned=no_sign_request)
    document_stream = stream_urls(s3_find_glob(s3_uri, skip_check=skip_check, s3=fetcher, **opts))
    # print(f'document_stream: {document_stream}')

    added, failed = dump_to_odc(
        fetcher(document_stream),
        dc,
        candidate_products,
        skip_lineage=skip_lineage,
        fail_on_missing_lineage=fail_on_missing_lineage,
        verify_lineage=verify_lineage,
        transform=transform,
        update=update,
        update_if_exists=update_if_exists,
        allow_unsafe=allow_unsafe,
    )

    print(f"Added {added} Datasets, Failed {failed} Datasets")

    if failed > 0:
        sys.exit(failed)


if __name__ == "__main__":
    cli()