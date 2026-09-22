import React, { useState, useEffect, useCallback } from 'react';
import { 
  Search, 
  Filter, 
  Plus, 
  Edit2, 
  Eye, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle2, 
  Boxes, 
  AlertTriangle, 
  PackageX, 
  TrendingUp 
} from 'lucide-react';
import { getInventory } from '../services/api';
import Badge from '../components/common/Badge';

export default function Inventory() {
  const [inventoryList, setInventoryList] = useState([]);
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');

  // Fetch real inventory data from Flask REST API -> MySQL
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
      console.error('Failed to load inventory from API:', err);
      setError(err.message || 'Unable to load inventory records. Please check the backend connection.');
    } finally {
      setIsLoading(false);
    }
  }, [searchTerm, categoryFilter, statusFilter]);

  // Load on mount and when filters change (with debouncing for search input)
  useEffect(() => {
    const handler = setTimeout(() => {
      loadInventory();
    }, 250);

    return () => clearTimeout(handler);
  }, [loadInventory]);

  return (
    <div>
      {/* Live Connection Banner */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.75rem 1.25rem',
        background: 'rgba(16, 185, 129, 0.08)',
        border: '1px solid rgba(16, 185, 129, 0.25)',
        borderRadius: 'var(--radius-md)',
        fontSize: '0.85rem',
        color: 'var(--success-500)',
        marginBottom: '1.5rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <CheckCircle2 size={16} />
          <span><strong>End-to-End Connected</strong>: React UI fetching live data via <code>GET /api/inventory</code> from MySQL.</span>
        </div>
        <button 
          className="btn btn-secondary btn-sm" 
          onClick={loadInventory} 
          disabled={isLoading}
          style={{ padding: '0.25rem 0.65rem', fontSize: '0.75rem' }}
        >
          <RefreshCw size={12} className={isLoading ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Dynamic Summary Cards (From Real MySQL Aggregates) */}
      {summary && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem'
        }}>
          <div className="card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Total Stock Valuation
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--primary-400)', marginTop: '0.25rem' }}>
              ₹{summary.total_valuation_cost?.toLocaleString('en-IN', { minimumFractionDigits: 2 }) || '0.00'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              At wholesale cost price
            </div>
          </div>

          <div className="card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Low Stock Warnings
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--warning-500)', marginTop: '0.25rem' }}>
              {summary.low_stock_count || 0} items
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Below safety buffer
            </div>
          </div>

          <div className="card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Overstocked Items
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--info-500)', marginTop: '0.25rem' }}>
              {summary.overstocked_count || 0} items
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Above max stock level
            </div>
          </div>

          <div className="card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Active SKUs
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.25rem' }}>
              {inventoryList.length} items
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              In catalog database
            </div>
          </div>
        </div>
      )}

      {/* Search & Filtering Controls */}
      <div className="controls-bar">
        <div style={{ display: 'flex', gap: '0.75rem', flex: 1, flexWrap: 'wrap' }}>
          {/* Search by Name or SKU */}
          <div className="search-input-wrapper">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              className="form-input search-input"
              placeholder="Search product name or SKU..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {/* Category Filter */}
          <select
            className="form-select"
            style={{ width: 'auto', minWidth: '160px' }}
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="All">All Categories</option>
            <option value="Beverages">Beverages</option>
            <option value="Snacks">Snacks</option>
            <option value="Staples">Staples</option>
            <option value="Personal Care">Personal Care</option>
            <option value="Household">Household</option>
          </select>

          {/* Stock Status Filter */}
          <select
            className="form-select"
            style={{ width: 'auto', minWidth: '160px' }}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="All">All Stock Statuses</option>
            <option value="healthy">Healthy Stock</option>
            <option value="low">Low Stock (Alert)</option>
            <option value="overstocked">Overstocked</option>
            <option value="out_of_stock">Out of Stock</option>
          </select>
        </div>

        {/* Add Product Trigger (Coming soon placeholder for Phase 7) */}
        <button 
          className="btn btn-secondary" 
          title="Product CRUD modal will activate in later phase"
          style={{ opacity: 0.8 }}
          onClick={() => alert('Product addition modal will be enabled in subsequent CRUD enhancements. Read operations are fully live!')}
        >
          <Plus size={16} />
          <span>Add Product</span>
        </button>
      </div>

      {/* Main Content States: Loading | Error | Empty | Table */}
      {isLoading && (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1rem' }}>
          <RefreshCw size={32} className="spin" style={{ margin: '0 auto 1rem', color: 'var(--primary-400)' }} />
          <h3 style={{ fontSize: '1.1rem', marginBottom: '0.25rem' }}>Loading Inventory from MySQL...</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Fetching real-time stock levels through Flask REST API</p>
        </div>
      )}

      {!isLoading && error && (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1rem', borderColor: 'var(--danger-500)' }}>
          <AlertCircle size={36} color="var(--danger-500)" style={{ margin: '0 auto 1rem' }} />
          <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem', color: 'var(--danger-500)' }}>Unable to Load Inventory</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', maxWidth: '480px', margin: '0 auto 1.5rem' }}>
            {error}
          </p>
          <button className="btn btn-primary" onClick={loadInventory}>
            <RefreshCw size={14} />
            <span>Retry Connection</span>
          </button>
        </div>
      )}

      {!isLoading && !error && inventoryList.length === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1rem' }}>
          <PackageX size={36} color="var(--text-muted)" style={{ margin: '0 auto 1rem' }} />
          <h3 style={{ fontSize: '1.1rem', marginBottom: '0.25rem' }}>No Products Found</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
            No inventory items matched your search "{searchTerm}" or active filter selections.
          </p>
          <button 
            className="btn btn-secondary btn-sm"
            onClick={() => { setSearchTerm(''); setCategoryFilter('All'); setStatusFilter('All'); }}
          >
            Clear Filters
          </button>
        </div>
      )}

      {!isLoading && !error && inventoryList.length > 0 && (
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
                  <th>Stock Status</th>
                </tr>
              </thead>
              <tbody>
                {inventoryList.map((item) => (
                  <tr key={item.sku}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {item.sku}
                    </td>
                    <td style={{ fontWeight: 600 }}>{item.product_name}</td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {item.category}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>₹{item.cost_price.toFixed(2)}</td>
                    <td style={{ fontWeight: 600 }}>₹{item.selling_price.toFixed(2)}</td>
                    <td style={{ 
                      fontWeight: 700, 
                      fontSize: '1rem',
                      color: item.status === 'Low Stock' ? 'var(--warning-500)' : item.status === 'Out of Stock' ? 'var(--danger-500)' : 'var(--text-primary)'
                    }}>
                      {item.current_stock}
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{item.safety_stock}</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{item.lead_time_days} days</td>
                    <td>
                      <Badge status={item.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
