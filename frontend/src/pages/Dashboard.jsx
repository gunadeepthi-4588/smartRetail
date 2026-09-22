import React, { useState, useEffect } from 'react';
import {
  DollarSign,
  ShoppingBag,
  Boxes,
  AlertTriangle,
  TrendingUp,
  ArrowUpRight,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import KpiCard from '../components/common/KpiCard';
import Badge from '../components/common/Badge';
import { getAnalyticsDashboard, getSalesTrend, getTopProducts } from '../services/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function Dashboard({ onNavigate }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [topProducts, setTopProducts] = useState({ best_sellers: [], profit_leaders: [] });

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [kpiRes, trendRes, topRes] = await Promise.all([
        getAnalyticsDashboard(),
        getSalesTrend(30),
        getTopProducts({ days: 30, limit: 3 })
      ]);

      setDashboardData(kpiRes.data);
      setTrendData(trendRes.data || []);
      setTopProducts(topRes.data || { best_sellers: [], profit_leaders: [] });
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const formatCurrency = (val) => {
    return `₹${Number(val || 0).toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })}`;
  };

  const fk = dashboardData?.financial_kpis || {};
  const ik = dashboardData?.inventory_kpis || {};

  // Chart setup
  const chartLabels = trendData.map((d) => {
    const parts = d.date.split('-');
    return `${parts[1]}/${parts[2]}`;
  });

  const trendChartConfig = {
    labels: chartLabels,
    datasets: [
      {
        label: 'Revenue (₹)',
        data: trendData.map((d) => d.revenue),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.12)',
        fill: true,
        tension: 0.35,
        pointRadius: trendData.length > 30 ? 0 : 2,
        pointHoverRadius: 4
      }
    ]
  };

  const trendChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1e293b',
        titleColor: '#f8fafc',
        bodyColor: '#e2e8f0',
        borderColor: '#334155',
        borderWidth: 1,
        callbacks: {
          label: (context) => ` Revenue: ₹${Number(context.raw).toLocaleString('en-IN')}`
        }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(51, 65, 85, 0.3)' },
        ticks: { color: '#94a3b8', font: { size: 10 } }
      },
      y: {
        grid: { color: 'rgba(51, 65, 85, 0.3)' },
        ticks: {
          color: '#10b981',
          callback: (val) => `₹${val}`
        }
      }
    }
  };

  return (
    <div>
      {/* Header controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>Operational Overview</h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: '0.25rem 0 0 0' }}>
            Real-time sales velocity, valuation, and stock health alerts
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadData} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="error-banner" style={{ marginBottom: '1.5rem' }}>
          <AlertCircle size={18} />
          <div style={{ flex: 1 }}>{error}</div>
          <button className="btn btn-secondary btn-sm" onClick={loadData}>Retry</button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="kpi-grid">
        <KpiCard
          title="Today's Revenue"
          value={loading ? '...' : formatCurrency(fk.today_revenue)}
          subtext={`${fk.today_transactions || 0} orders today`}
          icon={DollarSign}
          iconBg="rgba(16, 185, 129, 0.12)"
          iconColor="#10b981"
        />
        <KpiCard
          title="30-Day Units Sold"
          value={loading ? '...' : `${Number(fk.units_sold_30d || 0).toLocaleString()} units`}
          subtext={`across ${fk.transactions_30d || 0} transactions`}
          icon={ShoppingBag}
          iconBg="rgba(99, 102, 241, 0.12)"
          iconColor="#818cf8"
        />
        <KpiCard
          title="Inventory Valuation"
          value={loading ? '...' : formatCurrency(ik.total_inventory_value)}
          subtext={`${ik.total_products || 0} active catalog items`}
          icon={Boxes}
          iconBg="rgba(59, 130, 246, 0.12)"
          iconColor="#3b82f6"
        />
        <KpiCard
          title="Critical Stock Alerts"
          value={loading ? '...' : `${(ik.low_stock_count || 0) + (ik.out_of_stock_count || 0)} items`}
          subtext={`${ik.low_stock_count || 0} low, ${ik.out_of_stock_count || 0} stockout`}
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
              <span>Full Analytics</span>
              <ArrowUpRight size={14} />
            </button>
          </div>
          <div style={{ height: '240px', position: 'relative' }}>
            {loading ? (
              <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ color: 'var(--text-muted)' }}>Loading sales curve...</span>
              </div>
            ) : trendData.length === 0 ? (
              <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ color: 'var(--text-muted)' }}>No sales recorded</span>
              </div>
            ) : (
              <Line data={trendChartConfig} options={trendChartOptions} />
            )}
          </div>
        </div>

        {/* Action Center */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Action Center</h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Immediate inventory status</p>
            </div>
            <span className="badge badge-low-stock">
              {(ik.low_stock_count || 0) + (ik.out_of_stock_count || 0)} Risks
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ padding: '0.75rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', borderLeft: '3px solid var(--warning-500)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Low-Stock Buffer</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--warning-500)', fontWeight: 600 }}>{ik.low_stock_count || 0} products</span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Products below safety stock levels requiring replenishment.</p>
            </div>

            <div style={{ padding: '0.75rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', borderLeft: '3px solid var(--danger-500)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Stockouts</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--danger-500)', fontWeight: 600 }}>{ik.out_of_stock_count || 0} products</span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Zero stock items losing daily revenue opportunities.</p>
            </div>

            <button className="btn btn-primary btn-sm" style={{ width: '100%', marginTop: '0.25rem' }} onClick={() => onNavigate('inventory')}>
              Manage Inventory
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
                {loading ? (
                  <tr><td colSpan={3} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>Loading...</td></tr>
                ) : (topProducts.best_sellers || []).length === 0 ? (
                  <tr><td colSpan={3} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No sales data</td></tr>
                ) : (
                  (topProducts.best_sellers || []).map((item) => (
                    <tr key={item.product_id}>
                      <td style={{ fontWeight: 600 }}>{item.name}</td>
                      <td>{item.category}</td>
                      <td style={{ color: 'var(--primary-400)', fontWeight: 600 }}>{item.units_sold} units</td>
                    </tr>
                  ))
                )}
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
                  <th>Gross Margin</th>
                  <th>Gross Profit</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={3} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>Loading...</td></tr>
                ) : (topProducts.profit_leaders || []).length === 0 ? (
                  <tr><td colSpan={3} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No sales data</td></tr>
                ) : (
                  (topProducts.profit_leaders || []).map((item) => (
                    <tr key={item.product_id}>
                      <td style={{ fontWeight: 600 }}>{item.name}</td>
                      <td>{item.gross_margin_pct}%</td>
                      <td style={{ color: 'var(--success-500)', fontWeight: 600 }}>{formatCurrency(item.gross_profit)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
