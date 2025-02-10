import oss2
from loguru import logger
from config.service_config import OSS_ENDPOINT, OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET_NAME


class OSSClient:
    def __init__(self):
        auth = oss2.Auth(access_key_id=OSS_ACCESS_KEY_ID, access_key_secret=OSS_ACCESS_KEY_SECRET)
        self.bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)

    def upload_file(self, object_name, data):
        try:
            result = self.bucket.put_object(object_name, data)
            logger.info(f"File uploaded successfully, status code: {result.status}")
        except oss2.exceptions.OssError as e:
            logger.error(f"Failed to upload file: {e}")

    def upload_local_file(self, object_name, local_file):
        try:
            result = self.bucket.put_object_from_file(object_name, local_file)
            logger.info(f"Local file uploaded successfully, status code: {result.status}")
        except oss2.exceptions.OssError as e:
            logger.error(f"Failed to upload file : {e}")

    def delete_bucket(self):
        try:
            self.bucket.delete_bucket()
            logger.info("Bucket deleted successfully")
        except oss2.exceptions.OssError as e:
            logger.error(f"Failed to delete bucket: {e}")


    def download_file(self, object_name, local_file):
        try:
            self.bucket.get_object_to_file(object_name, local_file)
            logger.info(f"File {object_name} downloaded successfully to {local_file}")
        except oss2.exceptions.OssError as e:
            logger.error(f"Failed to download {object_name} to {local_file}: {e}")

oss_client = OSSClient()