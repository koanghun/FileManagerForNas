# AI 기반 Synology NAS 파일 관리 시스템

https://eventer-map.mydns.jp:7770/

AI를 활용하여 Synology NAS의 파일을 효율적으로 관리하는 시스템입니다.

## 주요 기능
- 웹 기반 파일 탐색기
- AI 기반 스마트 검색
- 파일 자동 분류 및 태그

## 기술 스택
- **Frontend:** React, TypeScript
- **Backend:** Python, FastAPI
- **Package Manager:** npm (frontend), pip (backend)

## 프로젝트 구조
- **/frontend:** React 기반의 프론트엔드 애플리케이션
- **/backend:** FastAPI 기반의 백엔드 API 서버
- **/doc:** 프로젝트 관련 문서 (요구사항, 아키텍처 등)

## 설치 및 실행 방법

1.  **저장소 복제:**
    ```bash
    git clone https://github.com/GoangHun/FileManagerForNas.git
    cd FileManagerForNas
    ```

2.  **백엔드 설정:**
    ```bash
    # 가상환경 생성
    python -m venv .venv
    # 가상환경 활성화 (Windows)
    .venv\Scripts\activate
    # 의존성 설치
    pip install -r requirements.txt
    ```

3.  **프론트엔드 설정:**
    ```bash
    cd frontend
    npm install
    ```

4.  **개발 서버 실행:**
    - **백엔드 (프로젝트 루트):**
      ```bash
      uvicorn backend.main:app --reload
      ```
    - **프론트엔드 (`frontend` 디렉터리):**
      ```bash
      npm start
      ```
