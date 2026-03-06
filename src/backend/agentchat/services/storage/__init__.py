from agentchat.services.storage.oss import AliyunOSSClient
from agentchat.services.storage.minio import MinioClient
from agentchat.settings import app_settings

if app_settings.storage.mode == "minio":
    storage_client = MinioClient()
else:
    storage_client = AliyunOSSClient()

if __name__ == "__main__":
    storage_client.list_files_in_folder("icons/user/")