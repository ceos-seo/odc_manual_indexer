import logging

from datacube.utils import changes
from datacube.index.hl import Doc2Dataset

def add_dataset(doc, uri, index):
    doc_id = doc['id']

    resolver = Doc2Dataset(index)
    dataset, err  = resolver(doc, uri)
    existing_dataset = index.datasets.get(doc_id)

    if not existing_dataset:
        logging.info("Trying to index")
        if err is not None:
            logging.error("%s", err)
        else:
            try:
                index.datasets.add(dataset, with_lineage=False) # Source policy to be checked in sentinel 2 dataset types
            except Exception as e:
                logging.error("Unhandled exception %s", e)
    else:
        logging.info("Updating dataset instead.")
        try:
            index.datasets.update(dataset, {tuple(): changes.allow_any})
        except Exception as e:
            logging.error("Unhandled exception %s", e)

    return dataset, err