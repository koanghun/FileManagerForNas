import os
import uuid
import hashlib
import datetime
from fastapi import FastAPI, HTTPException, Depends, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
from pathlib import Path

# Provider 관련 모듈 import
from .providers.base import FileSystemProvider, FileItem
from .providers.local import LocalProvider
from .providers.synology import SynologyAPIProvider
from .search_service import SearchService
from .index_manager import index_manager, IndexManager

# --- Pydantic 모델 정의 ---
class LoginRequest(BaseModel):
    host: str
    port: int = 5001
    username: str
    password: str
    secure: bool = True
    otp_code: Optional[str] = None

class IndexFolderRequest(BaseModel):
    folder_path: str

class FolderStatusRequest(BaseModel):
    folder_paths: List[str]

# --- FastAPI 앱 설정 ---
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    app.state.sessions: Dict[str, FileSystemProvider] = {}
    app.state.default_provider = LocalProvider(provider_id="local")
    try:
        app.state.search_service = SearchService()
        print("SearchService initialized successfully.")
    except Exception as e:
        print(f"ERROR: Failed to initialize SearchService: {e}")
        # Re-raise the exception to ensure the application truly fails to start
        raise
    app.state.index_manager = index_manager

@app.on_event("shutdown")
async def shutdown_event():
    for provider in app.state.sessions.values():
        if hasattr(provider, 'close'):
            await provider.close()
    if app.state.search_service and app.state.search_service.client:
        app.state.search_service.client.persist()
    if app.state.index_manager:
        app.state.index_manager.close()

# CORS 미들웨어 추가
origins = ["http://localhost", "http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 의존성 주입 및 헬퍼 ---
async def get_provider_and_id(
    req: Request,
    authorization: Optional[str] = Header(None)
) -> tuple[FileSystemProvider, Optional[str]]:
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        provider = req.app.state.sessions.get(token)
        if provider:
            return provider, provider.provider_id
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    return req.app.state.default_provider, req.app.state.default_provider.provider_id

# --- 텍스트 분할 (Chunking) 헬퍼 ---
def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50):
    """텍스트를 중첩되는 청크로 분할합니다."""
    if not text:
        return []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
    return chunks

# --- 백그라운드 인덱싱 작업 ---
async def do_index_folder(provider: FileSystemProvider, provider_id: str, folder_path: str, search_service: SearchService, index_manager: IndexManager):
    """지정된 폴더를 재귀적으로 탐색하며 파일을 인덱싱하는 백그라운드 작업"""
    if not provider_id:
        print("Error: provider_id is missing, cannot start indexing.")
        return
        
    index_manager.set_folder_status(provider_id, folder_path, "indexing")
    total_chunks_indexed = 0
    
    try:
        # Provider를 통해 재귀적으로 파일 목록 가져오기
        all_items = await provider.list_files_recursive(folder_path)
        
        # 텍스트 기반 파일 필터링
        text_extensions = ['.txt', '.md', '.py', '.js', '.ts', '.json', '.csv']
        files_to_index = [
            item for item in all_items 
            if not item.is_directory and Path(item.name).suffix in text_extensions
        ]

        # 각 파일을 순회하며 청킹 및 인덱싱
        for file_item in files_to_index:
            try:
                content = await provider.read_file_content(file_item.path)
                if not content:
                    continue

                # 텍스트를 청크로 분할
                chunks = chunk_text(content)
                if not chunks:
                    continue

                # ChromaDB에 저장할 데이터 준비
                documents = []
                metadatas = []
                ids = []
                for i, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadatas.append({"file_path": file_item.path, "chunk_number": i + 1})
                    ids.append(f"{file_item.path}-chunk-{i+1}")
                
                # SearchService를 통해 청크들을 일괄 인덱싱
                await search_service.index_chunks(documents=documents, metadatas=metadatas, ids=ids)
                total_chunks_indexed += len(chunks)

            except Exception as e:
                print(f"Error reading or indexing file {file_item.path}: {e}")

        index_manager.set_folder_status(provider_id, folder_path, "indexed", file_count=total_chunks_indexed)
        print(f"Successfully indexed {total_chunks_indexed} chunks from {len(files_to_index)} files in '{folder_path}'.")

    except Exception as e:
        print(f"Failed to index folder '{folder_path}': {e}")
        index_manager.set_folder_status(provider_id, folder_path, "failed")


# --- API 엔드포인트 ---
@app.get("/")
def read_root():
    return {"message": "Welcome to AI File Management Backend!"}

