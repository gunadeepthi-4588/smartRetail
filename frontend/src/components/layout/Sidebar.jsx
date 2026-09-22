import React from 'react';
import { 
  LayoutDashboard, 
  Boxes, 
  Receipt, 
  BarChart3, 
  TrendingUp, 
  Activity, 
  Settings, 
  LogOut,
  Store
} from 'lucide-react';

const MAIN_NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'inventory', label: 'Inventory', icon: Boxes },
  { id: 'sales', label: 'Sales & POS', icon: Receipt },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'forecast', label: 'Demand Forecast', icon: TrendingUp },
  { id: 'monitoring', label: 'Monitoring', icon: Activity },
];

export default function Sidebar({ activeRoute, onNavigate, onLogout }) {
  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="sidebar-brand">
        <div className="brand-logo">
          <Store size={18} />
        </div>
        <div className="brand-title">SmartRetail</div>
      </div>

      {/* Main Navigation */}
      <nav className="sidebar-nav">
        <div className="nav-section-title">Core Operations</div>
        {MAIN_NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeRoute === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Footer Navigation */}
      <div className="sidebar-footer">
        <div className="nav-section-title">System</div>
        <button
          className={`nav-item ${activeRoute === 'settings' ? 'active' : ''}`}
          onClick={() => onNavigate('settings')}
        >
          <Settings size={18} />
          <span>Settings</span>
        </button>
        <button
          className="nav-item"
          onClick={onLogout}
          style={{ color: 'var(--danger-500)' }}
        >
          <LogOut size={18} />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
