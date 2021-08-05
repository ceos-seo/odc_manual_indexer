import os
import re

import boto3
import joblib
from joblib import Parallel, delayed
from tqdm import tqdm

def s3_upload(directory, s3_uri):
    '''
    Upload data from `directory` to the S3 path `s3_uri`.
    The structure remains the same.

    Parameters
    ----------
    directory: str
        The directory to upload data from.
    s3_uri: str
        The S3 path to upload the data to.
    '''
    match = re.search('s3://(.*?)/(.*)', s3_uri)
    bucket = match.group(1)
    s3_base_prefix = match.group(2)

    def upload_scene(root, files):
        scene_base_dir = root.split('/')[-1]
        s3_prefix = os.path.join(s3_base_prefix, scene_base_dir)

        s3_client = boto3.client('s3')
        for file in files:
            s3_client.upload_file(os.path.join(root, file),
                                bucket, os.path.join(s3_prefix, file))

    Parallel(n_jobs=joblib.cpu_count()*10, backend='loky')(delayed(upload_scene)(root, files)
                        for root,dirs,files in tqdm(list(os.walk(directory)), desc='Uploading scenes to S3'))
