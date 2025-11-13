import os
from typing import List, Optional, AsyncGenerator
from .base import FileSystemProvider, FileItem
import asyncio
import shutil
import aiofiles
from fastapi import UploadFile

class LocalProvider(FileSystemProvider):
    """
    로컬 파일 시스템을 위한 Provider.
    로컬 디렉터리와 파일에 접근하여 정보를 가져옵니다.
    """
    def __init__(self, root_dir: str = None, provider_id: Optional[str] = None):
        super().__init__(provider_id)
        self.root_dir = os.path.abspath(root_dir) if root_dir else os.getcwd()

    def _get_full_path(self, path: str) -> str:
        """요청된 상대 경로를 안전한 절대 경로로 변환합니다."""
        full_path = os.path.abspath(os.path.join(self.root_dir, path))
        if not full_path.startswith(self.root_dir):
            raise PermissionError("Access denied: Path is outside the root directory.")
        return full_path

    async def list_files(self, path: str) -> List[FileItem]:
        full_path = self._get_full_path(path)
        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            raise FileNotFoundError(f"Directory not found: {path}")

        items = []
        for item_name in os.listdir(full_path):
            item_path = os.path.join(full_path, item_name)
            items.append(self._create_file_item(item_path))
        return items

    async def get_metadata(self, path: str) -> Optional[FileItem]:
        try:
            full_path = self._get_full_path(path)
            if not os.path.exists(full_path):
                return None
            return self._create_file_item(full_path)
        except (FileNotFoundError, PermissionError):
            return None

    async def read_file_content(self, path: str) -> Optional[str]:
        try:
            full_path = self._get_full_path(path)
            if not os.path.isfile(full_path):
                return None
            
            # 비동기적으로 파일 읽기
            loop = asyncio.get_running_loop()
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = await loop.run_in_executor(None, f.read)
            return content
        except Exception:
            return None

    async def list_files_recursive(self, path: str) -> List[FileItem]:
        full_path = self._get_full_path(path)
        if not os.path.isdir(full_path):
            raise FileNotFoundError(f"Directory not found: {path}")

        items = []
        for root, dirs, files in os.walk(full_path):
            for name in files:
                item_path = os.path.join(root, name)
                items.append(self._create_file_item(item_path))
            for name in dirs:
                item_path = os.path.join(root, name)
                items.append(self._create_file_item(item_path))
        return items

    async def upload_file(self, destination_path: str, file_obj: UploadFile) -> bool:
        try:
            full_path = self._get_full_path(destination_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            async with aiofiles.open(full_path, 'wb') as out_file:
                while content := await file_obj.read(1024 * 1024):
                    await out_file.write(content)
            return True
        except Exception as e:
            print(f"Error uploading file to {destination_path}: {e}")
            return False

    async def download_file(self, path: str) -> AsyncGenerator[bytes, None]:
        full_path = self._get_full_path(path)
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"File not found: {path}")

        async with aiofiles.open(full_path, 'rb') as f:
            while chunk := await f.read(1024 * 1024):
                yield chunk

    async def delete_item(self, path: str) -> bool:
        try:
            full_path = self._get_full_path(path)
            if not os.path.exists(full_path):
                return False

            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)
            return True
        except Exception as e:
            print(f"Error deleting item {path}: {e}")
            return False

    def _create_file_item(self, item_path: str) -> FileItem:
        """Helper to create a FileItem from a path."""
        is_directory = os.path.isdir(item_path)
        return FileItem(
            name=os.path.basename(item_path),
            is_directory=is_directory,
            path=os.path.relpath(item_path, self.root_dir).replace('\\', '/'),
            size=os.path.getsize(item_path) if not is_directory else None,
            last_modified=os.path.getmtime(item_path)
        )
