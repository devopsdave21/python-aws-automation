# -*- coding: utf-8 -*-

"""Classes for S3 Buckets."""

import mimetypes
from pathlib import Path
from botocore.exceptions import ClientError
import boto3
from functools import reduce


from hashlib import md5
import util

class BucketManager:
    """Manage an S3 bucket."""

    CHUNK_SIZE = 8388608

    def __init__(self, session):
        """Create a BucketManager object."""
        self.session = session
        self.s3 = self.session.resource('s3')
        self.transfer_config = boto3.s3.transfer.TransferConfig(
            multipart_chunksize=self.CHUNK_SIZE,
            multipart_chunksize=self.CHUNK_SIZE
        )

        self.manifest = {}


    def get_region_name(self):
        """Get the buckets region name."""
        bucket_location = self.s3.meta.client.get_bucket_location(Bucket=bucket)
        return bucket_location["LocationConstraint"] or 'us-east-1'

    
    def get_bucket_url(self, bucket):
        """Get the website URL for this bucket."""
        return "http://{}.{}".format(bucket.name, util.get_endpoint(self.get_region_name(bucket)).host)


    def all_buckets(self):
        """Get an iterator for all buckets."""
        return self.s3.buckets.all()

    def all_objects(self, bucket_name):
        """Get an iterator for all objects in a bucket."""
        return self.s3.Bucket(bucket_name).objects.all()

    def init_bucket(self, bucket_name):
        """Create new bucket, or return an already existing bucket."""
        s3_bucket = None
        try:
            s3_bucket = self.s3.create_bucket(Bucket=bucket_name,
                                        CreateBucketConfiguration={'LocationConstraint': self.session.region_name}
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                s3_bucket = self.s3.Bucket(bucket_name)
            else:
                raise e

        return s3_bucket

    def set_policy(self, bucket):
        """Set bucket policy to be readable by everyone."""
        policy = """
        {
            "Version":"2012-10-17",
            "Statement":[{
            "Sid":"PublicReadGetObject",
            "Effect":"Allow",
	        "Principal": "*",
                "Action":"s3:*",
                "Resource":["arn:aws:s3:::%s/*"
                ]
            }
        ]
        }
        """ % bucket.name
        policy = policy.strip()

        pol = bucket.Policy()
        pol.put(Policy=policy)

    def configure_website(self, bucket):
        """Configure permissions on S3."""
        bucket.Website().put(WebsiteConfiguration={
            'ErrorDocument': {
                'Key': 'error.html'
            },
            'IndexDocument': {
                'Suffix': 'index.html'
            }
        })


    def load_manifest(self, bucket):
        """Load manifest."""
        paginator = self.s3.meta.client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket.name):
            for obj in page.get('Contents', []):
                self.manifest[obj['Key']] = obj['ETag']

    @staticmethod
    def has_data(data):
        """Generate md5 hash for data."""
        hash = md5()
        hash.update(data)

        return hash


def gen_etag(self, path):
    """Generate etag for file."""
    hashes = []

    with open(path, 'rb') as f:
        while True:
            data = f.read(self.CHUNK_SIZE)

            if not data:
                break
        
        hashes.append(self.hash_data(data)

    if not hashes:
        return
    elif len(hashes) = 1:
        return '"{}"'.format(hash.hexdigest())
    else:
        hash = self.hash_data(reduce(lambda x, y: x + y, (h.digest() for h in hashes)))
        return '"{}-{}"'.format(hash.hexdigest(), len(hashes))
    

    @staticmethod
    def upload_file(bucket, path, key):
        """Upload file to S3 bucket."""
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'
        etag = self.gen_etag(path)
        if self.manifest.get(key, '') == etag:
            return
        return bucket.upload_file(
            path,
            key,
            ExtraArgs={
                'ContentType': content_type
            },
            Config=self.transfer_config
        )

    def sync(self, pathname, bucket):
        """Sync files to S3."""
        bucket = self.s3.Bucket(bucket)
        self.load_manifest(bucket)
        root = Path(pathname).expanduser().resolve()

        def handle_directory(target):
            for p in target.iterdir():
                if p.is_dir(): 
                    handle_directory(p)
                if p.is_file(): 
                    self.upload_file(bucket, str(p), str(p.relative_to(root)))

        handle_directory(root)





        