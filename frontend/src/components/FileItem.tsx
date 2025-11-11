import React from 'react';
import { FileItem as FileItemType } from '../types';

// 파일 확장자에 따라 적절한 이모지 아이콘을 반환하는 헬퍼 함수
const getFileIcon = (item: FileItemType): string => {
  if (item.is_directory) {
    return '📁'; // 디렉터리 아이콘
  }

  const extension = item.name.split('.').pop()?.toLowerCase();

  switch (extension) {
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
    case 'bmp':
    case 'svg':
    case 'webp':
      return '🖼️'; // 이미지 파일
    case 'mp4':
    case 'avi':
    case 'mov':
    case 'mkv':
      return '🎬'; // 비디오 파일
    case 'mp3':
    case 'wav':
    case 'ogg':
    case 'flac':
      return '🎵'; // 오디오 파일
    case 'zip':
    case 'rar':
    case '7z':
    case 'tar':
    case 'gz':
      return '📦'; // 압축 파일
    case 'pdf':
      return '📄'; // PDF 파일
    case 'doc':
    case 'docx':
      return '📝'; // 워드 문서
    case 'xls':
    case 'xlsx':
      return '📊'; // 엑셀 문서
    case 'ppt':
    case 'pptx':
      return ' presentation_emoji'; // 파워포인트 문서 (적절한 이모지 선택)
    case 'txt':
    case 'md':
      return '📃'; // 텍스트/마크다운 파일
    case 'js':
    case 'jsx':
    case 'ts':
    case 'tsx':
    case 'py':
    case 'html':
    case 'css':
    case 'json':
      return '💻'; // 코드 파일
    default:
      return '❓'; // 알 수 없는 파일 타입
  }
};

// FileItem 컴포넌트가 받을 props의 타입을 정의합니다.
interface FileItemProps {
  item: FileItemType;
  onItemClick: (item: FileItemType) => void;
}

const FileItem: React.FC<FileItemProps> = ({ item, onItemClick }) => {
  // 파일 크기를 KB 단위로 변환하고, 소수점 첫째 자리까지 표시합니다.
  // 파일이 아닌 경우(디렉터리)나 크기가 없는 경우 0을 사용합니다.
  const sizeInKB = Math.round((item.size || 0) / 1024);

  return (
    <li 
      onClick={() => onItemClick(item)} 
      style={{ cursor: item.is_directory ? 'pointer' : 'default' }}
    >
      <span className="icon">{getFileIcon(item)}</span> {/* 헬퍼 함수를 사용하여 아이콘 렌더링 */}
      <span className="name">{item.name}</span>
      
      {!item.is_directory && <span className="size">({sizeInKB} KB)</span>}
    </li>
  );
};

export default FileItem;
