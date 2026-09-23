import React from 'react';
import Sidebar from './Sidebar';
import Header from './Header';

export default function AppLayout({ activeRoute, onNavigate, onLogout, user, children }) {
  return (
    <div className="app-container">
      <Sidebar activeRoute={activeRoute} onNavigate={onNavigate} onLogout={onLogout} user={user} />
      <div className="main-wrapper">
        <Header
          activeRoute={activeRoute}
          userName={user?.name || 'Rajesh Kumar'}
          storeName={user?.store_name || 'Metro Mart Superstore'}
          userRole={user?.role || 'Store Owner'}
        />
        <main className="content-area">{children}</main>
      </div>
    </div>
  );
}