@app.post("/api/login")
async def login(login_data: LoginRequest, request: Request):
    try:
        # 호스트와 사용자 이름을 기반으로 안정적인 provider_id 생성
        stable_id_source = f"{login_data.host}:{login_data.username}"
        provider_id = hashlib.sha256(stable_id_source.encode()).hexdigest()

        provider = SynologyAPIProvider(
            host=login_data.host, port=str(login_data.port),
            username=login_data.username, password=login_data.password,
            secure=login_data.secure,
            provider_id=provider_id # 생성된 ID를 provider에 전달
        )
        await provider._login(otp_code=login_data.otp_code)
        
        session_token = str(uuid.uuid4())
        request.app.state.sessions[session_token] = provider
        
        return {"token": session_token, "message": "Login successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/api/files")
async def list_files(path: str = ".", provider_info: tuple = Depends(get_provider_and_id)):
    provider, _ = provider_info
    try:
        if isinstance(provider, SynologyAPIProvider) and path in ('/', '.'):
            items = await provider.list_shares()
        else:
            items = await provider.list_files(path)
        return {"path": path, "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@app.get("/api/search")
async def search_files(query: str, req: Request, n_results: int = 5):
    if not query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    results = await req.app.state.search_service.search(query, n_results)
    return {"query": query, "results": results}

@app.post("/api/index/folder")
async def index_folder(
    req: IndexFolderRequest,
    background_tasks: BackgroundTasks,
    provider_info: tuple = Depends(get_provider_and_id),
    search_service: SearchService = Depends(lambda: app.state.search_service),
    index_manager: IndexManager = Depends(lambda: app.state.index_manager)
):
    provider, provider_id = provider_info
    if not provider_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    background_tasks.add_task(do_index_folder, provider, provider_id, req.folder_path, search_service, index_manager)
    
    return {"message": f"Indexing started for '{req.folder_path}' in the background."}

@app.post("/api/index/status")
async def get_folder_statuses(req: FolderStatusRequest, provider_info: tuple = Depends(get_provider_and_id)):
    provider, provider_id = provider_info
    if not provider_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    db_statuses = app.state.index_manager.get_multiple_folder_statuses(provider_id, req.folder_paths)
    final_statuses = {}

    for path in req.folder_paths:
        db_status = db_statuses.get(path)
        if not db_status:
            final_statuses[path] = "not_indexed"
        elif db_status['status'] != 'indexed':
            final_statuses[path] = db_status['status']
        else:
            try:
                # 폴더의 마지막 수정 시간 확인 (Provider에 기능 필요)
                folder_meta = await provider.get_metadata(path)
                if folder_meta:
                    last_modified = datetime.datetime.fromtimestamp(folder_meta.last_modified)
                    last_indexed = datetime.datetime.fromisoformat(db_status['last_indexed_at'])
                    
                    if last_modified > last_indexed:
                        final_statuses[path] = "outdated"
                    else:
                        final_statuses[path] = "indexed"
                else:
                    final_statuses[path] = "not_indexed" # 폴더가 사라진 경우
            except Exception:
                final_statuses[path] = "indexed" # 메타데이터 확인 실패 시 일단 indexed로 처리

    return final_statuses

@app.delete("/api/index/folder")
async def delete_folder_index(req: IndexFolderRequest, provider_info: tuple = Depends(get_provider_and_id)):
    _, provider_id = provider_info
    if not provider_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # 1. DB에서 폴더 정보 삭제
    app.state.index_manager.remove_folder(provider_id, req.folder_path)

    # 2. ChromaDB에서 관련 파일들 삭제
    deleted_count = await app.state.search_service.delete_files_in_folder(req.folder_path)

    return {"message": f"Index for '{req.folder_path}' and {deleted_count} related files have been deleted."}

@app.get("/api/debug/indexed-files")
async def get_all_indexed_files(req: Request):
    """디버깅용: ChromaDB에 인덱싱된 모든 파일 목록을 반환합니다."""
    search_service: SearchService = req.app.state.search_service
    return {"indexed_files": search_service.get_indexed_files()}

@app.post("/api/debug/reset-db")
async def reset_vector_db(req: Request):
    """디버깅용: ChromaDB 컬렉션을 완전히 초기화합니다."""
    search_service: SearchService = req.app.state.search_service
    search_service.reset_db()
    # index_manager의 데이터도 초기화해야 할 수 있지만, 일단 벡터 DB만 초기화합니다.
    return {"message": "ChromaDB collection has been reset."}
