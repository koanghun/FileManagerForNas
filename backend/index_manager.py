import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Literal

# 상태를 나타내는 타입 정의
IndexStatus = Literal["indexed", "not_indexed", "outdated", "indexing", "failed"] # Add "failed"

class IndexManager:
    def __init__(self, db_path: str = "index_metadata.db"):
        self.db_path = Path(db_path)
        self.conn = None
        self._connect()
        self._create_table()
        self._cleanup_stale_indexing_statuses() # Call cleanup on startup

    def _connect(self):
        """데이터베이스에 연결합니다."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def _create_table(self):
        """'indexed_folders' 테이블이 없으면 생성합니다."""
        try:
            with self.conn:
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS indexed_folders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        provider_id TEXT NOT NULL,
                        folder_path TEXT NOT NULL,
                        last_indexed_at TIMESTAMP,
                        status TEXT NOT NULL,
                        file_count INTEGER DEFAULT 0,
                        UNIQUE(provider_id, folder_path)
                    )
                """)
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

    def _cleanup_stale_indexing_statuses(self):
        """
        서버 재시작 시 남아있는 'indexing' 상태를 'failed'로 변경합니다.
        """
        try:
            with self.conn:
                cursor = self.conn.execute("""
                    SELECT provider_id, folder_path FROM indexed_folders WHERE status = 'indexing'
                """)
                stale_folders = cursor.fetchall()
                
                if stale_folders:
                    print(f"Found {len(stale_folders)} stale 'indexing' statuses. Resetting to 'failed'.")
                    for folder in stale_folders:
                        self.conn.execute("""
                            UPDATE indexed_folders SET status = 'failed' WHERE provider_id = ? AND folder_path = ?
                        """, (folder['provider_id'], folder['folder_path']))
                    self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error cleaning up stale indexing statuses: {e}")

    def set_folder_status(self, provider_id: str, folder_path: str, status: str, file_count: int = 0):
        """폴더의 인덱싱 상태를 설정하거나 업데이트합니다."""
        now = datetime.datetime.now()
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT INTO indexed_folders (provider_id, folder_path, last_indexed_at, status, file_count)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(provider_id, folder_path) DO UPDATE SET
                        last_indexed_at = excluded.last_indexed_at,
                        status = excluded.status,
                        file_count = excluded.file_count
                """, (provider_id, folder_path, now, status, file_count))
        except sqlite3.Error as e:
            print(f"Error setting folder status: {e}")

    def get_folder_status(self, provider_id: str, folder_path: str) -> Dict | None:
        """특정 폴더의 상태 정보를 가져옵니다."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM indexed_folders WHERE provider_id = ? AND folder_path = ?
            """, (provider_id, folder_path))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Error getting folder status: {e}")
            return None

    def get_multiple_folder_statuses(self, provider_id: str, folder_paths: List[str]) -> Dict[str, Dict]:
        """여러 폴더의 상태 정보를 한 번에 가져옵니다."""
        if not folder_paths:
            return {}
        
        placeholders = ','.join('?' for _ in folder_paths)
        query = f"SELECT * FROM indexed_folders WHERE provider_id = ? AND folder_path IN ({placeholders})"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, [provider_id] + folder_paths)
            rows = cursor.fetchall()
            return {row['folder_path']: dict(row) for row in rows}
        except sqlite3.Error as e:
            print(f"Error getting multiple folder statuses: {e}")
            return {}

    def remove_folder(self, provider_id: str, folder_path: str):
        """폴더의 인덱싱 정보를 삭제합니다."""
        try:
            with self.conn:
                self.conn.execute("""
                    DELETE FROM indexed_folders WHERE provider_id = ? AND folder_path = ?
                """, (provider_id, folder_path))
        except sqlite3.Error as e:
            print(f"Error removing folder: {e}")

    def close(self):
        """데이터베이스 연결을 닫습니다."""
        if self.conn:
            self.conn.close()
            self.conn = None

index_manager = IndexManager()
