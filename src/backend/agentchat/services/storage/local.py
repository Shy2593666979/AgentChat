import shutil
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

from agentchat.settings import app_settings


class LocalStorageClient:
    """使用本地目录实现现有对象存储接口。"""

    def __init__(self, config=None):
        config = config or app_settings.storage.local
        root = Path(config.path).expanduser()
        self.root = (root if root.is_absolute() else Path(__file__).resolve().parents[3] / root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.base_url = config.base_url.rstrip("/") + "/"

    def _path(self, object_name):
        name = str(object_name)
        if "://" in name:
            name = urlparse(name).path
        prefix = urlparse(self.base_url).path.strip("/") + "/"
        name = unquote(name).replace("\\", "/").lstrip("/")
        if name.startswith(prefix):
            name = name[len(prefix):]
        path = (self.root / name).resolve()
        if path == self.root or not path.is_relative_to(self.root):
            raise ValueError("文件路径必须位于本地上传目录内")
        return path

    def upload_file(self, object_name, data):
        path = self._path(object_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data.encode("utf-8") if isinstance(data, str) else bytes(data))

    def upload_local_file(self, object_name, local_file):
        path = self._path(object_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(local_file, path)

    def download_file(self, object_name, local_file):
        path = Path(local_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self._path(object_name), path)

    def sign_url_for_get(self, object_name, expiration=3600):
        path = self._path(object_name)
        return self.base_url + quote(path.relative_to(self.root).as_posix(), safe="/")

    def list_files_in_folder(self, folder_path):
        folder = self._path(folder_path)
        if not folder.is_dir():
            return []
        return [p.relative_to(self.root).as_posix() for p in sorted(folder.iterdir())
                if p.is_file() and p.resolve().is_relative_to(self.root)]
