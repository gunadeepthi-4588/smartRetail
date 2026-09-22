import React, { useState, useEffect } from 'react';
import AppLayout from './components/layout/AppLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
import Sales from './pages/Sales';
import Analytics from './pages/Analytics';
import Forecast from './pages/Forecast';
import Monitoring from './pages/Monitoring';
import Settings from './pages/Settings';

export default function App() {
  // State-driven routing for single-page application
  const [currentRoute, setCurrentRoute] = useState(() => {
    const path = window.location.pathname.replace(/^\//, '');
    return path || 'dashboard';
  });
  const [isAuthenticated, setIsAuthenticated] = useState(true);

  // Sync browser back/forward buttons with route state
  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname.replace(/^\//, '');
      setCurrentRoute(path || 'dashboard');
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigateTo = (route) => {
    setCurrentRoute(route);
    window.history.pushState({}, '', `/${route === 'dashboard' ? '' : route}`);
    window.scrollTo(0, 0);
  };

  const handleLogin = () => {
    setIsAuthenticated(true);
    navigateTo('dashboard');
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    navigateTo('login');
  };

  if (!isAuthenticated || currentRoute === 'login') {
    return <Login onLoginSuccess={handleLogin} />;
  }

  return (
    <AppLayout
      activeRoute={currentRoute}
      onNavigate={navigateTo}
      onLogout={handleLogout}
    >
      {currentRoute === 'dashboard' && <Dashboard onNavigate={navigateTo} />}
      {currentRoute === 'inventory' && <Inventory />}
      {currentRoute === 'sales' && <Sales />}
      {currentRoute === 'analytics' && <Analytics />}
      {currentRoute === 'forecast' && <Forecast />}
      {currentRoute === 'monitoring' && <Monitoring />}
      {currentRoute === 'settings' && <Settings />}
    </AppLayout>
  );
}
