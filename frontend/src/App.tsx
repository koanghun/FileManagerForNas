// 1. Import (모듈 가져오기)
// React 라이브러리와 핵심 Hooks(useState, useEffect)를 가져옵니다.
// useState: 컴포넌트의 상태(state)를 관리하기 위한 Hook.
// useEffect: 컴포넌트의 사이드 이펙트(side effect, 예: 데이터 fetching)를 처리하기 위한 Hook.
import React, { useState, useEffect } from 'react';
import logo from './logo.svg';
import './App.css';

// 2. Interface (타입 정의)
// TypeScript의 인터페이스를 사용하여 파일/디렉터리 아이템 객체의 구조(shape)를 정의합니다.
// 이를 통해 API로부터 받은 데이터의 형식을 강제하고, 개발 중 발생할 수 있는 타입 관련 버그를 예방합니다.
interface FileItem {
  name: string;
  is_directory: boolean;
  path: string;
  size: number | null;
  last_modified: number;
}

// 3. Component (컴포넌트 정의)
// 'App'이라는 이름의 함수형 컴포넌트를 정의합니다. 이 함수가 반환하는 JSX가 화면에 렌더링됩니다.
function App() {
  // 4. State Management (상태 관리)
  // useState Hook을 사용하여 컴포넌트가 기억해야 할 상태(State)를 생성합니다.
  // 상태가 변경되면 컴포넌트는 리렌더링(re-rendering)되어 화면이 업데이트됩니다.

  // `files`: 파일 목록을 저장하는 상태 변수. FileItem 객체들의 배열로 초기화됩니다.
  // `setFiles`: `files` 상태를 업데이트하는 함수.
  const [files, setFiles] = useState<FileItem[]>([]);

  // `currentPath`: 현재 탐색 중인 경로를 저장하는 상태 변수. '.' (현재 디렉터리)로 초기화됩니다.
  // `setCurrentPath`: `currentPath` 상태를 업데이트하는 함수.
  const [currentPath, setCurrentPath] = useState<string>('.');

  // `error`: API 요청 등에서 발생한 에러 메시지를 저장하는 상태 변수. 초기값은 null입니다.
  // `setError`: `error` 상태를 업데이트하는 함수.
  const [error, setError] = useState<string | null>(null);

  // 5. Side Effects & Component Lifecycle (사이드 이펙트와 컴포넌트 라이프사이클)
  // useEffect Hook은 컴포넌트의 라이프사이클(생성, 업데이트, 소멸)에 맞춰 특정 작업을 수행하게 합니다.
  useEffect(() => {
    // Effect 함수: 컴포넌트가 렌더링된 후에 실행될 코드를 담고 있습니다.
    const fetchFiles = async () => {
      try {
        setError(null); // 이전 오류 지우기
        const response = await fetch(`http://localhost:8000/api/files?path=${currentPath}`);
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to fetch files');
        }
        const data = await response.json();
        // setFiles 함수를 호출하여 files 상태를 업데이트합니다. 이로 인해 컴포넌트가 리렌더링됩니다.
        setFiles(data.items);
      } catch (err: any) {
        console.error('Error fetching files:', err);
        setError(err.message || 'An unknown error occurred.');
      }
    };

    fetchFiles();
  }, [currentPath]); // 의존성 배열: 이 배열 안의 값(currentPath)이 변경될 때마다 Effect 함수가 다시 실행됩니다.
                      // - 마운트(Mounting) 시: 컴포넌트가 처음 렌더링될 때 한 번 실행됩니다.
                      // - 업데이트(Updating) 시: `currentPath` 상태가 변경될 때마다 다시 실행됩니다.

  // 6. Event Handlers (이벤트 처리 함수)
  // 사용자의 행동(클릭 등)에 반응하여 특정 로직을 실행하는 함수들입니다.

  // 파일/디렉터리 아이템을 클릭했을 때 호출됩니다.
  const handleItemClick = (item: FileItem) => {
    // 만약 디렉터리라면, setCurrentPath를 호출하여 currentPath 상태를 업데이트합니다.
    // 이 상태 변경이 useEffect를 다시 트리거하는 핵심 연결고리입니다.
    if (item.is_directory) {
      setCurrentPath(item.path);
    }
    // 파일의 경우, 나중에 다운로드 또는 미리보기를 구현할 수 있습니다.
  };

  // "Go Back" 버튼을 클릭했을 때 상위 경로로 currentPath를 변경합니다.
  const handleGoBack = () => {
    const parentPath = currentPath.split('/').slice(0, -1).join('/');
    setCurrentPath(parentPath === '' ? '.' : parentPath);
  };

  // 7. Rendering with JSX (JSX를 사용한 UI 렌더링)
  // 컴포넌트가 화면에 어떻게 보일지를 정의하는 부분입니다. HTML과 유사하지만 JavaScript가 내장된 JSX 문법을 사용합니다.
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <h1>File Explorer</h1>
        {/* 조건부 렌더링: `error` 상태가 null이 아닐 때만 에러 메시지를 렌더링합니다. */}
        {error && <p style={{ color: 'red' }}>Error: {error}</p>}
        <p>Current Path: {currentPath}</p>
        {/* 조건부 렌더링: `currentPath`가 '.'이 아닐 때만 "Go Back" 버튼을 렌더링합니다. */}
        {currentPath !== '.' && (
          <button onClick={handleGoBack}>Go Back</button>
        )}
        <ul>
          {/* 리스트 렌더링: `files` 배열을 순회하며 각 `item`에 대해 `<li>` 태그를 생성합니다. */}
          {files.map((item) => (
            // `key` prop: React가 리스트를 효율적으로 업데이트하기 위해 각 항목을 구별하는 고유한 값입니다.
            // `onClick`: 각 `<li>`에 클릭 이벤트를 연결합니다.
            <li key={item.path} onClick={() => handleItemClick(item)} style={{ cursor: item.is_directory ? 'pointer' : 'default' }}>
              {/* 삼항 연산자를 사용한 조건부 렌더링: 디렉터리 여부에 따라 다른 아이콘을 표시합니다. */}
              {item.is_directory ? '📁' : '📄'} {item.name} {item.is_directory ? '' : `(${Math.round((item.size || 0) / 1024)} KB)`}
            </li>
          ))}
        </ul>
      </header>
    </div>
  );
}

export default App;
