import React, { useState } from 'react';
import { ShoppingCart, CheckCircle, Receipt, AlertCircle, Plus, CreditCard } from 'lucide-react';
import Badge from '../components/common/Badge';

export default function Sales() {
  const [selectedProduct, setSelectedProduct] = useState('1');
  const [quantity, setQuantity] = useState(1);
  const [paymentMethod, setPaymentMethod] = useState('UPI');

  // Phase 6 Visual Placeholders - Will connect to POST /api/sales in Phase 8
  const mockTransactions = [
    { receipt: 'REC-20260920-030', date: '2026-09-20 19:00', items: 5, amount: 1620.00, method: 'Cash' },
    { receipt: 'REC-20260919-029', date: '2026-09-19 17:35', items: 5, amount: 1435.00, method: 'UPI' },
    { receipt: 'REC-20260918-028', date: '2026-09-18 15:10', items: 4, amount: 1980.00, method: 'Card' },
    { receipt: 'REC-20260917-027', date: '2026-09-17 13:20', items: 3, amount: 1290.00, method: 'UPI' },
  ];

  return (
    <div>
      <div className="placeholder-banner">
        <AlertCircle size={16} />
        <span>Phase 6 Visual Shell — POS sales terminal & transaction ledger preview. Full sales transaction backend integration activates in Phase 8.</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.8fr', gap: '1.5rem' }}>
        {/* Quick Sale POS Panel */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ShoppingCart size={18} color="var(--primary-400)" />
              <h2 className="card-title">Quick Sale Entry (POS)</h2>
            </div>
          </div>

          <form onSubmit={(e) => e.preventDefault()} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Select Product</label>
              <select
                className="form-select"
                value={selectedProduct}
                onChange={(e) => setSelectedProduct(e.target.value)}
              >
                <option value="1">Masala Chai Tea Bags 250g (₹135.00)</option>
                <option value="2">Arabica Filter Coffee 500g (₹330.00)</option>
                <option value="6">Classic Salted Potato Crisps (₹35.00)</option>
                <option value="9">Premium Basmati Rice 5kg (₹560.00)</option>
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Quantity</label>
                <input
                  type="number"
                  min="1"
                  className="form-input"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Unit Price (₹)</label>
                <input
                  type="text"
                  className="form-input"
                  value="135.00"
                  disabled
                  style={{ opacity: 0.7 }}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Payment Method</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem' }}>
                {['UPI', 'Cash', 'Card'].map((method) => (
                  <button
                    key={method}
                    type="button"
                    className={`btn ${paymentMethod === method ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ padding: '0.5rem' }}
                    onClick={() => setPaymentMethod(method)}
                  >
                    {method}
                  </button>
                ))}
              </div>
            </div>

            <div style={{
              padding: '1rem',
              background: 'var(--bg-surface-elevated)',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: '0.5rem'
            }}>
              <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Total Payable</span>
              <span style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--primary-400)' }}>
                ₹{(135.00 * (parseInt(quantity) || 1)).toFixed(2)}
              </span>
            </div>

            <button type="button" className="btn btn-primary" style={{ padding: '0.75rem' }}>
              <CheckCircle size={16} />
              <span>Complete Sale & Deduct Stock</span>
            </button>
          </form>
        </div>

        {/* Transaction History */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Receipt size={18} color="var(--text-muted)" />
              <h2 className="card-title">Recent Sales Transactions</h2>
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Last 30 days</span>
          </div>

          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Receipt #</th>
                  <th>Date / Time</th>
                  <th>Items</th>
                  <th>Payment</th>
                  <th style={{ textAlign: 'right' }}>Total Amount</th>
                </tr>
              </thead>
              <tbody>
                {mockTransactions.map((tx) => (
                  <tr key={tx.receipt}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--primary-400)' }}>
                      {tx.receipt}
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{tx.date}</td>
                    <td>{tx.items} line items</td>
                    <td>
                      <span className="badge badge-pending">{tx.method}</span>
                    </td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>₹{tx.amount.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
