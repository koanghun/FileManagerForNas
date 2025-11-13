import React from 'react';
import logo from '../logo.svg';
import SearchBar from './SearchBar'; // SearchBar 컴포넌트 임포트

interface HeaderProps {
  onSearch: (query: string) => void;
  isSearching: boolean;
}

const Header: React.FC<HeaderProps> = ({ onSearch, isSearching }) => {
  return (
    <header className="App-header">
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px', justifyContent: 'space-between', width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <img src={logo} className="App-logo" alt="logo" />
          <h1 style={{ margin: 0 }}>File Explorer</h1>
        </div>
      </div>
      <SearchBar onSearch={onSearch} isSearching={isSearching} />
    </header>
  );
};

export default Header;
