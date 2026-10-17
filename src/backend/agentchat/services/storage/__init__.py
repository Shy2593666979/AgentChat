from agentchat.settings import app_settings

if app_settings.storage.mode == "local":
    from agentchat.services.storage.local import LocalStorageClient
    storage_client = LocalStorageClient()
elif app_settings.storage.mode == "minio":
    from agentchat.services.storage.minio import MinioClient
    storage_client = MinioClient()
else:
    from agentchat.services.storage.oss import OSSClient
    storage_client = OSSClient()

if __name__ == "__main__":
    storage_client.list_files_in_folder("icons/user/")
