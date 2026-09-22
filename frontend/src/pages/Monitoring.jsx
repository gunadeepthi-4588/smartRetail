import React from 'react';
import { Activity, AlertCircle, CheckCircle2, TrendingDown, Target, BarChart2 } from 'lucide-react';
import KpiCard from '../components/common/KpiCard';
import Badge from '../components/common/Badge';

export default function Monitoring() {
  return (
    <div>
      <div className="placeholder-banner">
        <AlertCircle size={16} />
        <span>Phase 6 Visual Shell — Forecast Accuracy & Drift Monitoring. Model validation & actuals tracking activates in Phase 14.</span>
      </div>

      {/* Model & Accuracy KPIs */}
      <div className="kpi-grid">
        <KpiCard
          title="MAE (Mean Absolute Error)"
          value="2.8 units"
          subtext="average prediction variance"
          icon={Target}
          iconBg="rgba(99, 102, 241, 0.12)"
          iconColor="#818cf8"
        />
        <KpiCard
          title="WAPE (Weighted % Error)"
          value="8.4%"
          subtext="across top 20 SKUs"
          trend={-1.2}
          icon={Activity}
          iconBg="rgba(16, 185, 129, 0.12)"
          iconColor="#10b981"
        />
        <KpiCard
          title="Model Bias Tendency"
          value="+0.4 units"
          subtext="slight positive buffer (fewer stockouts)"
          icon={BarChart2}
          iconBg="rgba(59, 130, 246, 0.12)"
          iconColor="#3b82f6"
        />
        <KpiCard
          title="Stockout Prevention"
          value="98.5%"
          subtext="service level achieved"
          icon={CheckCircle2}
          iconBg="rgba(16, 185, 129, 0.12)"
          iconColor="#10b981"
        />
      </div>

      {/* Main Grid: Predicted vs Actual Visualizer */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Historical Predicted Demand vs Actual Sales</h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Continuous performance evaluation as sales advance</p>
            </div>
            <Badge status="Healthy" text="Active Evaluation" />
          </div>
          <div style={{
            height: '260px',
            background: 'var(--bg-surface-elevated)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            gap: '0.75rem',
            border: '1px dashed var(--border-medium)'
          }}>
            <Activity size={36} color="var(--primary-400)" />
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Chart.js Predicted vs Actual Time-Series Overlay (Phase 14)
            </span>
          </div>
        </div>

        {/* Health Summary */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Pipeline Health</h2>
            <Badge status="Healthy" text="Online" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.85rem' }}>
            <div style={{ padding: '0.75rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Active Model</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Ridge Regression (Lag 1, 7, 14 + Rolling Mean)</div>
            </div>
            <div style={{ padding: '0.75rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Validation Strategy</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Time-aware temporal split (No future data leakage)</div>
            </div>
            <div style={{ padding: '0.75rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Last Batch Training</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Nightly Automated Run • 0 Errors</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
