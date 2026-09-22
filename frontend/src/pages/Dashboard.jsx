import React from 'react';
import { DollarSign, ShoppingBag, Boxes, AlertTriangle, TrendingUp, AlertCircle, ArrowUpRight } from 'lucide-react';
import KpiCard from '../components/common/KpiCard';
import Badge from '../components/common/Badge';

export default function Dashboard({ onNavigate }) {
  return (
    <div>
      <div className="placeholder-banner">
        <AlertCircle size={16} />
        <span>Phase 6 Visual Shell — UI layout initialized with visual placeholders; live REST API connection activates in Phase 7.</span>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <KpiCard
          title="Today's Revenue"
          value="₹1,620.00"
          subtext="vs yesterday"
          trend={12.4}
          icon={DollarSign}
          iconBg="rgba(16, 185, 129, 0.12)"
          iconColor="#10b981"
        />
        <KpiCard
          title="Total Units Sold"
          value="247 units"
          subtext="across 30 transactions"
          trend={8.1}
          icon={ShoppingBag}
          iconBg="rgba(99, 102, 241, 0.12)"
          iconColor="#818cf8"
        />
        <KpiCard
          title="Inventory Valuation"
          value="₹84,250.00"
          subtext="20 active catalog items"
          icon={Boxes}
          iconBg="rgba(59, 130, 246, 0.12)"
          iconColor="#3b82f6"
        />
        <KpiCard
          title="Critical Alerts"
          value="3 items"
          subtext="stock below safety threshold"
          icon={AlertTriangle}
          iconBg="rgba(245, 158, 11, 0.12)"
          iconColor="#f59e0b"
        />
      </div>

      {/* Main Grid: Trends & Action Center */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Sales & Revenue Trend */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">30-Day Sales & Revenue Trend</h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Historical daily sales velocity over time</p>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('analytics')}>
              <span>View Analytics</span>
              <ArrowUpRight size={14} />
            </button>
          </div>
          <div style={{
            height: '240px',
            background: 'var(--bg-surface-elevated)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            gap: '0.75rem',
            border: '1px dashed var(--border-medium)'
          }}>
            <TrendingUp size={36} color="var(--primary-400)" />
            <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              Interactive Chart.js Trend Visualizer (Configured for Phase 9)
            </span>
          </div>
        </div>

        {/* Action Center */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Action Center</h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Immediate attention required</p>
            </div>
            <span className="badge badge-low-stock">3 Risks</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ padding: '0.75rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', borderLeft: '3px solid var(--warning-500)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Potato Crisps 100g</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--warning-500)' }}>Stock: 8 / Safety: 30</span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Critically low stock buffer.</p>
            </div>
            <div style={{ padding: '0.75rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', borderLeft: '3px solid var(--warning-500)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Masala Chai Bags 250g</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--warning-500)' }}>Stock: 12 / Safety: 25</span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Fast-moving item approaching reorder line.</p>
            </div>
            <button className="btn btn-primary btn-sm" style={{ width: '100%', marginTop: '0.25rem' }} onClick={() => onNavigate('forecast')}>
              Review Reorder Recommendations
            </button>
          </div>
        </div>
      </div>

      {/* Bottom Row: Volume Leaders vs Profit Leaders */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Top Best-Sellers (Volume)</h2>
            <Badge status="Healthy" text="Top Units" />
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Category</th>
                  <th>Units Sold</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ fontWeight: 600 }}>Classic Salted Potato Crisps</td>
                  <td>Snacks</td>
                  <td style={{ color: 'var(--primary-400)', fontWeight: 600 }}>77 units</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Masala Chai Tea Bags 250g</td>
                  <td>Beverages</td>
                  <td style={{ color: 'var(--primary-400)', fontWeight: 600 }}>31 units</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Spicy Corn Nachos 150g</td>
                  <td>Snacks</td>
                  <td style={{ color: 'var(--primary-400)', fontWeight: 600 }}>19 units</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Top Profit Leaders (Gross Margin)</h2>
            <Badge status="Healthy" text="Top Margin" />
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Unit Margin</th>
                  <th>Gross Profit</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ fontWeight: 600 }}>Premium Basmati Rice 5kg</td>
                  <td>₹140.00 / unit</td>
                  <td style={{ color: 'var(--success-500)', fontWeight: 600 }}>₹2,240.00</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Arabica Filter Coffee 500g</td>
                  <td>₹110.00 / unit</td>
                  <td style={{ color: 'var(--success-500)', fontWeight: 600 }}>₹1,540.00</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Roasted Salted Cashews</td>
                  <td>₹80.00 / unit</td>
                  <td style={{ color: 'var(--success-500)', fontWeight: 600 }}>₹1,280.00</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
