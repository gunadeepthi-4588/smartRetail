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

  // User session state with localStorage persistence
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('smartretail_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const isAuthenticated = !!user;

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

  const handleLogin = (userData) => {
    setUser(userData);
    try {
      localStorage.setItem('smartretail_user', JSON.stringify(userData));
    } catch (e) {
      console.warn('Failed saving user to localStorage', e);
    }
    navigateTo('dashboard');
  };

  const handleLogout = () => {
    setUser(null);
    try {
      localStorage.removeItem('smartretail_user');
    } catch (e) {
      console.warn('Failed clearing user from localStorage', e);
    }
    navigateTo('login');
  };

  // Protected route guard: unauthenticated visits or explicit /login route
  if (!isAuthenticated || currentRoute === 'login') {
    return <Login onLoginSuccess={handleLogin} />;
  }

  return (
    <AppLayout
      activeRoute={currentRoute}
      onNavigate={navigateTo}
      onLogout={handleLogout}
      user={user}
    >
      {currentRoute === 'dashboard' && <Dashboard onNavigate={navigateTo} />}
      {currentRoute === 'inventory' && <Inventory />}
      {currentRoute === 'sales' && <Sales />}
      {currentRoute === 'analytics' && <Analytics />}
      {currentRoute === 'forecast' && <Forecast />}
      {currentRoute === 'monitoring' && <Monitoring />}
      {currentRoute === 'settings' && <Settings user={user} />}
    </AppLayout>
  );
}

