import React from 'react';
import { FileItem as FileItemType, FolderStatus } from '../types';
import './FileItem.css'; // 새로운 CSS 파일 임포트

// 파일 확장자에 따라 적절한 이모지 아이콘을 반환하는 헬퍼 함수
const getFileIcon = (item: FileItemType): string => {
  if (item.is_directory) return '📁';
  const extension = item.name.split('.').pop()?.toLowerCase();
  switch (extension) {
    case 'png': case 'jpg': case 'jpeg': case 'gif': case 'bmp': case 'svg': case 'webp': return '🖼️';
    case 'mp4': case 'avi': case 'mov': case 'mkv': return '🎬';
    case 'mp3': case 'wav': case 'ogg': case 'flac': return '🎵';
    case 'zip': case 'rar': case '7z': case 'tar': case 'gz': return '📦';
    case 'pdf': return '📄';
    case 'doc': case 'docx': return '📝';
    case 'xls': case 'xlsx': return '📊';
    case 'ppt': case 'pptx': return '🖥️';
    case 'txt': case 'md': return '📃';
    case 'js': case 'jsx': case 'ts': case 'tsx': case 'py': case 'html': case 'css': case 'json': return '💻';
    default: return '❓';
  }
};

// FileItem 컴포넌트가 받을 props의 타입을 정의합니다.
interface FileItemProps {
  item: FileItemType;
  onItemClick: (item: FileItemType) => void;
  status?: FolderStatus;
  onIndex: (path: string) => void;
  onDeleteIndex: (path: string) => void;
}

const FileItem: React.FC<FileItemProps> = ({ item, onItemClick, status, onIndex, onDeleteIndex }) => {
  const sizeInKB = Math.round((item.size || 0) / 1024);

  const renderFolderActions = () => {
    if (!item.is_directory || !status) return null;

    const isActionable = status !== 'indexing';

    switch (status) {
      case 'not_indexed':
      case 'failed':
        return (
          <button className="index-button index" onClick={(e) => { e.stopPropagation(); onIndex(item.path); }} disabled={!isActionable}>
            Index
          </button>
        );
      case 'indexed':
      case 'outdated':
        return (
          <>
            <button className="index-button re-index" onClick={(e) => { e.stopPropagation(); onIndex(item.path); }} disabled={!isActionable}>
              Re-index
            </button>
            <button className="index-button delete-index" onClick={(e) => { e.stopPropagation(); onDeleteIndex(item.path); }} disabled={!isActionable}>
              Delete Index
            </button>
          </>
        );
      case 'indexing':
        return <button className="index-button" disabled>Indexing...</button>;
      default:
        return null;
    }
  };

  return (
    <li>
      <div className="file-item-container">
        <div className="file-info" onClick={() => item.is_directory && onItemClick(item)}>
          {item.is_directory && status && <div className={`status-indicator status-${status}`} title={status}></div>}
          <span className="icon">{getFileIcon(item)}</span>
          <span className="name">{item.name}</span>
          {!item.is_directory && <span className="size">({sizeInKB} KB)</span>}
        </div>
        <div className="file-actions">
          {renderFolderActions()}
        </div>
      </div>
    </li>
  );
};

export default FileItem;
