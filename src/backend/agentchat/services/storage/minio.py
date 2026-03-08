import io
from minio import Minio
from minio.error import S3Error
from loguru import logger
from agentchat.settings import app_settings

class MinioClient:
    def __init__(self):
        self.client = Minio(
            secure=False,
            endpoint=app_settings.storage.minio.endpoint,
            access_key=app_settings.storage.minio.access_key_id,
            secret_key=app_settings.storage.minio.access_key_secret,
        )
        self.bucket_name = app_settings.storage.minio.bucket_name
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
            logger.success(f"Minio Bucket: {self.bucket_name} created success")


    def upload_file(self, object_name, data):
        try:
            if isinstance(data, (bytes, bytearray)):
                data_stream = io.BytesIO(data)
                length = len(data)
            else:
                data = data.encode("utf-8") if isinstance(data, str) else data
                data_stream = io.BytesIO(data)
                length = len(data)
            self.client.put_object(self.bucket_name, object_name, data_stream, length)
            logger.info(f"File uploaded successfully: {object_name}")
        except S3Error as e:
            logger.error(f"Failed to upload file: {e}")

    def upload_local_file(self, object_name, local_file):
        try:
            self.client.fput_object(self.bucket_name, object_name, local_file)
            logger.info(f"Local file uploaded successfully: {object_name}")
        except S3Error as e:
            logger.error(f"Failed to upload file : {e}")

    def delete_bucket(self):
        try:
            self.client.remove_bucket(self.bucket_name)
            logger.info("Bucket deleted successfully")
        except S3Error as e:
            logger.error(f"Failed to delete bucket: {e}")

    def sign_url_for_get(self, object_name, expiration=3600):
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                self.bucket_name, object_name, expires=timedelta(seconds=expiration)
            )
            return url
        except S3Error as e:
            logger.error(f"Failed to generate GET URL for {object_name}: {e}")

    def download_file(self, object_name, local_file):
        try:
            self.client.fget_object(self.bucket_name, object_name, local_file)
            logger.info(f"File {object_name} downloaded successfully to {local_file}")
        except S3Error as e:
            logger.error(f"Failed to download {object_name} to {local_file}: {e}")

    def list_files_in_folder(self, folder_path):
        """
        列出指定文件夹下的所有文件（不递归，假设文件夹下没有子目录）

        Args:
            folder_path (str): 文件夹路径，需以斜杠 / 结尾

        Returns:
            list: 文件信息列表，每个元素是包含文件名、大小、修改时间等信息的字典
        """
        try:
            if folder_path and not folder_path.endswith('/'):
                folder_path += '/'

            objects = self.client.list_objects(
                self.bucket_name, prefix=folder_path, recursive=False
            )
            files_url = [
                obj.object_name for obj in objects
                if not obj.is_dir and not obj.object_name.endswith('/')
            ]
            return files_url
        except S3Error as e:
            logger.error(f"Failed to list files in folder {folder_path}: {e}")
            return []


