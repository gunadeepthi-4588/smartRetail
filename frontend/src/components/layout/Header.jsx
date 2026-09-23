import React from 'react';
import { Store } from 'lucide-react';

const PAGE_TITLES = {
  dashboard: 'Executive Dashboard',
  inventory: 'Inventory & Stock Management',
  sales: 'Sales & POS Terminal',
  analytics: 'Analytics & Business Intelligence',
  forecast: 'ML Demand Forecasting & Decision Support',
  monitoring: 'Forecast Accuracy & Model Monitoring',
  settings: 'Store Configuration & Diagnostics'
};

export default function Header({
  activeRoute,
  storeName = 'Metro Mart Superstore',
  userName = 'Rajesh Kumar',
  userRole = 'Store Owner'
}) {
  const title = PAGE_TITLES[activeRoute] || 'SmartRetail';
  const initials = userName
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .join('')
    .toUpperCase() || 'RK';

  return (
    <header className="top-header">
      <div className="header-left">
        <h1 className="page-title">{title}</h1>
        <div className="store-badge">
          <Store size={13} />
          <span>{storeName}</span>
        </div>
      </div>

      <div className="header-right">
        <div className="user-profile">
          <div className="avatar">{initials}</div>
          <div className="user-info">
            <span className="user-name">{userName}</span>
            <span className="user-role">{userRole}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
