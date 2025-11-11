import React from 'react';
import { FileItem as FileItemType } from '../types';
import FileItem from './FileItem';

// FileList 컴포넌트가 받을 props의 타입을 정의합니다.
interface FileListProps {
  files: FileItemType[];
  onItemClick: (item: FileItemType) => void;
}

const FileList: React.FC<FileListProps> = ({ files, onItemClick }) => {
  return (
    <ul>
      {/* `files` 배열을 순회하며 각 `item`에 대해 `FileItem` 컴포넌트를 렌더링합니다. */}
      {files.map((item) => (
        // React가 리스트를 효율적으로 업데이트하기 위해 각 항목을 구별하는 고유한 `key` prop을 전달합니다.
        <FileItem key={item.path} item={item} onItemClick={onItemClick} />
      ))}
    </ul>
  );
};

export default FileList;
