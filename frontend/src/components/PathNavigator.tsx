import React from 'react';

// PathNavigator 컴포넌트가 받을 props의 타입을 정의합니다.
interface PathNavigatorProps {
  currentPath: string;
  onGoBack: () => void;
}

const PathNavigator: React.FC<PathNavigatorProps> = ({ currentPath, onGoBack }) => {
  return (
    <div className="path-navigator">
      <p>Current Path: {currentPath}</p>
      {/* `currentPath`가 최상위 경로('.')가 아닐 때만 "Go Back" 버튼을 보여줍니다. */}
      {currentPath !== '.' && (
        <button onClick={onGoBack}>Go Back</button>
      )}
    </div>
  );
};

export default PathNavigator;
