import React from 'react';

export default function KpiCard({ title, value, subtext, icon: Icon, iconBg = 'rgba(99, 102, 241, 0.12)', iconColor = '#818cf8', trend }) {
  return (
    <div className="kpi-card">
      <div className="kpi-header">
        <span>{title}</span>
        {Icon && (
          <div className="kpi-icon-box" style={{ background: iconBg, color: iconColor }}>
            <Icon size={18} />
          </div>
        )}
      </div>
      <div className="kpi-value">{value}</div>
      {subtext && (
        <div className="kpi-footer">
          {trend && (
            <span style={{ color: trend > 0 ? 'var(--success-500)' : 'var(--danger-500)', fontWeight: 600 }}>
              {trend > 0 ? `+${trend}%` : `${trend}%`}
            </span>
          )}
          <span>{subtext}</span>
        </div>
      )}
    </div>
  );
}
