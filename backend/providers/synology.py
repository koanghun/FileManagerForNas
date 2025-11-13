import httpx
import os
from typing import List, Optional, AsyncGenerator
from .base import FileSystemProvider, FileItem
import asyncio
from fastapi import UploadFile
import chardet

# Synology API의 응답 형식에 맞춘 Pydantic 모델 (필요에 따라 추가)

class SynologyAPIProvider(FileSystemProvider):
    """
    Synology File Station API를 위한 Provider.
    """
    def __init__(self, host: str, port: str, username: str, password: str, secure: bool = True, provider_id: Optional[str] = None):
        super().__init__(provider_id)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.secure = secure

        self.base_url = f"https://{self.host}:{self.port}/webapi" if self.secure else f"http://{self.host}:{self.port}/webapi"
        self._sid = None # 세션 ID
        self._syno_token = None # CSRF 방지를 위한 Syno Token
        self.client = httpx.AsyncClient(verify=self.secure) # 비동기 HTTP 클라이언트

    async def _login(self, otp_code: Optional[str] = None):
        """
        Synology NAS에 로그인하여 세션 ID (_sid)를 얻습니다.
        2FA를 위해 otp_code를 선택적으로 받습니다.
        """
        api_path = "entry.cgi"
        params = {
            "api": "SYNO.API.Auth",
            "version": "7", # 최신 버전에 따라 조절
            "method": "login",
            "account": self.username,
            "passwd": self.password,
            "session": "FileStation",
            "format": "sid"
        }
        # 2FA 코드가 제공된 경우, 파라미터에 추가
        if otp_code:
            params["otp_code"] = otp_code

        try:
            # POST 요청 시에는 파라미터를 'data'로 전달하여 form-encoded body로 보냅니다.
            response = await self.client.post(f"{self.base_url}/{api_path}", data=params)
            response.raise_for_status() # HTTP 오류 발생 시 예외 발생
            data = response.json()

            if data.get("success"):
                self._sid = data["data"]["sid"]
                self._syno_token = data["data"].get("synotoken") # synotoken 가져오기
                print(f"Synology NAS 로그인 성공. SID: {self._sid}")
                
                # CSRF 토큰이 있는 경우, 클라이언트의 기본 헤더로 설정
                if self._syno_token:
                    self.client.headers["X-SYNO-Token"] = self._syno_token
                    print(f"Syno-Token 설정 완료.")
            else:
                # API 레벨에서 로그인 실패 처리
                error_code = data.get("error", {}).get("code")
                raise ConnectionRefusedError(f"Synology 로그인 실패. 오류 코드: {error_code}")
        except httpx.RequestError as e:
            raise ConnectionError(f"Synology NAS에 연결할 수 없습니다: {e}")

    async def _api_request(self, api_name: str, method: str, params: dict, version: str = "2", request_method: str = "GET") -> dict:
        """인증된 API 요청을 보내기 위한 헬퍼 함수"""
        if not self._sid:
            raise PermissionError("Not logged in.")

        api_path = "entry.cgi"
        base_params = {
            "api": api_name,
            "version": version,
            "method": method,
            "_sid": self._sid,
        }
        full_params = {**base_params, **params}
        
        try:
            if request_method.upper() == "POST":
                response = await self.client.post(f"{self.base_url}/{api_path}", data=full_params)
            else:
                response = await self.client.get(f"{self.base_url}/{api_path}", params=full_params)
            
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                error_code = data.get("error", {}).get("code")
                raise PermissionError(f"API 요청 실패 ({api_name}.{method}). 코드: {error_code}")
            return data
        except httpx.RequestError as e:
            raise ConnectionError(f"Synology NAS API 요청 실패: {e}")

    def _parse_file_data(self, file_data: dict) -> FileItem:
        """API 응답 데이터를 FileItem 모델로 변환하는 헬퍼 함수"""
        is_dir = file_data["isdir"]
        additional = file_data.get("additional", {})
        time_info = additional.get("time", {})
        
        return FileItem(
            name=file_data["name"],
            is_directory=is_dir,
            path=file_data["path"],
            size=additional.get("size") if not is_dir else None,
            last_modified=time_info.get("mtime", 0)
        )

    async def list_shares(self) -> List[FileItem]:
        """
        Synology NAS의 모든 공유 폴더 목록을 조회합니다.
        """
        data = await self._api_request("SYNO.FileStation.List", "list_share", {})
        items = []
        for share_data in data["data"]["shares"]:
            # list_share는 additional 정보가 없으므로 수동으로 생성
            item = FileItem(
                name=share_data["name"],
                is_directory=True,
                path=share_data["path"],
                size=None,
                last_modified=0 # 공유 폴더는 수정 시간이 없음
            )
            items.append(item)
        return items

    async def list_files(self, path: str) -> List[FileItem]:
        """
        지정된 경로의 파일 및 디렉터리 목록을 반환합니다.
        """
        params = {
            "folder_path": path,
            "additional": '["real_path","size","owner","time"]'
        }
        data = await self._api_request("SYNO.FileStation.List", "list", params)
        
        items = []
        for file_data in data["data"]["files"]:
            items.append(self._parse_file_data(file_data))
        return items

    async def get_metadata(self, path: str) -> Optional[FileItem]:
        """지정된 파일 또는 디렉터리의 메타데이터를 반환합니다."""
        params = {
            "path": path,
            "additional": '["real_path","size","owner","time"]'
        }
        try:
            data = await self._api_request("SYNO.FileStation.List", "getinfo", params)
            if data["data"]["files"]:
                return self._parse_file_data(data["data"]["files"][0])
            return None
        except (PermissionError, ConnectionError):
            # 파일이 없거나 권한이 없는 경우 None 반환
            return None

    async def read_file_content(self, path: str) -> Optional[str]:
        """지정된 텍스트 파일의 내용을 문자열로 반환합니다."""
        api_path = "entry.cgi"
        params = {
            "api": "SYNO.FileStation.Download", "version": "2", "method": "download",
            "_sid": self._sid, "path": path, "mode": "open"
        }
        try:
            # stream으로 요청하여 대용량 파일에 대비
            async with self.client.stream("GET", f"{self.base_url}/{api_path}", params=params, timeout=30.0) as response:
                response.raise_for_status()
                content_bytes = await response.aread()
                
                # chardet을 사용하여 인코딩 감지
                detection = chardet.detect(content_bytes)
                detected_encoding = detection['encoding'] if detection['confidence'] > 0.7 else None # 70% 이상 신뢰도일 때만 사용

                # 디코딩 시도 목록
                encodings_to_try = []
                if detected_encoding:
                    encodings_to_try.append(detected_encoding)
                encodings_to_try.extend(['utf-8', 'euc-kr', 'shift_jis']) # 기본 인코딩 추가

                for encoding in encodings_to_try:
                    try:
                        # errors='replace'를 사용하여 깨진 문자를 대체
                        return content_bytes.decode(encoding, errors='replace')
                    except UnicodeDecodeError:
                        continue
                
                # 모든 인코딩 실패 시 None 반환
                print(f"Could not decode file content for {path} with any of the attempted encodings.")
                return None
        except Exception as e:
            print(f"Error reading file content for {path}: {e}")
            return None

    async def list_files_recursive(self, path: str) -> List[FileItem]:
        """지정된 경로의 모든 하위 파일 및 디렉터리 목록을 재귀적으로 반환합니다."""
        all_items: List[FileItem] = []
        queue: List[str] = [path]
        
        while queue:
            current_path = queue.pop(0)
            try:
                # 현재 경로의 메타데이터를 가져와서 FileItem으로 추가
                meta = await self.get_metadata(current_path)
                if meta and meta.path != path: # 최상위 경로는 중복 추가 방지
                    all_items.append(meta)

                # 현재 경로가 디렉토리일 경우, 하위 목록 조회
                if meta and meta.is_directory:
                    items = await self.list_files(current_path)
                    for item in items:
                        if item.is_directory:
                            queue.append(item.path) # 하위 디렉토리는 큐에 추가
                        else:
                            all_items.append(item) # 파일은 바로 목록에 추가
            except PermissionError as e:
                print(f"권한 오류: {current_path} 폴더를 읽을 수 없습니다. 건너뜁니다. ({e})")
            except Exception as e:
                print(f"오류 발생: {current_path} 폴더 처리 중 오류. 건너뜁니다. ({e})")
        
        return all_items

    async def upload_file(self, destination_path: str, file_obj: UploadFile) -> bool:
        """
        Synology NAS에 파일을 업로드합니다.
        """
        api_path = "entry.cgi"
        # Synology API는 destination_path를 폴더 경로로 기대합니다.
        # 파일 이름은 multipart/form-data의 'file' 부분에서 가져옵니다.
        folder_path = os.path.dirname(destination_path)
        file_name = os.path.basename(destination_path)

        # 파일 내용을 비동기적으로 읽어 httpx.AsyncClient의 'files' 파라미터에 전달
        # httpx는 'files' 파라미터에 (filename, file_like_object, content_type) 튜플을 기대합니다.
        files = {
            "file": (file_name, file_obj.file, file_obj.content_type)
        }

        # API 파라미터
        data = {
            "api": "SYNO.FileStation.Upload",
            "version": "2",
            "method": "upload",
            "_sid": self._sid,
            "path": folder_path,
            "overwrite": "true", # 기존 파일이 있으면 덮어쓰기
            "create_parents": "true" # 상위 폴더가 없으면 생성
        }

        try:
            # httpx는 'data'와 'files'를 함께 사용하여 multipart/form-data 요청을 자동으로 구성합니다.
            response = await self.client.post(f"{self.base_url}/{api_path}", data=data, files=files, timeout=60.0)
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                print(f"File '{file_name}' uploaded successfully to '{folder_path}'.")
                return True
            else:
                error_code = result.get("error", {}).get("code")
                print(f"Synology upload failed for '{file_name}'. Error code: {error_code}")
                return False
        except httpx.RequestError as e:
            print(f"Synology upload request failed for '{file_name}': {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during Synology upload for '{file_name}': {e}")
            return False

    async def download_file(self, path: str) -> AsyncGenerator[bytes, None]:
        """
        Synology NAS에서 파일을 비동기적으로 다운로드합니다.
        파일 내용을 바이트 스트림으로 반환합니다.
        """
        api_path = "entry.cgi"
        params = {
            "api": "SYNO.FileStation.Download", "version": "2", "method": "download",
            "_sid": self._sid, "path": path, "mode": "download" # mode를 'download'로 설정
        }
        try:
            async with self.client.stream("GET", f"{self.base_url}/{api_path}", params=params, timeout=30.0) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield chunk
        except Exception as e:
            print(f"Error downloading file from Synology NAS {path}: {e}")
            raise # Re-raise the exception to be handled by the caller

    async def delete_item(self, path: str) -> bool:
        """
        Synology NAS에서 파일 또는 폴더를 삭제합니다.
        """
        try:
            # Synology API는 여러 경로를 배열로 받을 수 있지만, 여기서는 단일 경로만 처리합니다.
            params = {
                "path": f'["{path}"]', # JSON 배열 형식으로 전달
                "force_delete": "true" # 휴지통을 거치지 않고 강제 삭제
            }
            data = await self._api_request("SYNO.FileStation.Delete", "delete", params, request_method="POST")
            
            if data.get("success"):
                # Synology API의 delete 응답은 성공 시 data 필드가 비어있거나
                # task_id를 포함할 수 있습니다. 여기서는 단순히 success 여부만 확인합니다.
                print(f"Item '{path}' deleted successfully from Synology NAS.")
                return True
            else:
                error_code = data.get("error", {}).get("code")
                print(f"Synology delete failed for '{path}'. Error code: {error_code}")
                return False
        except Exception as e:
            print(f"Error deleting item from Synology NAS {path}: {e}")
            return False

    async def close(self):
        """
        HTTP 클라이언트 세션을 닫습니다.
        """
        await self.client.aclose()
