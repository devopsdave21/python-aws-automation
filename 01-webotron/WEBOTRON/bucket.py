# -*- coding: utf-8 -*-

"""Classes for S3 Buckets."""

import mimetypes
from pathlib import Path
from botocore.exceptions import ClientError
import boto3

class BucketManager:
    """Manage an S3 bucket."""

    def __init__(self, session):
        """Create a BucketManager object."""
        self.session = session
        self.s3 = self.session.resource('s3')
        
    
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

    @staticmethod
    def upload_file(bucket, path, key):
        """Upload file to S3 bucket."""
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'
        return bucket.upload_file(
            path,
            key,
            ExtraArgs={
                'ContentType': content_type
            }
        )

    def sync(self, pathname, bucket):
        """Sync files to S3."""
        bucket = self.s3.Bucket(bucket)
        root = Path(pathname).expanduser().resolve()

        def handle_directory(target):
            for p in target.iterdir():
                if p.is_dir(): 
                    handle_directory(p)
                if p.is_file(): 
                    self.upload_file(bucket, str(p), str(p.relative_to(root)))

        handle_directory(root)





        