import React from 'react';
import logo from '../logo.svg';

const Header: React.FC = () => {
  return (
    <header className="App-header">
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '20px' }}>
        <img src={logo} className="App-logo" alt="logo" />
        <h1>File Explorer</h1>
      </div>
    </header>
  );
};

export default Header;
