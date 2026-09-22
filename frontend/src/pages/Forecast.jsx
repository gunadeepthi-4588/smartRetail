import React, { useState } from 'react';
import { TrendingUp, AlertCircle, Sparkles, Calculator, Check, ArrowRight, ShieldCheck } from 'lucide-react';
import KpiCard from '../components/common/KpiCard';
import Badge from '../components/common/Badge';

export default function Forecast() {
  const [selectedProduct, setSelectedProduct] = useState('1');
  const [horizon, setHorizon] = useState(7); // 7 or 30 days

  // Phase 6 Visual Placeholders - Will connect to Scikit-learn ML Forecasting Engine in Phases 10-13
  const mockCalculation = {
    productName: 'Masala Chai Tea Bags 250g',
    currentStock: 12,
    safetyStock: 25,
    leadTimeDays: 2,
    predictedDemand: 48,
    recommendedReorder: 61,
    formula: 'Required Stock (48 + 25 = 73) - Current Stock (12) = 61 Units'
  };

  return (
    <div>
      <div className="placeholder-banner">
        <AlertCircle size={16} />
        <span>Phase 6 Visual Shell — Demand Forecasting & Explainable Reorder Engine. Scikit-learn ML pipeline activates in Phases 10–13.</span>
      </div>

      {/* Control Bar: Product Selector & Horizon Toggle */}
      <div className="controls-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 1 }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Select Target Product:
          </label>
          <select
            className="form-select"
            style={{ maxWidth: '320px' }}
            value={selectedProduct}
            onChange={(e) => setSelectedProduct(e.target.value)}
          >
            <option value="1">Masala Chai Tea Bags 250g (SKU-BEV-001)</option>
            <option value="6">Classic Salted Potato Crisps (SKU-SNK-002)</option>
            <option value="9">Premium Basmati Rice 5kg (SKU-STP-001)</option>
            <option value="2">Arabica Filter Coffee 500g (SKU-BEV-002)</option>
          </select>
        </div>

        <div style={{ display: 'flex', gap: '0.35rem', background: 'var(--bg-surface-elevated)', padding: '0.25rem', borderRadius: 'var(--radius-md)' }}>
          <button
            className={`btn btn-sm ${horizon === 7 ? 'btn-primary' : 'btn-secondary'}`}
            style={{ border: 'none' }}
            onClick={() => setHorizon(7)}
          >
            7-Day Forecast
          </button>
          <button
            className={`btn btn-sm ${horizon === 30 ? 'btn-primary' : 'btn-secondary'}`}
            style={{ border: 'none' }}
            onClick={() => setHorizon(30)}
          >
            30-Day Forecast
          </button>
        </div>
      </div>

      {/* 4 Decision Support Metric Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-header">
            <span>Current In-Store Stock</span>
            <span className="badge badge-low-stock">Low</span>
          </div>
          <div className="kpi-value">{mockCalculation.currentStock} units</div>
          <div className="kpi-footer">Physical shelf count</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span>Safety Stock Buffer</span>
            <span className="badge badge-healthy">Protected</span>
          </div>
          <div className="kpi-value">{mockCalculation.safetyStock} units</div>
          <div className="kpi-footer">Lead time: {mockCalculation.leadTimeDays} days</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span>Forecasted Demand ({horizon}D)</span>
            <span style={{ color: 'var(--primary-400)', fontSize: '0.75rem', fontWeight: 600 }}>ML Output</span>
          </div>
          <div className="kpi-value" style={{ color: 'var(--primary-400)' }}>
            {mockCalculation.predictedDemand} units
          </div>
          <div className="kpi-footer">Estimated sales velocity</div>
        </div>

        <div className="kpi-card" style={{ border: '1px solid rgba(99, 102, 241, 0.4)', background: 'rgba(99, 102, 241, 0.05)' }}>
          <div className="kpi-header">
            <span style={{ color: 'var(--primary-400)' }}>Recommended Order</span>
            <Sparkles size={16} color="var(--primary-400)" />
          </div>
          <div className="kpi-value" style={{ color: '#ffffff' }}>
            {mockCalculation.recommendedReorder} units
          </div>
          <div className="kpi-footer" style={{ color: 'var(--text-secondary)' }}>Explainable recommendation</div>
        </div>
      </div>

      {/* Main Section: Chart + Explainability Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1.2fr', gap: '1.5rem' }}>
        {/* Forecast Visualizer */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Demand Forecast vs Historical Actuals</h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Historical daily sales + {horizon}-day ML projected demand</p>
            </div>
          </div>
          <div style={{
            height: '280px',
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
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Chart.js Historical Line + Forecast Horizon Projection (Phases 10-11)
            </span>
          </div>
        </div>

        {/* Explainability Decision Support Box */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Calculator size={18} color="var(--primary-400)" />
              <h2 className="card-title">Explainable Logic</h2>
            </div>
            <span className="badge badge-healthy">Transparent</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              SmartRetail never places automated purchase orders. Every recommendation is completely transparent:
            </p>

            <div style={{ padding: '1rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.35rem', fontWeight: 600 }}>
                Step-by-Step Mathematical Evaluation
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--primary-400)', lineHeight: '1.6' }}>
                1. Required = Forecast ({mockCalculation.predictedDemand}) + Safety ({mockCalculation.safetyStock}) = 73<br />
                2. Net Order = Required (73) - Current Stock ({mockCalculation.currentStock}) = 61
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              <ShieldCheck size={16} color="var(--success-500)" />
              <span>Protects against stockouts during {mockCalculation.leadTimeDays}-day supplier lead time.</span>
            </div>

            <button className="btn btn-primary" style={{ marginTop: '0.5rem' }}>
              <Check size={16} />
              <span>Mark Recommendation as Reviewed</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
