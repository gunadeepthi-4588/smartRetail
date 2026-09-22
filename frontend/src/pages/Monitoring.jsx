import React, { useState, useEffect } from 'react';
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  TrendingDown,
  TrendingUp,
  Target,
  BarChart2,
  Calendar,
  Layers,
  Clock,
  RefreshCw,
  Info,
  ShieldCheck,
  Zap
} from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import KpiCard from '../components/common/KpiCard';
import Badge from '../components/common/Badge';
import {
  getProducts,
  getForecastMonitoring,
  getForecastMonitoringSummary,
  reconcileMonitoringActuals
} from '../services/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function Monitoring() {
  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState(''); // '' means All Products
  const [periodDays, setPeriodDays] = useState(30); // 7, 30, 90
  const [loading, setLoading] = useState(true);
  const [reconciling, setReconciling] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [monitoringData, setMonitoringData] = useState([]);
  const [summaryData, setSummaryData] = useState(null);

  // 1. Fetch products list on mount
  useEffect(() => {
    async function loadProducts() {
      try {
        const res = await getProducts();
        setProducts(res.data || []);
      } catch (err) {
        console.error('Failed to load products for monitoring:', err);
      }
    }
    loadProducts();
  }, []);

  // 2. Fetch monitoring data and summary when filters change
  const fetchMonitoring = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        days: periodDays,
      };
      if (selectedProductId) {
        params.product_id = selectedProductId;
      }

      const [dataRes, sumRes] = await Promise.all([
        getForecastMonitoring(params),
        getForecastMonitoringSummary(params)
      ]);

      setMonitoringData(dataRes.data || []);
      setSummaryData(sumRes || null);
    } catch (err) {
      setError(err.message || 'Failed to fetch forecast monitoring data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonitoring();
  }, [selectedProductId, periodDays]);

  // Handle Manual Reconcile Actuals
  const handleReconcile = async () => {
    setReconciling(true);
    setSuccessMsg(null);
    setError(null);
    try {
      const res = await reconcileMonitoringActuals(selectedProductId ? Number(selectedProductId) : null);
      setSuccessMsg(res.message || 'Actual sales synchronized successfully.');
      await fetchMonitoring();
    } catch (err) {
      setError('Reconciliation failed: ' + err.message);
    } finally {
      setReconciling(false);
    }
  };

  // Extract metrics safely
  const metrics = summaryData?.metrics || {};
  const mae = metrics.mae !== null && metrics.mae !== undefined ? `${metrics.mae} units` : '—';
  const rmse = metrics.rmse !== null && metrics.rmse !== undefined ? `${metrics.rmse} units` : '—';
  const wape = metrics.wape_pct !== null && metrics.wape_pct !== undefined ? `${metrics.wape_pct}%` : '—';
  const biasVal = metrics.bias;
  const biasFormatted = biasVal !== null && biasVal !== undefined ? `${biasVal > 0 ? '+' : ''}${biasVal} units` : '—';

  const sampleCount = summaryData?.sample_count || monitoringData.length || 0;
  const modelName = summaryData?.model_name || 'Random Forest (trees=50, depth=6)';
  const freshness = summaryData?.data_freshness || {};
  const interpretation = summaryData?.interpretation || 'Awaiting historical data for evaluation.';

  // Prepare Dual-Line Chart: Actual Sales vs Predicted Demand
  // Aggregate by date if multiple products selected
  const dateMap = {};
  monitoringData.forEach(item => {
    const d = item.date;
    if (!dateMap[d]) {
      dateMap[d] = { predicted: 0, actual: 0, count: 0 };
    }
    dateMap[d].predicted += item.predicted_demand;
    dateMap[d].actual += item.actual_demand;
    dateMap[d].count += 1;
  });

  const chartDates = Object.keys(dateMap).sort();
  const predictedSeries = chartDates.map(d => Math.round(dateMap[d].predicted * 100) / 100);
  const actualSeries = chartDates.map(d => Math.round(dateMap[d].actual * 100) / 100);

  const demandComparisonChartData = {
    labels: chartDates.map(d => {
      const parts = d.split('-');
      return parts.length === 3 ? `${parts[1]}/${parts[2]}` : d;
    }),
    datasets: [
      {
        label: 'Actual Demand (Units Sold)',
        data: actualSeries,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.12)',
        pointBackgroundColor: '#10b981',
        pointBorderColor: '#ffffff',
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 2.5,
        fill: true,
        tension: 0.3
      },
      {
        label: 'Predicted Demand (Forecast)',
        data: predictedSeries,
        borderColor: '#818cf8',
        backgroundColor: 'rgba(129, 140, 248, 0.05)',
        pointBackgroundColor: '#818cf8',
        pointBorderColor: '#ffffff',
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 2.5,
        borderDash: [5, 4],
        fill: false,
        tension: 0.3
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#94a3b8',
          font: { family: 'Outfit, sans-serif', size: 12 },
          usePointStyle: true,
          pointStyle: 'circle'
        }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(15, 23, 42, 0.92)',
        titleColor: '#f8fafc',
        bodyColor: '#e2e8f0',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 10,
        callbacks: {
          afterBody: (context) => {
            if (context.length >= 2) {
              const act = context[0].raw || 0;
              const pred = context[1].raw || 0;
              const diff = Math.round((act - pred) * 100) / 100;
              const sign = diff > 0 ? '+' : '';
              return `Variance (Actual - Pred): ${sign}${diff} units`;
            }
            return '';
          }
        }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.04)' },
        ticks: { color: '#64748b', font: { size: 11 } }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.06)' },
        ticks: { color: '#64748b', font: { size: 11 } },
        beginAtZero: true
      }
    }
  };

  // Error Trend Chart (Error = Actual - Predicted)
  const errorSeries = chartDates.map(d => Math.round((dateMap[d].actual - dateMap[d].predicted) * 100) / 100);
  const errorColors = errorSeries.map(val => val >= 0 ? 'rgba(59, 130, 246, 0.85)' : 'rgba(245, 158, 11, 0.85)');

  const errorChartData = {
    labels: chartDates.map(d => {
      const parts = d.split('-');
      return parts.length === 3 ? `${parts[1]}/${parts[2]}` : d;
    }),
    datasets: [
      {
        label: 'Forecast Error (Actual - Predicted)',
        data: errorSeries,
        backgroundColor: errorColors,
        borderRadius: 4,
        borderWidth: 0
      }
    ]
  };

  const errorChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.92)',
        titleColor: '#f8fafc',
        bodyColor: '#e2e8f0',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        callbacks: {
          label: (context) => {
            const val = context.raw;
            const status = val > 0 ? 'Under-predicted (+ demand > forecast)' : val < 0 ? 'Over-predicted (- forecast > demand)' : 'Exact match';
            return `Error: ${val > 0 ? '+' : ''}${val} units (${status})`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.04)' },
        ticks: { color: '#64748b', font: { size: 11 } }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.06)' },
        ticks: { color: '#64748b', font: { size: 11 } }
      }
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', paddingBottom: '3rem' }}>
      {/* Top Filter Bar */}
      <div className="card" style={{ padding: '1.25rem 1.5rem' }}>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            {/* Product Selector */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Layers size={16} color="var(--primary-400)" />
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Product:</span>
              <select
                className="input-field"
                style={{ width: '220px', padding: '0.45rem 0.75rem', fontSize: '0.85rem' }}
                value={selectedProductId}
                onChange={(e) => setSelectedProductId(e.target.value)}
              >
                <option value="">All Monitored Products</option>
                {products.map((p) => (
                  <option key={p.product_id} value={p.product_id}>
                    {p.name} ({p.sku})
                  </option>
                ))}
              </select>
            </div>

            {/* Monitoring Period Selector */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Calendar size={16} color="var(--primary-400)" />
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Evaluation Period:</span>
              <div style={{ display: 'flex', gap: '0.25rem', background: 'var(--bg-surface-elevated)', padding: '3px', borderRadius: 'var(--radius-md)' }}>
                {[7, 30, 90].map((days) => (
                  <button
                    key={days}
                    type="button"
                    onClick={() => setPeriodDays(days)}
                    style={{
                      padding: '0.35rem 0.75rem',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      borderRadius: 'var(--radius-sm)',
                      border: 'none',
                      cursor: 'pointer',
                      background: periodDays === days ? 'var(--primary-600)' : 'transparent',
                      color: periodDays === days ? '#ffffff' : 'var(--text-secondary)',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    {days} Days
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Sync / Reconcile Button */}
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleReconcile}
            disabled={reconciling || loading}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', padding: '0.45rem 0.9rem' }}
          >
            <RefreshCw size={14} className={reconciling ? 'animate-spin' : ''} />
            <span>{reconciling ? 'Syncing...' : 'Sync Actual Sales'}</span>
          </button>
        </div>
      </div>

      {/* Notifications / Alerts */}
      {error && (
        <div style={{
          padding: '0.85rem 1rem',
          background: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: 'var(--radius-md)',
          color: '#f87171',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div style={{
          padding: '0.85rem 1rem',
          background: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: 'var(--radius-md)',
          color: '#34d399',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <CheckCircle2 size={16} />
          <span>{successMsg}</span>
        </div>
      )}

      {/* KPI Accuracy Cards */}
      <div className="kpi-grid">
        <KpiCard
          title="MAE (Mean Absolute Error)"
          value={mae}
          subtext="mean(|actual - predicted|) demand"
          icon={Target}
          iconBg="rgba(99, 102, 241, 0.12)"
          iconColor="#818cf8"
        />
        <KpiCard
          title="RMSE (Root Mean Squared Error)"
          value={rmse}
          subtext="sqrt(mean((actual - predicted)²))"
          icon={Activity}
          iconBg="rgba(16, 185, 129, 0.12)"
          iconColor="#10b981"
        />
        <KpiCard
          title="WAPE (Weighted % Error)"
          value={wape}
          subtext="sum(|actual - pred|) / sum(actual)"
          icon={BarChart2}
          iconBg="rgba(59, 130, 246, 0.12)"
          iconColor="#3b82f6"
        />
        <KpiCard
          title="Forecast Bias"
          value={biasFormatted}
          subtext="mean(predicted - actual)"
          icon={biasVal && biasVal > 0 ? TrendingUp : TrendingDown}
          iconBg={biasVal && biasVal > 0 ? "rgba(245, 158, 11, 0.12)" : "rgba(139, 92, 246, 0.12)"}
          iconColor={biasVal && biasVal > 0 ? "#f59e0b" : "#8b5cf6"}
        />
      </div>

      {/* Interpretation & Model Health Banner */}
      <div className="card" style={{ padding: '1.25rem 1.5rem', background: 'var(--bg-surface-elevated)' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', alignItems: 'center' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
              <Info size={16} color="var(--primary-400)" />
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Deterministic Performance Interpretation
              </span>
              <Badge status={sampleCount > 0 ? "Healthy" : "Neutral"} text={`${sampleCount} Observations`} />
            </div>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
              {interpretation}
            </p>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', fontStyle: 'italic' }}>
              * Monitoring measures historical forecast performance; it does not guarantee future forecast accuracy.
            </p>
          </div>

          {/* Model Metadata Box */}
          <div style={{
            background: 'var(--bg-surface)',
            padding: '0.85rem 1rem',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-medium)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.4rem',
            fontSize: '0.8rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Evaluated Model:</span>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{modelName}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Last Forecast Date:</span>
              <span style={{ color: 'var(--text-secondary)' }}>{freshness.last_forecast_date || 'N/A'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Last Actual Sales Date:</span>
              <span style={{ color: 'var(--text-secondary)' }}>{freshness.last_actual_date || 'N/A'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Visualizations: Overlay Line Chart & Error Trend */}
      {sampleCount === 0 && !loading ? (
        <div className="card" style={{
          padding: '3rem 2rem',
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1rem'
        }}>
          <AlertCircle size={40} color="var(--primary-400)" />
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.35rem' }}>
              No Historical Evaluation Records Found
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', maxWidth: '500px' }}>
              {freshness.message || 'Actual sales data is not yet available for this forecast period. Generate forecasts or synchronize historical sales to populate monitoring metrics.'}
            </p>
          </div>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleReconcile}
            disabled={reconciling}
            style={{ fontSize: '0.85rem' }}
          >
            <RefreshCw size={14} className={reconciling ? 'animate-spin' : ''} style={{ marginRight: '0.5rem' }} />
            Sync Actual Sales Now
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '1.5rem' }}>
          {/* Chart 1: Actual Demand vs Predicted Demand */}
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title">Actual Sales vs Predicted Demand</h2>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Daily time-series comparison over selected {periodDays}-day window
                </p>
              </div>
              <Badge status="Healthy" text="Time Series" />
            </div>
            <div style={{ height: '300px', position: 'relative' }}>
              {loading ? (
                <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <RefreshCw size={24} className="animate-spin" color="var(--primary-400)" />
                </div>
              ) : (
                <Line data={demandComparisonChartData} options={chartOptions} />
              )}
            </div>
          </div>

          {/* Chart 2: Error Trend (Actual - Predicted) */}
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title">Forecast Error Trend</h2>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Error = Actual - Predicted (Blue: Under-predicted, Amber: Over-predicted)
                </p>
              </div>
              <Badge status="Neutral" text="Variance" />
            </div>
            <div style={{ height: '300px', position: 'relative' }}>
              {loading ? (
                <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <RefreshCw size={24} className="animate-spin" color="var(--primary-400)" />
                </div>
              ) : (
                <Bar data={errorChartData} options={errorChartOptions} />
              )}
            </div>
          </div>
        </div>
      )}

      {/* Historical Forecast vs Actual Demand Breakdown Table */}
      {monitoringData.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Historical Evaluation Records</h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Detailed product-level forecast verification records ({monitoringData.length} records)
              </p>
            </div>
          </div>

          <div className="table-container" style={{ maxHeight: '420px', overflowY: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Target Date</th>
                  <th>Product</th>
                  <th>SKU</th>
                  <th style={{ textAlign: 'right' }}>Predicted Demand</th>
                  <th style={{ textAlign: 'right' }}>Actual Demand</th>
                  <th style={{ textAlign: 'right' }}>Error (Act - Pred)</th>
                  <th style={{ textAlign: 'right' }}>Abs Error</th>
                  <th style={{ textAlign: 'right' }}>Error %</th>
                  <th>Evaluated Model</th>
                </tr>
              </thead>
              <tbody>
                {monitoringData.map((row, idx) => {
                  const isPositiveError = row.error >= 0;
                  return (
                    <tr key={`${row.forecast_id}-${idx}`}>
                      <td style={{ fontWeight: 500 }}>{row.date}</td>
                      <td>{row.product_name || `Product #${row.product_id}`}</td>
                      <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{row.sku || '—'}</td>
                      <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--primary-300)' }}>
                        {row.predicted_demand.toFixed(1)} units
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 600, color: '#34d399' }}>
                        {row.actual_demand.toFixed(1)} units
                      </td>
                      <td style={{
                        textAlign: 'right',
                        fontWeight: 600,
                        color: isPositiveError ? '#60a5fa' : '#fbbf24'
                      }}>
                        {isPositiveError ? `+${row.error.toFixed(1)}` : row.error.toFixed(1)}
                      </td>
                      <td style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>
                        {row.absolute_error.toFixed(1)}
                      </td>
                      <td style={{ textAlign: 'right', color: 'var(--text-muted)' }}>
                        {row.percentage_error !== null ? `${row.percentage_error}%` : 'N/A'}
                      </td>
                      <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {row.model_name}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
