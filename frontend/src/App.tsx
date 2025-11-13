// 1. Import (모듈 가져오기)
import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import { FileItem as FileItemType, SearchResult, FolderStatusMap } from './types';
import Header from './components/Header';
import PathNavigator from './components/PathNavigator';
import FileList from './components/FileList';
import Login from './components/Login';
import SearchResults from './components/SearchResults'; // 검색 결과 컴포넌트
import './components/SearchBar.css'; // SearchBar CSS 추가
import './components/SearchResults.css'; // SearchResults CSS 추가


// --- Helper Functions ---
const getErrorMessage = (err: any): string => {
  let errorMessage = 'An unknown error occurred.';
  
  // FastAPI 유효성 검사 에러 처리 (err.detail이 배열일 경우)
  if (err.detail && Array.isArray(err.detail) && err.detail[0]?.msg) {
    errorMessage = err.detail.map((d: any) => `${d.loc[d.loc.length - 1]}: ${d.msg}`).join('; ');
  } 
  // 일반적인 FastAPI 에러 처리 (err.detail이 문자열일 경우)
  else if (err.detail && typeof err.detail === 'string') {
    errorMessage = err.detail;
  } 
  // 그 외 일반적인 JavaScript 에러 처리
  else if (err.message) {
    errorMessage = err.message;
  }
  
  return errorMessage;
};


// 2. Component (컴포넌트 정의)
function App() {
  // 3. State Management (상태 관리)
  const [files, setFiles] = useState<FileItemType[]>([]);
  const [currentPath, setCurrentPath] = useState<string>('/');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [sessionToken, setSessionToken] = useState<string | null>(null);

  const [viewMode, setViewMode] = useState<'files' | 'search'>('files');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);

  // 인덱싱 상태 관리
  const [folderStatuses, setFolderStatuses] = useState<FolderStatusMap>({});

  // 4. Side Effects & Data Fetching (사이드 이펙트와 데이터 요청)
  const fetchFolderStatuses = useCallback(async (directories: string[]): Promise<FolderStatusMap | null> => {
    if (directories.length === 0 || !sessionToken) return null;
    try {
      const response = await fetch('http://localhost:8000/api/index/status', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionToken}`
        },
        body: JSON.stringify({ folder_paths: directories }),
      });
      if (!response.ok) throw await response.json();
      const statuses = await response.json();
      setFolderStatuses(prev => ({ ...prev, ...statuses }));
      return statuses;
    } catch (err) {
      console.error('Error fetching folder statuses:', err);
      return null;
    }
  }, [sessionToken]);

  useEffect(() => {
    if (!isLoggedIn || !sessionToken || viewMode !== 'files') return;

    const fetchFiles = async () => {
      setIsLoading(true);
      try {
        setError(null);
        const response = await fetch(`http://localhost:8000/api/files?path=${encodeURIComponent(currentPath)}`, {
          headers: { 'Authorization': `Bearer ${sessionToken}` }
        });
        if (!response.ok) throw await response.json();
        
        const data = await response.json();
        setFiles(data.items);

        // 파일 목록 로드 후, 디렉토리들의 상태를 조회합니다.
        const directories = data.items
          .filter((item: FileItemType) => item.is_directory)
          .map((item: FileItemType) => item.path);
        fetchFolderStatuses(directories);

      } catch (err: any) {
        console.error('Error fetching files:', err);
        setError(getErrorMessage(err));
      } finally {
        setIsLoading(false);
      }
    };

    fetchFiles();
  }, [currentPath, isLoggedIn, sessionToken, viewMode, fetchFolderStatuses]);

  // 5. Event Handlers (이벤트 처리 함수)
  const handleLogin = async (credentials: any) => {
    try {
      setError(null);
      const response = await fetch('http://localhost:8000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });
      if (!response.ok) throw await response.json();
      const data = await response.json();
      setSessionToken(data.token);
      setIsLoggedIn(true);
    } catch (err: any) {
      console.error('Login failed:', err);
      setError(getErrorMessage(err));
    }
  };

  const handleItemClick = (item: FileItemType) => {
    if (item.is_directory) {
      setCurrentPath(item.path);
    }
  };

  const handleGoBack = () => {
    if (currentPath === '/') return;
    const parentPath = currentPath.split('/').slice(0, -1).join('/') || '/';
    setCurrentPath(parentPath);
  };

  const handleSearch = async (query: string) => {
    if (!sessionToken) return;
    setIsSearching(true);
    setError(null);
    setSearchQuery(query);
    try {
      const response = await fetch(`http://localhost:8000/api/search?query=${encodeURIComponent(query)}`, {
        headers: { 'Authorization': `Bearer ${sessionToken}` }
      });
      if (!response.ok) throw await response.json();
      const data = await response.json();
      setSearchResults(data.results);
      setViewMode('search');
    } catch (err: any) {
      console.error('Error during search:', err);
      setError(getErrorMessage(err));
    } finally {
      setIsSearching(false);
    }
  };

  const handleClearSearch = () => {
    setViewMode('files');
    setSearchQuery('');
    setSearchResults([]);
  };

  const handleIndexFolder = async (folderPath: string) => {
    if (!sessionToken) return;
    setFolderStatuses(prev => ({ ...prev, [folderPath]: 'indexing' }));
    try {
      const response = await fetch('http://localhost:8000/api/index/folder', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionToken}`
        },
        body: JSON.stringify({ folder_path: folderPath }),
      });
      if (!response.ok) throw await response.json();
      
      // 3초마다 상태를 폴링하여 확인
      const intervalId = setInterval(async () => {
        const newStatuses = await fetchFolderStatuses([folderPath]);
        if (newStatuses && newStatuses[folderPath] !== 'indexing') {
          clearInterval(intervalId);
        }
      }, 3000);

    } catch (err: any) {
      console.error(`Error indexing folder ${folderPath}:`, err);
      setError(getErrorMessage(err));
      setFolderStatuses(prev => ({ ...prev, [folderPath]: 'failed' }));
    }
  };

  const handleDeleteIndex = async (folderPath: string) => {
    if (!sessionToken) return;
    try {
      const response = await fetch('http://localhost:8000/api/index/folder', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionToken}`
        },
        body: JSON.stringify({ folder_path: folderPath }),
      });
      if (!response.ok) throw await response.json();
      setFolderStatuses(prev => ({ ...prev, [folderPath]: 'not_indexed' }));
    } catch (err: any) {
      console.error(`Error deleting index for ${folderPath}:`, err);
      setError(getErrorMessage(err));
    }
  };

  // 6. Rendering (UI 렌더링)
  if (!isLoggedIn) {
    return <Login onLogin={handleLogin} error={error} />;
  }

  return (
    <div className="App">
      <Header onSearch={handleSearch} isSearching={isSearching} />
      <div className="file-explorer-container">
        {error && <p style={{ color: 'red' }}>Error: {error}</p>}
        
        {viewMode === 'files' && (
          isLoading ? (
            <p>Loading files...</p>
          ) : (
            <>
              <PathNavigator 
                currentPath={currentPath} 
                onGoBack={handleGoBack} 
              />
              <FileList 
                files={files} 
                onItemClick={handleItemClick}
                folderStatuses={folderStatuses}
                onIndexFolder={handleIndexFolder}
                onDeleteIndex={handleDeleteIndex}
              />
            </>
          )
        )}

        {viewMode === 'search' && (
          isSearching ? (
            <p>Searching...</p>
          ) : (
            <SearchResults 
              results={searchResults}
              query={searchQuery}
              onClear={handleClearSearch}
            />
          )
        )}
      </div>
    </div>
  );
}

export default App;
