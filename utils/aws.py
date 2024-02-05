from enum import Enum
import re

import boto3
from botocore.exceptions import ClientError


class Language(Enum):
    ENGLISH_US = 'en-US'
    ENGLISH_UK = 'en-GB'
    DUTCH = 'nl-NL'
    SPANISH = 'es-ES'
    HEBREW = 'he-IL'


class Region(Enum):
    US_EAST_1 = 'us-east-1'
    US_EAST_2 = 'us-east-2'
    US_WEST_1 = 'us-west-1'
    US_WEST_2 = 'us-west-2'
    SA_SAO_PAOLO = 'sa-east-1'
    EU_FRANKFURT = 'eu-central-1'
    EU_LONDON = 'eu-west-2'
    EU_IRELAND = 'eu-west-1'


class S3:
    origin = 'aws'
    default_folder = '/tmp'

    def __init__(self, region, bucket):
        self.region = region
        self.bucket = bucket
        self.s3_client = boto3.client('s3')

    def upload(self, filepath, key):
        if not self.bucket_exists():
            self.create_bucket()

        s3_resource = boto3.resource('s3', region_name=self.region.value)
        s3_bucket = s3_resource.Bucket(name=self.bucket)
        s3_bucket.upload_file(Filename=filepath, Key=key)

        return self.get_object_uri(key=key)

    def bucket_exists(self):
        """Check if a bucket exists."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
            return True
        except ClientError as e:
            return False

    def create_bucket(self):
        """Create an S3 bucket in a specified region."""
        try:
            location = {'LocationConstraint': self.region.value}
            self.s3_client.create_bucket(Bucket=self.bucket,
                                         CreateBucketConfiguration=location)
        except ClientError as e:
            print(f"Error creating bucket: {e}")
            raise e

    def delete(self, key):
        """Deletes an object specified by the key from the S3 bucket.

        Args:
            key (str): The key of the object to delete in the S3 bucket.

        Returns:
            dict: The response from the S3 service after attempting the delete operation.
        """
        s3_client = boto3.client('s3')
        response = s3_client.delete_object(Bucket=self.bucket, Key=key)
        return response['ResponseMetadata']['HTTPStatusCode'] == 204

    def exists(self, key):
        if not self.bucket_exists():
            return False

        files = self.list_files()

        try:
            next(upload for upload in files if key in upload)
        except StopIteration:
            return False

        return True

    def get_object_uri(self, key):
        object_location = boto3.client('s3').get_bucket_location(Bucket=self.bucket)['LocationConstraint']
        object_uri = 'https://{bucket}.s3-{location}.amazonaws.com/{key}'.format(
            location=object_location,
            bucket=self.bucket,
            key=key
        )

        return object_uri

    def metadata(self, uri):
        bucket, region, key = re.search(
            pattern=r'https://([^\.]+)\.s3-([^\.]+)\.amazonaws.com/(.+$)',
            string=uri
        ).groups()
        s3_client = boto3.client('s3')
        s3_object = s3_client.get_object(Bucket=bucket, Key=key)

        metadata = {
            'uri': uri,
            'bucket': bucket,
            'region': region,
            'key': key,
            'origin': self.origin,
            'content_length': s3_object['ContentLength'],
            'e_tag': s3_object['ETag'],
        }

        return metadata

    def list_files(self):
        resource_list = [obj.key for obj in self._list_objects()]
        return resource_list

    def _list_objects(self):
        resource = boto3.resource('s3', region_name=self.region.value)
        bucket = resource.Bucket(name=self.bucket)
        return bucket.objects.all()
