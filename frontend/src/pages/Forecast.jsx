import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Sparkles,
  RefreshCw,
  AlertCircle,
  Calendar,
  Layers,
  Cpu,
  BarChart2,
  Clock,
  ArrowRight
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
import { getProducts, getProductForecast, generateForecast } from '../services/api';

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

export default function Forecast() {
  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [horizon, setHorizon] = useState(7); // 7 or 30 days
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [forecastData, setForecastData] = useState(null);

  // 1. Fetch products list on mount
  useEffect(() => {
    async function loadProducts() {
      try {
        const res = await getProducts();
        const prods = res.data || [];
        setProducts(prods);
        if (prods.length > 0) {
          setSelectedProductId(String(prods[0].product_id));
        }
      } catch (err) {
        setError('Failed to load products list: ' + err.message);
      }
    }
    loadProducts();
  }, []);

  // 2. Fetch existing forecast when selected product or horizon changes
  useEffect(() => {
    if (!selectedProductId) return;

    async function loadProductForecast() {
      setLoading(true);
      setError(null);
      try {
        const res = await getProductForecast(selectedProductId, horizon);
        setForecastData(res.data);
      } catch (err) {
        setError(err.message || 'Failed to fetch stored forecast.');
      } finally {
        setLoading(false);
      }
    }

    loadProductForecast();
  }, [selectedProductId, horizon]);

  // 3. Handle Generate / Re-run Forecast button click
  const handleGenerateForecast = async () => {
    if (!selectedProductId) return;
    setGenerating(true);
    setError(null);
    try {
      await generateForecast({
        product_id: parseInt(selectedProductId, 10),
        horizon_days: horizon
      });
      // Refresh current product forecast view
      const res = await getProductForecast(selectedProductId, horizon);
      setForecastData(res.data);
    } catch (err) {
      setError(err.message || 'Failed to generate forecast.');
    } finally {
      setGenerating(false);
    }
  };

  // Build combined timeline for Chart.js (Historical actuals + Future predictions)
  const history = forecastData?.history || [];
  const predictions = forecastData?.predictions || [];

  const timelineLabels = [
    ...history.map((h) => {
      const parts = h.date.split('-');
      return `${parts[1]}/${parts[2]}`;
    }),
    ...predictions.map((p) => {
      const parts = p.target_date.split('-');
      return `${parts[1]}/${parts[2]}`;
    })
  ];

  // Actual values aligned across timeline
  const actualDataPoints = [
    ...history.map((h) => h.actual_demand),
    ...predictions.map(() => null)
  ];

  // Predicted values aligned across timeline (connecting from last historical point for continuity)
  const lastHistoricalVal = history.length > 0 ? history[history.length - 1].actual_demand : null;
  const forecastDataPoints = [
    ...history.slice(0, -1).map(() => null),
    lastHistoricalVal,
    ...predictions.map((p) => p.predicted_demand)
  ];

  const chartConfig = {
    labels: timelineLabels,
    datasets: [
      {
        label: 'Historical Actual Sales',
        data: actualDataPoints,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.2,
        pointRadius: 3,
        pointHoverRadius: 5,
        fill: false
      },
      {
        label: `${horizon}-Day Forecasted Demand`,
        data: forecastDataPoints,
        borderColor: '#818cf8',
        backgroundColor: 'rgba(129, 140, 248, 0.15)',
        borderDash: [5, 5],
        tension: 0.35,
        pointRadius: 4,
        pointHoverRadius: 6,
        fill: true
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: '#cbd5e1',
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
            const val = context.raw;
            if (val === null) return null;
            return ` ${context.dataset.label}: ${val} units`;
          }
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
          color: '#94a3b8',
          stepSize: 2
        }
      }
    }
  };

  const totalProjected = predictions.reduce((acc, p) => acc + p.predicted_demand, 0);
  const avgDaily = predictions.length > 0 ? (totalProjected / predictions.length).toFixed(2) : '0.00';
  const selectedProductObj = products.find((p) => String(p.product_id) === String(selectedProductId)) || forecastData?.product;

  return (
    <div>
      {/* Header controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>ML Demand Forecasting</h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: '0.25rem 0 0 0' }}>
            Machine learning unit demand projections powered by Scikit-learn Random Forest
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Horizon Selector */}
          <div style={{ display: 'flex', background: 'var(--bg-surface)', padding: '0.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
            {[7, 30].map((h) => (
              <button
                key={h}
                className={`btn btn-sm ${horizon === h ? 'btn-primary' : 'btn-secondary'}`}
                style={{ border: 'none', padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                onClick={() => setHorizon(h)}
              >
                {h}-Day Horizon
              </button>
            ))}
          </div>

          {/* Generate Forecast Action */}
          <button
            className="btn btn-primary btn-sm"
            onClick={handleGenerateForecast}
            disabled={generating || loading || !selectedProductId}
          >
            <Sparkles size={14} className={generating ? 'spin' : ''} />
            <span>{generating ? 'Forecasting...' : 'Generate New Forecast'}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner" style={{ marginBottom: '1.5rem' }}>
          <AlertCircle size={18} />
          <div style={{ flex: 1 }}>{error}</div>
          <button className="btn btn-secondary btn-sm" onClick={handleGenerateForecast}>Retry</button>
        </div>
      )}

      {/* Target Product Selection Bar */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem 1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Target Product:
          </label>
          <select
            className="form-select"
            style={{ maxWidth: '380px', flex: 1 }}
            value={selectedProductId}
            onChange={(e) => setSelectedProductId(e.target.value)}
          >
            {products.map((p) => (
              <option key={p.product_id} value={p.product_id}>
                {p.name} ({p.sku}) — {p.category}
              </option>
            ))}
          </select>
          {selectedProductObj && (
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <Badge status="Healthy" text={selectedProductObj.category} />
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                SKU: {selectedProductObj.sku}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Forecast Metric Cards */}
      <div className="kpi-grid">
        <KpiCard
          title="Total Projected Demand"
          value={loading || generating ? '...' : `${totalProjected.toFixed(1)} units`}
          subtext={`Cumulative ${horizon}-day forecasted volume`}
          icon={TrendingUp}
          iconBg="rgba(99, 102, 241, 0.12)"
          iconColor="#818cf8"
        />
        <KpiCard
          title="Daily Projected Velocity"
          value={loading || generating ? '...' : `${avgDaily} units/day`}
          subtext="Expected average daily sales rate"
          icon={BarChart2}
          iconBg="rgba(16, 185, 129, 0.12)"
          iconColor="#10b981"
        />
        <KpiCard
          title="Selected Forecast Model"
          value="Random Forest"
          subtext={forecastData?.model_name || 'trees=50, depth=6'}
          icon={Cpu}
          iconBg="rgba(245, 158, 11, 0.12)"
          iconColor="#f59e0b"
        />
        <KpiCard
          title="Forecast Run Timestamp"
          value={forecastData?.forecast_run_date || 'Current'}
          subtext="Persisted in MySQL forecasts table"
          icon={Calendar}
          iconBg="rgba(59, 130, 246, 0.12)"
          iconColor="#3b82f6"
        />
      </div>

      {/* Main Forecast Chart Visualizer */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header">
          <div>
            <h2 className="card-title">Historical Sales & Future Projected Demand Curve</h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Solid line represents recorded actuals; dashed line represents {horizon}-day ML projection
            </p>
          </div>
          <span className="badge badge-healthy">
            {predictions.length > 0 ? `${predictions.length} Step Ahead` : 'No Forecast'}
          </span>
        </div>
        <div style={{ height: '300px', position: 'relative' }}>
          {loading || generating ? (
            <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ color: 'var(--text-muted)' }}>Computing recursive time-series forecast...</span>
            </div>
          ) : predictions.length === 0 ? (
            <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '0.5rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>No forecast generated yet for this product.</span>
              <button className="btn btn-primary btn-sm" onClick={handleGenerateForecast}>
                Generate Initial Forecast
              </button>
            </div>
          ) : (
            <Line data={chartConfig} options={chartOptions} />
          )}
        </div>
      </div>

      {/* Daily Breakdown Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Day-by-Day Forecast Schedule ({horizon} Days)</h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Individual target date predictions persisted in database
            </p>
          </div>
        </div>

        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Step</th>
                <th>Target Date</th>
                <th>Day of Week</th>
                <th>Predicted Demand</th>
                <th>Actual Recorded Sales</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {loading || generating ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    Loading schedule...
                  </td>
                </tr>
              ) : predictions.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No predictions available.
                  </td>
                </tr>
              ) : (
                predictions.map((p, idx) => {
                  const targetD = new Date(p.target_date);
                  const dayName = targetD.toLocaleDateString('en-US', { weekday: 'long' });
                  return (
                    <tr key={p.target_date}>
                      <td style={{ fontWeight: 600, color: 'var(--text-muted)' }}>#{idx + 1}</td>
                      <td style={{ fontWeight: 600 }}>{p.target_date}</td>
                      <td>{dayName}</td>
                      <td style={{ fontWeight: 700, color: 'var(--primary-400)' }}>
                        {p.predicted_demand.toFixed(2)} units
                      </td>
                      <td>
                        {p.actual_demand !== null && p.actual_demand !== undefined ? (
                          <span style={{ fontWeight: 600, color: 'var(--success-500)' }}>
                            {p.actual_demand} units
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Pending Actuals</span>
                        )}
                      </td>
                      <td>
                        {p.actual_demand !== null && p.actual_demand !== undefined ? (
                          <span className="badge badge-healthy">Evaluated</span>
                        ) : (
                          <span className="badge badge-healthy" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', borderColor: 'rgba(99, 102, 241, 0.3)' }}>
                            Forward Projected
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
