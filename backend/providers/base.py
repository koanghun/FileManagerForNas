from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
from fastapi import UploadFile

# 프론트엔드의 FileItem 인터페이스와 일치하는 Pydantic 모델
# 모든 Provider는 이 형식에 맞춰 파일 정보를 반환해야 합니다.
class FileItem(BaseModel):
    name: str
    is_directory: bool
    path: str
    size: Optional[int] = None
    last_modified: float

# 모든 파일 시스템 Provider가 상속받아야 할 추상 기본 클래스(ABC)
class FileSystemProvider(ABC):
    """
    파일 시스템 Provider를 위한 추상 기본 클래스.
    모든 Provider는 이 클래스에 정의된 메서드들을 반드시 구현해야 합니다.
    """
    def __init__(self, provider_id: Optional[str] = None):
        self.provider_id = provider_id

    @abstractmethod
    async def list_files(self, path: str) -> List[FileItem]:
        """
        지정된 경로의 파일 및 디렉터리 목록을 비동기적으로 반환합니다.

        :param path: 조회할 경로
        :return: FileItem 모델의 리스트
        """
        pass

    @abstractmethod
    async def get_metadata(self, path: str) -> Optional[FileItem]:
        """
        지정된 파일 또는 디렉터리의 메타데이터를 반환합니다.
        """
        pass

    @abstractmethod
    async def read_file_content(self, path: str) -> Optional[str]:
        """
        지정된 텍스트 파일의 내용을 문자열로 반환합니다.
        """
        pass
    
    @abstractmethod
    async def list_files_recursive(self, path: str) -> List[FileItem]:
        """
        지정된 경로의 모든 하위 파일 및 디렉터리 목록을 재귀적으로 반환합니다.
        """
        pass

    @abstractmethod
    async def upload_file(self, destination_path: str, file_obj: UploadFile) -> bool:
        """
        지정된 경로로 파일을 업로드합니다.

        :param destination_path: 파일을 저장할 대상 경로 (파일 이름 포함).
        :param file_obj: 업로드할 파일 객체 (FastAPI UploadFile).
        :return: 업로드 성공 여부.
        """
        pass

    @abstractmethod
    async def download_file(self, path: str) -> AsyncGenerator[bytes, None]:
        """
        지정된 경로의 파일을 비동기적으로 다운로드합니다.
        파일 내용을 바이트 스트림으로 반환합니다.

        :param path: 다운로드할 파일의 경로.
        :return: 파일 내용을 비동기적으로 생성하는 바이트 제너레이터.
        """
        pass

    @abstractmethod
    async def delete_item(self, path: str) -> bool:
        """
        지정된 경로의 파일 또는 디렉터리를 삭제합니다.

        :param path: 삭제할 파일 또는 디렉터리의 경로.
        :return: 삭제 성공 여부.
        """
        pass
