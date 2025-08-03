import oss2
from loguru import logger
from agentchat.settings import app_settings

class AliyunOSSClient:
    def __init__(self):
        auth = oss2.Auth(access_key_id=app_settings.aliyun_oss["access_key_id"],
                         access_key_secret=app_settings.aliyun_oss["access_key_secret"])
        self.bucket = oss2.Bucket(auth, app_settings.aliyun_oss["endpoint"], app_settings.aliyun_oss["bucket_name"])

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

    def sign_url_for_get(self, object_name, expiration=3600):
        try:
            url = self.bucket.sign_url("GET", object_name, expiration, slash_safe=True)
            return url
        except oss2.exceptions.OssError as e:
            logger.error(f"Failed to generate GET URL for {object_name}: {e}")

    def download_file(self, object_name, local_file):
        try:
            self.bucket.get_object_to_file(object_name, local_file)
            logger.info(f"File {object_name} downloaded successfully to {local_file}")
        except oss2.exceptions.OssError as e:
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
            # 确保文件夹路径以斜杠结尾
            if folder_path and not folder_path.endswith('/'):
                folder_path += '/'

            files_url = []
            for obj in oss2.ObjectIterator(self.bucket, prefix=folder_path, delimiter='/'):
                if not obj.is_prefix():  # 只处理文件，忽略文件夹
                    files_url.append(obj.key)
            return [file_url for file_url in files_url if not file_url.endswith('/')]
        except oss2.exceptions.OssError as e:
            logger.error(f"Failed to list files in folder {folder_path}: {e}")
            return []


aliyun_oss = AliyunOSSClient()


if __name__ == "__main__":
    aliyun_oss.list_files_in_folder("icons/user/")
