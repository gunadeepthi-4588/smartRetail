import React, { useState, useEffect } from 'react';
import {
  DollarSign,
  TrendingUp,
  ShoppingBag,
  Boxes,
  AlertCircle,
  RefreshCw,
  Calendar,
  Layers,
  Award,
  Sparkles,
  ArrowUpRight,
  Clock
} from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Doughnut } from 'react-chartjs-2';
import KpiCard from '../components/common/KpiCard';
import Badge from '../components/common/Badge';
import {
  getAnalyticsDashboard,
  getSalesTrend,
  getTopProducts,
  getSlowMovers,
  getCategoryPerformance
} from '../services/api';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function Analytics() {
  const [timeRange, setTimeRange] = useState(30); // 7, 30, 90
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [dashboardData, setDashboardData] = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [topProducts, setTopProducts] = useState({ best_sellers: [], revenue_leaders: [], profit_leaders: [] });
  const [slowMovers, setSlowMovers] = useState([]);
  const [categoryData, setCategoryData] = useState([]);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const [kpiRes, trendRes, topRes, slowRes, catRes] = await Promise.all([
        getAnalyticsDashboard(),
        getSalesTrend(timeRange),
        getTopProducts({ days: timeRange, limit: 5 }),
        getSlowMovers({ days_threshold: 30 }),
        getCategoryPerformance({ days: timeRange })
      ]);

      setDashboardData(kpiRes.data);
      setTrendData(trendRes.data || []);
      setTopProducts(topRes.data || { best_sellers: [], revenue_leaders: [], profit_leaders: [] });
      setSlowMovers(slowRes.data || []);
      setCategoryData(catRes.data || []);
    } catch (err) {
      setError(err.message || 'Failed to load analytics data from server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  // Format currency
  const formatCurrency = (val) => {
    return `₹${Number(val || 0).toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })}`;
  };

  // Trend Chart Configuration
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
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        yAxisID: 'y',
        fill: true,
        tension: 0.35,
        pointRadius: trendData.length > 30 ? 0 : 3,
        pointHoverRadius: 5
      },
      {
        label: 'Units Sold',
        data: trendData.map((d) => d.units_sold),
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.05)',
        yAxisID: 'y1',
        borderDash: [4, 4],
        tension: 0.35,
        pointRadius: trendData.length > 30 ? 0 : 3,
        pointHoverRadius: 5
      }
    ]
  };

  const trendChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false
    },
    plugins: {
      legend: {
        labels: {
          color: '#94a3b8',
          font: { family: 'Outfit, sans-serif', size: 12 }
        }
      },
      tooltip: {
        backgroundColor: '#1e293b',
        titleColor: '#f8fafc',
        bodyColor: '#e2e8f0',
        borderColor: '#334155',
        borderWidth: 1,
        padding: 10,
        callbacks: {
          label: (context) => {
            if (context.datasetIndex === 0) {
              return ` Revenue: ₹${Number(context.raw).toLocaleString('en-IN')}`;
            }
            return ` Units Sold: ${context.raw} units`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(51, 65, 85, 0.4)' },
        ticks: { color: '#94a3b8', font: { size: 10 } }
      },
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        grid: { color: 'rgba(51, 65, 85, 0.4)' },
        ticks: {
          color: '#10b981',
          callback: (val) => `₹${val}`
        }
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        grid: { drawOnChartArea: false },
        ticks: {
          color: '#818cf8',
          stepSize: 5
        }
      }
    }
  };

  // Category Doughnut Chart Configuration
  const categoryColors = [
    '#6366f1',
    '#10b981',
    '#f59e0b',
    '#ec4899',
    '#06b6d4',
    '#8b5cf6',
    '#14b8a6',
    '#f97316'
  ];

  const doughnutConfig = {
    labels: categoryData.map((c) => c.category),
    datasets: [
      {
        data: categoryData.map((c) => c.revenue),
        backgroundColor: categoryColors.slice(0, categoryData.length),
        borderColor: '#1e293b',
        borderWidth: 2
      }
    ]
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          color: '#cbd5e1',
          font: { family: 'Outfit, sans-serif', size: 11 },
          boxWidth: 12
        }
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const val = context.raw;
            return ` ${context.label}: ₹${Number(val).toLocaleString('en-IN')}`;
          }
        }
      }
    }
  };

  const fk = dashboardData?.financial_kpis || {};
  const ik = dashboardData?.inventory_kpis || {};

  return (
    <div>
      {/* Top Controls Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>Business Analytics & Intelligence</h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: '0.25rem 0 0 0' }}>
            Descriptive performance intelligence aggregated live from MySQL transactions
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {/* Time Range Selector */}
          <div style={{ display: 'flex', background: 'var(--bg-surface)', padding: '0.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
            {[7, 30, 90].map((days) => (
              <button
                key={days}
                className={`btn btn-sm ${timeRange === days ? 'btn-primary' : 'btn-secondary'}`}
                style={{ border: 'none', padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                onClick={() => setTimeRange(days)}
              >
                {days} Days
              </button>
            ))}
          </div>

          <button className="btn btn-secondary btn-sm" onClick={loadAnalytics} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner" style={{ marginBottom: '1.5rem' }}>
          <AlertCircle size={18} />
          <div style={{ flex: 1 }}>{error}</div>
          <button className="btn btn-secondary btn-sm" onClick={loadAnalytics}>Retry</button>
        </div>
      )}

      {/* Financial & Inventory KPIs */}
      <div className="kpi-grid">
        <KpiCard
          title={`${timeRange}-Day Gross Revenue`}
          value={loading ? '...' : formatCurrency(fk.revenue_30d)}
          subtext={`${fk.transactions_30d || 0} customer orders`}
          icon={DollarSign}
          iconBg="rgba(16, 185, 129, 0.12)"
          iconColor="#10b981"
        />
        <KpiCard
          title={`${timeRange}-Day Gross Profit`}
          value={loading ? '...' : formatCurrency(fk.gross_profit_30d)}
          subtext={`${fk.gross_margin_pct_30d || 0}% average gross margin`}
          icon={TrendingUp}
          iconBg="rgba(99, 102, 241, 0.12)"
          iconColor="#818cf8"
        />
        <KpiCard
          title={`${timeRange}-Day Units Sold`}
          value={loading ? '...' : `${Number(fk.units_sold_30d || 0).toLocaleString()} units`}
          subtext="Volume moved through POS"
          icon={ShoppingBag}
          iconBg="rgba(59, 130, 246, 0.12)"
          iconColor="#3b82f6"
        />
        <KpiCard
          title="Inventory Valuation"
          value={loading ? '...' : formatCurrency(ik.total_inventory_value)}
          subtext={`${ik.total_products || 0} active catalog items`}
          icon={Boxes}
          iconBg="rgba(245, 158, 11, 0.12)"
          iconColor="#f59e0b"
        />
      </div>

      {/* Main Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1.2fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Sales Trend Chart */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Sales & Revenue Timeline ({timeRange}D)</h2>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Daily revenue vs units sold</p>
            </div>
            <Badge status="Healthy" text="Time Series" />
          </div>
          <div style={{ height: '260px', position: 'relative' }}>
            {loading ? (
              <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ color: 'var(--text-muted)' }}>Loading sales trend...</span>
              </div>
            ) : trendData.length === 0 ? (
              <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ color: 'var(--text-muted)' }}>No sales recorded in this period</span>
              </div>
            ) : (
              <Line data={trendChartConfig} options={trendChartOptions} />
            )}
          </div>
        </div>

        {/* Category Contribution Doughnut */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Category Revenue Contribution</h2>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Distribution across departments</p>
            </div>
            <Badge status="Healthy" text="Mix" />
          </div>
          <div style={{ height: '260px', position: 'relative' }}>
            {loading ? (
              <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ color: 'var(--text-muted)' }}>Loading categories...</span>
              </div>
            ) : categoryData.length === 0 ? (
              <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ color: 'var(--text-muted)' }}>No category data</span>
              </div>
            ) : (
              <Doughnut data={doughnutConfig} options={doughnutOptions} />
            )}
          </div>
        </div>
      </div>

      {/* Metrics Breakdown: 3 Distinct Leaders Columns */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* 1. Volume Best-Sellers */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title" style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Award size={18} color="var(--primary-400)" />
                <span>Volume Best-Sellers</span>
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Ranked strictly by Units Sold (SUM(qty))</p>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {loading ? (
              <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading best-sellers...</span>
            ) : topProducts.best_sellers.length === 0 ? (
              <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No sales data</span>
            ) : (
              topProducts.best_sellers.map((item, idx) => (
                <div key={item.product_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--border-light)' }}>
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{idx + 1}. {item.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.category} • {item.sku}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 700, color: 'var(--primary-400)', fontSize: '0.9rem' }}>{item.units_sold} units</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{formatCurrency(item.revenue)}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 2. Revenue Leaders */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title" style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <DollarSign size={18} color="var(--success-500)" />
                <span>Revenue Leaders</span>
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Ranked by Total Value (SUM(qty * price))</p>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {loading ? (
              <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading revenue leaders...</span>
            ) : topProducts.revenue_leaders.length === 0 ? (
              <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No sales data</span>
            ) : (
              topProducts.revenue_leaders.map((item, idx) => (
                <div key={item.product_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--border-light)' }}>
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{idx + 1}. {item.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.category} • {item.units_sold} units</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 700, color: 'var(--success-500)', fontSize: '0.9rem' }}>{formatCurrency(item.revenue)}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{item.sku}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 3. Gross Profit Leaders */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title" style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <TrendingUp size={18} color="#818cf8" />
                <span>Gross Profit Leaders</span>
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Ranked by SUM(qty * (price - unit_cost))</p>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {loading ? (
              <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading profit leaders...</span>
            ) : topProducts.profit_leaders.length === 0 ? (
              <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No sales data</span>
            ) : (
              topProducts.profit_leaders.map((item, idx) => (
                <div key={item.product_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--border-light)' }}>
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{idx + 1}. {item.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.category} • {item.gross_margin_pct}% margin</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 700, color: '#818cf8', fontSize: '0.9rem' }}>{formatCurrency(item.gross_profit)}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Rev: {formatCurrency(item.revenue)}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Slow-Moving Inventory Intelligence Section */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Clock size={18} color="var(--warning-500)" />
              <span>Slow-Moving Products & Capital Lockup</span>
            </h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Active items with &gt;30 days since last sale or low velocity (tied up capital in warehouse)
            </p>
          </div>
          <span className="badge badge-low-stock">
            {slowMovers.length} Slow-Movers Detected
          </span>
        </div>

        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Category</th>
                <th>Current Stock</th>
                <th>Last Sale Date</th>
                <th>Days Dormant</th>
                <th>Holding Value (Cost)</th>
                <th>Diagnosis</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    Analyzing inventory velocity...
                  </td>
                </tr>
              ) : slowMovers.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No slow-moving products found. Inventory velocity is healthy.
                  </td>
                </tr>
              ) : (
                slowMovers.map((item) => (
                  <tr key={item.product_id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{item.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.sku}</div>
                    </td>
                    <td>{item.category}</td>
                    <td>
                      <span style={{ fontWeight: 600 }}>{item.current_stock}</span> units
                    </td>
                    <td>
                      {item.never_sold ? (
                        <span style={{ color: 'var(--warning-500)', fontSize: '0.8rem' }}>Never Sold</span>
                      ) : (
                        item.last_sale_date ? item.last_sale_date.split(' ')[0] : '—'
                      )}
                    </td>
                    <td>
                      {item.never_sold ? (
                        <span className="badge badge-out-of-stock">No Sales</span>
                      ) : (
                        <span style={{ color: 'var(--warning-500)', fontWeight: 600 }}>
                          {item.days_since_last_sale} days
                        </span>
                      )}
                    </td>
                    <td style={{ fontWeight: 600, color: 'var(--danger-500)' }}>
                      {formatCurrency(item.inventory_holding_value)}
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {item.reason}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
