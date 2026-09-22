import React from 'react';
import Sidebar from './Sidebar';
import Header from './Header';

export default function AppLayout({ activeRoute, onNavigate, onLogout, children }) {
  return (
    <div className="app-container">
      <Sidebar activeRoute={activeRoute} onNavigate={onNavigate} onLogout={onLogout} />
      <div className="main-wrapper">
        <Header activeRoute={activeRoute} />
        <main className="content-area">{children}</main>
      </div>
    </div>
  );
}
