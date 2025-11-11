// 1. Import (모듈 가져오기)
import React, { useState, useEffect } from 'react';
import './App.css';
import { FileItem as FileItemType } from './types';
import Header from './components/Header';
import PathNavigator from './components/PathNavigator';
import FileList from './components/FileList';

// 2. Component (컴포넌트 정의)
function App() {
  // 3. State Management (상태 관리)
  const [files, setFiles] = useState<FileItemType[]>([]);
  const [currentPath, setCurrentPath] = useState<string>('.');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false); // 로딩 상태 추가

  // 4. Side Effects & Data Fetching (사이드 이펙트와 데이터 요청)
  useEffect(() => {
    const fetchFiles = async () => {
      setIsLoading(true); // 데이터 요청 시작 시 로딩 상태 true
      try {
        setError(null);
        const response = await fetch(`http://localhost:8000/api/files?path=${encodeURIComponent(currentPath)}`);
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to fetch files');
        }
        const data = await response.json();
        setFiles(data.items);
      } catch (err: any) {
        console.error('Error fetching files:', err);
        setError(err.message || 'An unknown error occurred.');
      } finally {
        setIsLoading(false); // 데이터 요청 완료 시 로딩 상태 false
      }
    };

    fetchFiles();
  }, [currentPath]);

  // 5. Event Handlers (이벤트 처리 함수)
  const handleItemClick = (item: FileItemType) => {
    if (item.is_directory) {
      setCurrentPath(item.path);
    }
  };

  const handleGoBack = () => {
    const parentPath = currentPath.split('/').slice(0, -1).join('/');
    setCurrentPath(parentPath === '' ? '.' : parentPath);
  };

  // 6. Rendering (UI 렌더링)
  // 상태와 핸들러를 각 UI 컴포넌트에 props로 전달하여 렌더링을 위임합니다.
  return (
    <div className="App">
      <Header />
      <div className="file-explorer-container">
        {error && <p style={{ color: 'red' }}>Error: {error}</p>}
        
        {isLoading ? (
          <p>Loading files...</p> // 로딩 중일 때 메시지 표시
        ) : (
          <>
            <PathNavigator 
              currentPath={currentPath} 
              onGoBack={handleGoBack} 
            />
            
            <FileList 
              files={files} 
              onItemClick={handleItemClick} 
            />
          </>
        )}
      </div>
    </div>
  );
}

export default App;
