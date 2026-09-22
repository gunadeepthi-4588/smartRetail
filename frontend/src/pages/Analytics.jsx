import React from 'react';
import { BarChart3, TrendingUp, PieChart, AlertCircle, DollarSign, ArrowUpRight } from 'lucide-react';
import KpiCard from '../components/common/KpiCard';
import Badge from '../components/common/Badge';

export default function Analytics() {
  return (
    <div>
      <div className="placeholder-banner">
        <AlertCircle size={16} />
        <span>Phase 6 Visual Shell — Analytics & Intelligence dashboards. Pandas/NumPy business intelligence aggregation activates in Phase 9.</span>
      </div>

      {/* Financial KPIs */}
      <div className="kpi-grid">
        <KpiCard
          title="Gross Revenue (30D)"
          value="₹37,685.00"
          subtext="30 sales transactions"
          trend={14.8}
          icon={DollarSign}
          iconBg="rgba(16, 185, 129, 0.12)"
          iconColor="#10b981"
        />
        <KpiCard
          title="Gross Profit"
          value="₹11,493.00"
          subtext="30.5% profit margin"
          trend={9.2}
          icon={TrendingUp}
          iconBg="rgba(99, 102, 241, 0.12)"
          iconColor="#818cf8"
        />
        <KpiCard
          title="Inventory Turnover"
          value="3.2x"
          subtext="annualized stock turns"
          icon={BarChart3}
          iconBg="rgba(59, 130, 246, 0.12)"
          iconColor="#3b82f6"
        />
        <KpiCard
          title="Slow-Moving Items"
          value="2 items"
          subtext=">30 days without velocity"
          icon={AlertCircle}
          iconBg="rgba(245, 158, 11, 0.12)"
          iconColor="#f59e0b"
        />
      </div>

      {/* Chart Visualizer Placeholders */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Daily Revenue & Sales Volume</h2>
            <Badge status="Healthy" text="Time Series" />
          </div>
          <div style={{
            height: '220px',
            background: 'var(--bg-surface-elevated)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            gap: '0.5rem',
            border: '1px dashed var(--border-medium)'
          }}>
            <BarChart3 size={32} color="var(--primary-400)" />
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Chart.js Revenue vs Volume Dual-Axis Chart (Phase 9)
            </span>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Category Revenue Distribution</h2>
            <Badge status="Healthy" text="Breakdown" />
          </div>
          <div style={{
            height: '220px',
            background: 'var(--bg-surface-elevated)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            gap: '0.5rem',
            border: '1px dashed var(--border-medium)'
          }}>
            <PieChart size={32} color="#a855f7" />
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Category Profit Contribution Doughnut Chart (Phase 9)
            </span>
          </div>
        </div>
      </div>

      {/* Metrics Breakdown: Best-Sellers vs Revenue Leaders vs Slow-Movers */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1.5rem' }}>
        {/* Best-Sellers */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title" style={{ fontSize: '0.95rem' }}>Volume Best-Sellers</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
              <span>1. Potato Crisps 100g</span>
              <span style={{ fontWeight: 600, color: 'var(--primary-400)' }}>77 units</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
              <span>2. Masala Chai Bags 250g</span>
              <span style={{ fontWeight: 600, color: 'var(--primary-400)' }}>31 units</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
              <span>3. Spicy Corn Nachos</span>
              <span style={{ fontWeight: 600, color: 'var(--primary-400)' }}>19 units</span>
            </div>
          </div>
        </div>

        {/* Revenue Leaders */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title" style={{ fontSize: '0.95rem' }}>Revenue Leaders</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
              <span>1. Basmati Rice 5kg</span>
              <span style={{ fontWeight: 600, color: 'var(--success-500)' }}>₹8,960.00</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
              <span>2. Whole Wheat Atta 10kg</span>
              <span style={{ fontWeight: 600, color: 'var(--success-500)' }}>₹4,950.00</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
              <span>3. Arabica Coffee 500g</span>
              <span style={{ fontWeight: 600, color: 'var(--success-500)' }}>₹4,620.00</span>
            </div>
          </div>
        </div>

        {/* Slow-Moving Inventory */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title" style={{ fontSize: '0.95rem' }}>Slow-Moving Inventory</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
              <span>Microfiber Cloth 3-Pack</span>
              <span style={{ color: 'var(--warning-500)' }}>165 in stock (1 sold)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
              <span>Coconut Shampoo 350ml</span>
              <span style={{ color: 'var(--warning-500)' }}>110 in stock (1 sold)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
