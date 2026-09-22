import React, { useState, useEffect, useCallback } from 'react';
import { 
  Search, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle2, 
  Boxes, 
  AlertTriangle, 
  PackageX, 
  TrendingUp,
  Brain,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  Clock,
  Layers,
  HelpCircle,
  X,
  Calculator,
  Info
} from 'lucide-react';
import { getInventory, getInventoryIntelligence } from '../services/api';
import Badge from '../components/common/Badge';

export default function Inventory() {
  const [activeTab, setActiveTab] = useState('intelligence'); // 'intelligence' or 'catalog'
  const [horizon, setHorizon] = useState(7); // 7 or 30 days
  
  // Catalog State
  const [inventoryList, setInventoryList] = useState([]);
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');

  // Intelligence State
  const [intelligenceList, setIntelligenceList] = useState([]);
  const [isIntelligenceLoading, setIsIntelligenceLoading] = useState(false);
  const [intelligenceError, setIntelligenceError] = useState(null);
  const [intelStatusFilter, setIntelStatusFilter] = useState('All');

  // Selected item for Explainability Details Modal
  const [selectedExplainItem, setSelectedExplainItem] = useState(null);

  // 1. Fetch Standard Inventory
  const loadInventory = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getInventory({
        search: searchTerm,
        category: categoryFilter,
        status: statusFilter
      });
      setInventoryList(response.data || []);
      setSummary(response.summary || null);
    } catch (err) {
      setError(err.message || 'Unable to load inventory records.');
    } finally {
      setIsLoading(false);
    }
  }, [searchTerm, categoryFilter, statusFilter]);

  // 2. Fetch Inventory Intelligence & Reorder Engine
  const loadIntelligence = useCallback(async () => {
    setIsIntelligenceLoading(true);
    setIntelligenceError(null);
    try {
      const res = await getInventoryIntelligence({ days: horizon });
      setIntelligenceList(res.data || []);
    } catch (err) {
      setIntelligenceError(err.message || 'Unable to load inventory intelligence.');
    } finally {
      setIsIntelligenceLoading(false);
    }
  }, [horizon]);

  useEffect(() => {
    if (activeTab === 'catalog') {
      const handler = setTimeout(() => {
        loadInventory();
      }, 200);
      return () => clearTimeout(handler);
    } else {
      loadIntelligence();
    }
  }, [activeTab, loadInventory, loadIntelligence]);

  // Filtered intelligence list
  const filteredIntelligence = intelligenceList.filter((item) => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          item.sku.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = intelStatusFilter === 'All' ? true : 
                          intelStatusFilter === 'REORDER' ? item.recommendation_status === 'REORDER' :
                          intelStatusFilter === 'STOCKOUT_RISK' ? item.stockout_risk :
                          intelStatusFilter === 'OVERSTOCK' ? item.overstock_risk : true;
    return matchesSearch && matchesStatus;
  });

  const totalReorderItems = intelligenceList.filter((i) => i.recommendation_status === 'REORDER').length;
  const totalStockoutRisks = intelligenceList.filter((i) => i.stockout_risk).length;
  const totalOverstocked = intelligenceList.filter((i) => i.overstock_risk).length;

  return (
    <div>
      {/* Header & View Switcher */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>Inventory Management & Intelligence</h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: '0.25rem 0 0 0' }}>
            Decision-support reorder engine, transparent mathematical explainability, and risk monitoring
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Main Tab Toggle */}
          <div style={{ display: 'flex', background: 'var(--bg-surface)', padding: '0.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
            <button
              className={`btn btn-sm ${activeTab === 'intelligence' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ border: 'none', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem' }}
              onClick={() => setActiveTab('intelligence')}
            >
              <Brain size={14} />
              <span>Inventory Intelligence ({totalReorderItems} Reorders)</span>
            </button>
            <button
              className={`btn btn-sm ${activeTab === 'catalog' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ border: 'none', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem' }}
              onClick={() => setActiveTab('catalog')}
            >
              <Boxes size={14} />
              <span>Stock Catalog</span>
            </button>
          </div>

          {activeTab === 'intelligence' && (
            <div style={{ display: 'flex', background: 'var(--bg-surface)', padding: '0.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
              {[7, 30].map((h) => (
                <button
                  key={h}
                  className={`btn btn-sm ${horizon === h ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ border: 'none', padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                  onClick={() => setHorizon(h)}
                >
                  {h}D Horizon
                </button>
              ))}
            </div>
          )}

          <button 
            className="btn btn-secondary btn-sm" 
            onClick={activeTab === 'intelligence' ? loadIntelligence : loadInventory}
            disabled={activeTab === 'intelligence' ? isIntelligenceLoading : isLoading}
          >
            <RefreshCw size={14} className={(activeTab === 'intelligence' ? isIntelligenceLoading : isLoading) ? 'spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* INTELLIGENCE TAB VIEW */}
      {activeTab === 'intelligence' && (
        <>
          {/* Summary Metric Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            <div className="card" style={{ padding: '1rem', borderLeft: '4px solid var(--primary-400)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                Reorder Recommended
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--primary-400)', marginTop: '0.25rem' }}>
                {totalReorderItems} Products
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Required stock &gt; current stock
              </div>
            </div>

            <div className="card" style={{ padding: '1rem', borderLeft: '4px solid var(--danger-500)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                Stockout Risk Buffer
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--danger-500)', marginTop: '0.25rem' }}>
                {totalStockoutRisks} Products
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Stock &lt; lead time demand + safety
              </div>
            </div>

            <div className="card" style={{ padding: '1rem', borderLeft: '4px solid var(--warning-500)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                Overstock Risk Warning
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--warning-500)', marginTop: '0.25rem' }}>
                {totalOverstocked} Products
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Stock &gt; 1.5x 30-day velocity
              </div>
            </div>

            <div className="card" style={{ padding: '1rem', borderLeft: '4px solid var(--success-500)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                Decision Protocol
              </div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', marginTop: '0.25rem' }}>
                Store Owner Decides
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--success-500)' }}>
                Never auto-orders (MVP Locked)
              </div>
            </div>
          </div>

          {/* Intelligence Filters Bar */}
          <div className="card" style={{ marginBottom: '1.5rem', padding: '0.75rem 1.25rem' }}>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <div className="search-input-wrapper" style={{ flex: 1, minWidth: '240px' }}>
                <Search size={16} className="search-icon" />
                <input
                  type="text"
                  className="form-input search-input"
                  placeholder="Filter intelligence by product name or SKU..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              <select
                className="form-select"
                style={{ width: 'auto', minWidth: '180px' }}
                value={intelStatusFilter}
                onChange={(e) => setIntelStatusFilter(e.target.value)}
              >
                <option value="All">All Recommendations</option>
                <option value="REORDER">Action: REORDER Only</option>
                <option value="STOCKOUT_RISK">High Stockout Risk</option>
                <option value="OVERSTOCK">Overstocked Items</option>
              </select>
            </div>
          </div>

          {/* Intelligence Table */}
          {isIntelligenceLoading ? (
            <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1rem' }}>
              <RefreshCw size={32} className="spin" style={{ margin: '0 auto 1rem', color: 'var(--primary-400)' }} />
              <h3 style={{ fontSize: '1.1rem', marginBottom: '0.25rem' }}>Computing Inventory Intelligence...</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Calculating lead-time demand, risk buffers, and explainable reorder quantities</p>
            </div>
          ) : intelligenceError ? (
            <div className="error-banner">
              <AlertCircle size={18} />
              <div style={{ flex: 1 }}>{intelligenceError}</div>
              <button className="btn btn-secondary btn-sm" onClick={loadIntelligence}>Retry</button>
            </div>
          ) : (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Product & SKU</th>
                      <th>Current Stock</th>
                      <th>Lead Time</th>
                      <th>Safety Stock</th>
                      <th>Lead-Time Demand</th>
                      <th>{horizon}D Forecast</th>
                      <th>Stockout Risk</th>
                      <th>Overstock Risk</th>
                      <th>Recommended Reorder</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredIntelligence.map((item) => (
                      <tr key={item.product_id}>
                        <td>
                          <div style={{ fontWeight: 600 }}>{item.name}</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.sku} • {item.category}</div>
                        </td>
                        <td style={{ fontWeight: 700, fontSize: '0.95rem' }}>
                          {item.current_stock}
                        </td>
                        <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                          {item.lead_time_days} days
                        </td>
                        <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                          {item.safety_stock} units
                        </td>
                        <td style={{ color: '#818cf8', fontWeight: 600 }}>
                          {item.lead_time_demand}
                        </td>
                        <td style={{ color: 'var(--primary-400)', fontWeight: 600 }}>
                          {item.forecasted_demand}
                        </td>
                        <td>
                          {item.stockout_risk ? (
                            <span className="badge badge-out-of-stock" title={`Shortage gap: ${item.stockout_gap} units`}>
                              Risk (-{item.stockout_gap})
                            </span>
                          ) : (
                            <span className="badge badge-healthy">Protected</span>
                          )}
                        </td>
                        <td>
                          {item.overstock_risk ? (
                            <span className="badge badge-low-stock" title={item.overstock_note}>
                              Overstock
                            </span>
                          ) : (
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Normal</span>
                          )}
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span style={{ fontWeight: 700, fontSize: '0.95rem', color: item.recommended_quantity > 0 ? 'var(--primary-400)' : 'var(--text-muted)' }}>
                              {item.recommended_quantity > 0 ? `+${item.recommended_quantity} units` : '0'}
                            </span>
                            {item.recommendation_status === 'REORDER' && (
                              <span className="badge badge-healthy" style={{ background: 'rgba(99, 102, 241, 0.2)', color: '#818cf8', borderColor: 'rgba(99, 102, 241, 0.4)', fontSize: '0.7rem' }}>
                                REORDER
                              </span>
                            )}
                          </div>
                        </td>
                        <td>
                          <button
                            className="btn btn-secondary btn-sm"
                            style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                            onClick={() => setSelectedExplainItem(item)}
                          >
                            <HelpCircle size={13} color="var(--primary-400)" />
                            <span>Why?</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* CATALOG TAB VIEW (Existing Live Product List) */}
      {activeTab === 'catalog' && (
        <>
          {summary && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
              <div className="card" style={{ padding: '1rem' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Total Valuation</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--primary-400)', marginTop: '0.25rem' }}>
                  ₹{Number(summary.total_valuation || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
              </div>
              <div className="card" style={{ padding: '1rem' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Total Units</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, marginTop: '0.25rem' }}>
                  {Number(summary.total_units || 0).toLocaleString()}
                </div>
              </div>
              <div className="card" style={{ padding: '1rem' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Low Stock Alert</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--warning-500)', marginTop: '0.25rem' }}>
                  {summary.low_stock_count || 0}
                </div>
              </div>
            </div>
          )}

          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>Product Name</th>
                    <th>Category</th>
                    <th>Cost</th>
                    <th>Selling Price</th>
                    <th>Current Stock</th>
                    <th>Safety Stock</th>
                    <th>Lead Time</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {inventoryList.map((item) => (
                    <tr key={item.sku}>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>{item.sku}</td>
                      <td style={{ fontWeight: 600 }}>{item.product_name}</td>
                      <td>{item.category}</td>
                      <td>₹{item.cost_price.toFixed(2)}</td>
                      <td style={{ fontWeight: 600 }}>₹{item.selling_price.toFixed(2)}</td>
                      <td style={{ fontWeight: 700, color: item.status === 'Low Stock' ? 'var(--warning-500)' : 'var(--text-primary)' }}>{item.current_stock}</td>
                      <td>{item.safety_stock}</td>
                      <td>{item.lead_time_days} days</td>
                      <td><Badge status={item.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* EXPLAINABILITY MODAL */}
      {selectedExplainItem && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(15, 23, 42, 0.75)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1rem'
        }}>
          <div className="card" style={{
            maxWidth: '680px',
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '1.5rem',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)'
          }}>
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem', borderBottom: '1px solid var(--border-light)', paddingBottom: '0.75rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Calculator size={20} color="var(--primary-400)" />
                  <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0 }}>
                    Why This Recommendation?
                  </h2>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: '0.25rem 0 0 0' }}>
                  {selectedExplainItem.name} ({selectedExplainItem.sku}) • {selectedExplainItem.planning_horizon_days}-Day Planning Horizon
                </p>
              </div>
              <button 
                className="btn btn-secondary btn-sm" 
                style={{ padding: '0.35rem', borderRadius: '50%' }}
                onClick={() => setSelectedExplainItem(null)}
              >
                <X size={16} />
              </button>
            </div>

            {/* Section 1: Reorder Recommendation Formula */}
            <div style={{ marginBottom: '1.25rem', padding: '1rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase' }}>
                  1. Reorder Recommendation
                </span>
                <span className="badge" style={{ 
                  background: selectedExplainItem.recommended_quantity > 0 ? 'rgba(99, 102, 241, 0.2)' : 'rgba(51, 65, 85, 0.4)',
                  color: selectedExplainItem.recommended_quantity > 0 ? '#818cf8' : 'var(--text-muted)'
                }}>
                  {selectedExplainItem.recommendation_status}
                </span>
              </div>

              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: selectedExplainItem.recommended_quantity > 0 ? 'var(--primary-400)' : 'var(--text-muted)', marginBottom: '0.5rem' }}>
                Recommended Quantity: {selectedExplainItem.recommended_quantity} units
              </div>

              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem', lineHeight: 1.5 }}>
                {selectedExplainItem.explanation?.reorder?.reason}
              </p>

              <div style={{ background: 'var(--bg-app)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--primary-400)', lineHeight: 1.6 }}>
                <div><strong>Formula:</strong> Required Stock (Forecast + Safety Stock) - Current Stock - Stock on Order</div>
                <div><strong>Evaluation:</strong> {selectedExplainItem.explanation?.reorder?.calculation_string}</div>
              </div>

              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <Info size={12} />
                <span>{selectedExplainItem.explanation?.reorder?.mvp_assumption}</span>
              </div>
            </div>

            {/* Section 2: Stockout Risk */}
            <div style={{ marginBottom: '1.25rem', padding: '1rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase' }}>
                  2. Stockout Risk Evaluation
                </span>
                <span className={selectedExplainItem.stockout_risk ? "badge badge-out-of-stock" : "badge badge-healthy"}>
                  {selectedExplainItem.stockout_risk ? "Stockout Risk Detected" : "Protected"}
                </span>
              </div>

              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem', lineHeight: 1.5 }}>
                {selectedExplainItem.explanation?.stockout_risk?.reason}
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                <div>• Lead Time: <strong>{selectedExplainItem.lead_time_days} days</strong></div>
                <div>• Lead-Time Demand: <strong>{selectedExplainItem.lead_time_demand} units</strong></div>
                <div>• Safety Buffer: <strong>{selectedExplainItem.safety_stock} units</strong></div>
                <div>• Shortage Gap: <strong style={{ color: selectedExplainItem.stockout_risk ? 'var(--danger-500)' : 'var(--text-primary)' }}>{selectedExplainItem.stockout_gap} units</strong></div>
              </div>
            </div>

            {/* Section 3: Overstock Risk */}
            <div style={{ marginBottom: '1.25rem', padding: '1rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase' }}>
                  3. Overstock Risk Analysis
                </span>
                <span className={selectedExplainItem.overstock_risk ? "badge badge-low-stock" : "badge"}>
                  {selectedExplainItem.overstock_risk ? "Overstocked" : "Normal Velocity"}
                </span>
              </div>

              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', lineHeight: 1.5 }}>
                {selectedExplainItem.explanation?.overstock_risk?.reason}
              </p>

              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                30-Day Sales: <strong>{selectedExplainItem.units_sold_30d} units</strong> (avg {selectedExplainItem.average_30_day_demand} units/day) • Overstock Threshold (1.5x): <strong>{selectedExplainItem.overstock_threshold} units</strong>
              </div>
            </div>

            {/* Section 4: Safety Stock Derivation */}
            <div style={{ marginBottom: '1.25rem', padding: '1rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', display: 'block', marginBottom: '0.5rem' }}>
                4. Safety Stock Buffer Derivation
              </span>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
                {selectedExplainItem.explanation?.safety_stock?.reason}
              </p>
            </div>

            {/* Decision Protocol Footer */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem', background: 'rgba(16, 185, 129, 0.08)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--success-500)' }}>
                <ShieldCheck size={18} />
                <span>SmartRetail never auto-orders. The store owner retains 100% final purchasing control.</span>
              </div>
              <button className="btn btn-secondary btn-sm" onClick={() => setSelectedExplainItem(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
