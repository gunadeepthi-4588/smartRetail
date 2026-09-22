import React, { useState } from 'react';
import { Search, Filter, Plus, Edit2, AlertCircle, Eye } from 'lucide-react';
import Badge from '../components/common/Badge';

export default function Inventory() {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');

  // Phase 6 Visual Placeholders - Will connect to GET /api/inventory in Phase 7
  const mockInventory = [
    { sku: 'SKU-BEV-001', name: 'Masala Chai Tea Bags 250g', category: 'Beverages', cost: 90.0, price: 135.0, stock: 12, safety: 25, status: 'Low Stock' },
    { sku: 'SKU-BEV-002', name: 'Arabica Filter Coffee 500g', category: 'Beverages', cost: 220.0, price: 330.0, stock: 45, safety: 15, status: 'Healthy' },
    { sku: 'SKU-SNK-002', name: 'Classic Salted Potato Crisps 100g', category: 'Snacks', cost: 20.0, price: 35.0, stock: 8, safety: 30, status: 'Low Stock' },
    { sku: 'SKU-STP-001', name: 'Premium Basmati Rice 5kg', category: 'Staples', cost: 420.0, price: 560.0, stock: 7, safety: 15, status: 'Low Stock' },
    { sku: 'SKU-PC-002', name: 'Coconut Nourishing Shampoo 350ml', category: 'Personal Care', cost: 150.0, price: 230.0, stock: 110, safety: 15, status: 'Overstocked' },
    { sku: 'SKU-HH-004', name: 'Microfiber Cleaning Cloth 3-Pack', category: 'Household', cost: 60.0, price: 100.0, stock: 165, safety: 10, status: 'Overstocked' },
  ];

  return (
    <div>
      <div className="placeholder-banner">
        <AlertCircle size={16} />
        <span>Phase 6 Visual Shell — Product & Inventory catalog preview. Real-time REST API connection will activate in Phase 7.</span>
      </div>

      {/* Controls Bar */}
      <div className="controls-bar">
        <div style={{ display: 'flex', gap: '0.75rem', flex: 1, flexWrap: 'wrap' }}>
          <div className="search-input-wrapper">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              className="form-input search-input"
              placeholder="Search by product name or SKU..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <select
            className="form-select"
            style={{ width: 'auto', minWidth: '150px' }}
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

          <select
            className="form-select"
            style={{ width: 'auto', minWidth: '150px' }}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="All">All Statuses</option>
            <option value="Healthy">Healthy</option>
            <option value="Low Stock">Low Stock</option>
            <option value="Overstocked">Overstocked</option>
            <option value="Out of Stock">Out of Stock</option>
          </select>
        </div>

        <button className="btn btn-primary">
          <Plus size={16} />
          <span>Add New Product</span>
        </button>
      </div>

      {/* Inventory Table */}
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
                <th>Stock Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {mockInventory.map((item) => (
                <tr key={item.sku}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {item.sku}
                  </td>
                  <td style={{ fontWeight: 600 }}>{item.name}</td>
                  <td>{item.category}</td>
                  <td>₹{item.cost.toFixed(2)}</td>
                  <td style={{ fontWeight: 600 }}>₹{item.price.toFixed(2)}</td>
                  <td style={{ fontWeight: 700, fontSize: '0.95rem' }}>{item.stock}</td>
                  <td style={{ color: 'var(--text-secondary)' }}>{item.safety}</td>
                  <td>
                    <Badge status={item.status} />
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '0.5rem' }}>
                      <button className="btn btn-secondary btn-sm" title="Adjust Stock">
                        <Edit2 size={13} />
                      </button>
                      <button className="btn btn-secondary btn-sm" title="View Details">
                        <Eye size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
