from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# CORS 미들웨어 추가
origins = [
    "http://localhost",
    "http://localhost:3000", # 프론트엔드 출처 허용
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to AI File Management Backend!"}

@app.get("/api/test")
def test_api():
    return {"message": "Hello from FastAPI!"}

@app.get("/api/files")
def list_files(path: str = "."): # 현재 디렉터리를 기본값으로 설정
    try:
        # 경로가 안전하고 프로젝트 디렉터리(또는 지정된 루트) 내에 있는지 확인
        # 현재는 모든 경로를 허용하지만, 실제 NAS 시스템에서는 제한될 것입니다.
        # 데모를 위해 루트를 프로젝트 디렉터리로 가정합니다.
        base_path = os.getcwd() # 백엔드의 현재 작업 디렉터리 가져오기
        full_path = os.path.join(base_path, path)
        full_path = os.path.normpath(full_path)

        # 기본 보안 검사: 경로가 base_path 밖으로 나가지 않도록 확인
        if not full_path.startswith(base_path):
            raise HTTPException(status_code=403, detail="Access denied: Path outside allowed directory.")

        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Directory not found.")
        if not os.path.isdir(full_path):
            raise HTTPException(status_code=400, detail="Path is not a directory.")

        items = []
        for item_name in os.listdir(full_path):
            item_path = os.path.join(full_path, item_name)
            is_directory = os.path.isdir(item_path)
            items.append({
                "name": item_name,
                "is_directory": is_directory,
                "path": os.path.relpath(item_path, base_path), # base_path에 대한 상대 경로 반환
                "size": os.path.getsize(item_path) if not is_directory else None,
                "last_modified": os.path.getmtime(item_path)
            })
        return {"path": path, "items": items}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"내부 서버 오류: {e}") # 내부 서버 오류: {e}
