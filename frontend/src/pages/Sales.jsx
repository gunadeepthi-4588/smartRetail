import React, { useState, useEffect, useCallback } from 'react';
import { 
  ShoppingCart, 
  CheckCircle, 
  Receipt, 
  AlertCircle, 
  Plus, 
  Trash2, 
  RefreshCw, 
  CreditCard, 
  Eye, 
  X, 
  CheckCircle2,
  PackageCheck
} from 'lucide-react';
import { getProducts, createSale, getSales, getSale } from '../services/api';
import Badge from '../components/common/Badge';

export default function Sales() {
  // Product Catalog & Cart State
  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [selectedQuantity, setSelectedQuantity] = useState(1);
  const [cart, setCart] = useState([]);
  const [paymentMethod, setPaymentMethod] = useState('UPI');

  // UI & Network States
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [successReceipt, setSuccessReceipt] = useState(null);

  // Sales History State
  const [salesHistory, setSalesHistory] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [historyFilterMethod, setHistoryFilterMethod] = useState('All');
  const [selectedSaleDetail, setSelectedSaleDetail] = useState(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  // Fetch product catalog for POS dropdown
  const loadProductCatalog = useCallback(async () => {
    try {
      const response = await getProducts();
      const productList = response.data || [];
      setProducts(productList);
      if (productList.length > 0 && !selectedProductId) {
        setSelectedProductId(String(productList[0].product_id));
      }
    } catch (err) {
      console.error('Failed to load products for POS:', err);
    }
  }, [selectedProductId]);

  // Fetch sales transaction history
  const loadSalesHistory = useCallback(async () => {
    setIsLoadingHistory(true);
    try {
      const response = await getSales({ payment_method: historyFilterMethod });
      setSalesHistory(response.data || []);
    } catch (err) {
      console.error('Failed to load sales history:', err);
    } finally {
      setIsLoadingHistory(false);
    }
  }, [historyFilterMethod]);

  useEffect(() => {
    loadProductCatalog();
  }, [loadProductCatalog]);

  useEffect(() => {
    loadSalesHistory();
  }, [loadSalesHistory]);

  const currentSelectedProduct = products.find((p) => String(p.product_id) === String(selectedProductId));

  // Add selected item to Cart
  const handleAddToCart = () => {
    setErrorMessage(null);
    setSuccessReceipt(null);
    if (!currentSelectedProduct) return;

    const qty = parseInt(selectedQuantity) || 1;
    if (qty <= 0) {
      setErrorMessage('Quantity must be greater than zero.');
      return;
    }

    const availableStock = currentSelectedProduct.current_stock || 0;
    const existingInCart = cart.find((item) => item.product_id === currentSelectedProduct.product_id);
    const currentCartQty = existingInCart ? existingInCart.quantity : 0;
    const totalRequested = currentCartQty + qty;

    if (totalRequested > availableStock) {
      setErrorMessage(
        `Insufficient stock for "${currentSelectedProduct.name}". Available: ${availableStock} units, already in cart: ${currentCartQty}.`
      );
      return;
    }

    if (existingInCart) {
      setCart(
        cart.map((item) =>
          item.product_id === currentSelectedProduct.product_id
            ? {
                ...item,
                quantity: totalRequested,
                line_total: Number((totalRequested * item.unit_price).toFixed(2)),
              }
            : item
        )
      );
    } else {
      setCart([
        ...cart,
        {
          product_id: currentSelectedProduct.product_id,
          name: currentSelectedProduct.name,
          sku: currentSelectedProduct.sku,
          unit_price: currentSelectedProduct.selling_price,
          quantity: qty,
          available_stock: availableStock,
          line_total: Number((qty * currentSelectedProduct.selling_price).toFixed(2)),
        },
      ]);
    }

    setSelectedQuantity(1);
  };

  const handleRemoveFromCart = (productId) => {
    setCart(cart.filter((item) => item.product_id !== productId));
  };

  const handleUpdateCartQty = (productId, newQty) => {
    const qty = parseInt(newQty);
    if (isNaN(qty) || qty <= 0) return;

    const targetItem = cart.find((item) => item.product_id === productId);
    if (!targetItem) return;

    if (qty > targetItem.available_stock) {
      setErrorMessage(`Cannot exceed available stock of ${targetItem.available_stock} units for ${targetItem.name}.`);
      return;
    }

    setErrorMessage(null);
    setCart(
      cart.map((item) =>
        item.product_id === productId
          ? {
              ...item,
              quantity: qty,
              line_total: Number((qty * item.unit_price).toFixed(2)),
            }
          : item
      )
    );
  };

  // Grand Total Calculation
  const grandTotal = cart.reduce((sum, item) => sum + item.line_total, 0);

  // Complete POS Sale
  const handleCheckout = async () => {
    if (cart.length === 0) {
      setErrorMessage('Please add at least one product to the sale before completing checkout.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setSuccessReceipt(null);

    const salePayload = {
      store_id: 1,
      payment_method: paymentMethod,
      items: cart.map((item) => ({
        product_id: item.product_id,
        quantity: item.quantity,
        unit_price: item.unit_price,
      })),
    };

    try {
      const result = await createSale(salePayload);
      setSuccessReceipt(result.data);
      setCart([]); // Clear cart
      // Refresh catalog and sales history
      loadProductCatalog();
      loadSalesHistory();
    } catch (err) {
      console.error('Checkout failed:', err);
      setErrorMessage(err.message || 'Transaction failed. No items were deducted.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // View Sale Details
  const handleViewSaleDetail = async (saleId) => {
    setIsLoadingDetail(true);
    try {
      const response = await getSale(saleId);
      setSelectedSaleDetail(response.data);
    } catch (err) {
      console.error('Failed to fetch sale detail:', err);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  return (
    <div>
      {/* Success Receipt Banner */}
      {successReceipt && (
        <div style={{
          padding: '1.25rem',
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: 'var(--radius-lg)',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: '1rem'
        }}>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
            <CheckCircle2 size={24} color="var(--success-500)" style={{ marginTop: '0.15rem' }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--success-500)' }}>
                Sale Completed Successfully — Receipt: {successReceipt.receipt_number}
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                Total: <strong>₹{successReceipt.total_amount.toFixed(2)}</strong> paid via <strong>{successReceipt.payment_method}</strong>. 
                Inventory stock decremented atomically across {successReceipt.items_count} line items.
              </p>
            </div>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => setSuccessReceipt(null)}>
            Dismiss
          </button>
        </div>
      )}

      {/* Error Alert */}
      {errorMessage && (
        <div style={{
          padding: '1rem',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--danger-500)',
          fontSize: '0.875rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertCircle size={18} />
            <span>{errorMessage}</span>
          </div>
          <button 
            onClick={() => setErrorMessage(null)} 
            style={{ background: 'none', border: 'none', color: 'var(--danger-500)', cursor: 'pointer' }}
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Main POS Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.8fr', gap: '1.5rem' }}>
        {/* Quick Sale POS Entry Panel */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ShoppingCart size={18} color="var(--primary-400)" />
              <h2 className="card-title">POS Quick Checkout</h2>
            </div>
            <span className="badge badge-healthy">Live Stock Sync</span>
          </div>

          {/* Add Item Form */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', marginBottom: '1.25rem', paddingBottom: '1.25rem', borderBottom: '1px solid var(--border-subtle)' }}>
            <div className="form-group">
              <label className="form-label">Select Product</label>
              <select
                className="form-select"
                value={selectedProductId}
                onChange={(e) => setSelectedProductId(e.target.value)}
              >
                {products.map((p) => (
                  <option key={p.product_id} value={p.product_id}>
                    {p.name} — ₹{p.selling_price.toFixed(2)} (Stock: {p.current_stock})
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div className="form-group">
                <label className="form-label">Quantity</label>
                <input
                  type="number"
                  min="1"
                  max={currentSelectedProduct?.current_stock || 999}
                  className="form-input"
                  value={selectedQuantity}
                  onChange={(e) => setSelectedQuantity(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Unit Price</label>
                <input
                  type="text"
                  className="form-input"
                  value={currentSelectedProduct ? `₹${currentSelectedProduct.selling_price.toFixed(2)}` : '₹0.00'}
                  disabled
                  style={{ opacity: 0.75 }}
                />
              </div>
            </div>

            <button type="button" className="btn btn-secondary" onClick={handleAddToCart} style={{ width: '100%' }}>
              <Plus size={15} />
              <span>Add to Sale</span>
            </button>
          </div>

          {/* Cart Items List */}
          <div style={{ marginBottom: '1.25rem' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
              Current Cart ({cart.length} items)
            </div>

            {cart.length === 0 ? (
              <div style={{ padding: '1.5rem', textAlign: 'center', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Cart is currently empty. Add items above.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '200px', overflowY: 'auto' }}>
                {cart.map((item) => (
                  <div
                    key={item.product_id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.5rem 0.75rem',
                      background: 'var(--bg-surface-elevated)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.85rem'
                    }}
                  >
                    <div style={{ flex: 1, minWidth: 0, paddingRight: '0.5rem' }}>
                      <div style={{ fontWeight: 600, textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                        {item.name}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        ₹{item.unit_price.toFixed(2)} × {item.quantity}
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <span style={{ fontWeight: 700, color: 'var(--primary-400)' }}>
                        ₹{item.line_total.toFixed(2)}
                      </span>
                      <button
                        onClick={() => handleRemoveFromCart(item.product_id)}
                        style={{ background: 'none', border: 'none', color: 'var(--danger-500)', cursor: 'pointer', padding: '0.2rem' }}
                        title="Remove item"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Payment Method Selector */}
          <div className="form-group" style={{ marginBottom: '1.25rem' }}>
            <label className="form-label">Payment Method</label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem' }}>
              {['UPI', 'Cash', 'Card'].map((m) => (
                <button
                  key={m}
                  type="button"
                  className={`btn ${paymentMethod === m ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '0.5rem', fontSize: '0.8rem' }}
                  onClick={() => setPaymentMethod(m)}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          {/* Payable Total & Complete Button */}
          <div style={{
            padding: '1rem',
            background: 'var(--bg-surface-elevated)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1rem'
          }}>
            <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Total Payable</span>
            <span style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--primary-400)' }}>
              ₹{grandTotal.toFixed(2)}
            </span>
          </div>

          <button
            type="button"
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.75rem', fontSize: '0.95rem' }}
            onClick={handleCheckout}
            disabled={cart.length === 0 || isSubmitting}
          >
            {isSubmitting ? (
              <>
                <RefreshCw size={16} className="spin" />
                <span>Processing Atomic Transaction...</span>
              </>
            ) : (
              <>
                <CheckCircle size={16} />
                <span>Complete Sale ({cart.length} items)</span>
              </>
            )}
          </button>
        </div>

        {/* Transaction History & Detail View */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Receipt size={18} color="var(--text-muted)" />
              <h2 className="card-title">Sales Transaction Ledger</h2>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <select
                className="form-select"
                style={{ width: 'auto', padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                value={historyFilterMethod}
                onChange={(e) => setHistoryFilterMethod(e.target.value)}
              >
                <option value="All">All Methods</option>
                <option value="UPI">UPI</option>
                <option value="Cash">Cash</option>
                <option value="Card">Card</option>
              </select>
              <button className="btn btn-secondary btn-sm" onClick={loadSalesHistory}>
                <RefreshCw size={12} className={isLoadingHistory ? 'spin' : ''} />
              </button>
            </div>
          </div>

          {/* Transactions Table */}
          <div className="table-container" style={{ flex: 1 }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Receipt #</th>
                  <th>Date</th>
                  <th>Items</th>
                  <th>Payment</th>
                  <th style={{ textAlign: 'right' }}>Total Amount</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {isLoadingHistory ? (
                  <tr>
                    <td colSpan="6" style={{ textAlign: 'center', padding: '2rem' }}>
                      <RefreshCw size={20} className="spin" style={{ margin: '0 auto 0.5rem' }} />
                      <div>Loading transactions from MySQL...</div>
                    </td>
                  </tr>
                ) : salesHistory.length === 0 ? (
                  <tr>
                    <td colSpan="6" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                      No sales transactions found.
                    </td>
                  </tr>
                ) : (
                  salesHistory.map((s) => (
                    <tr key={s.sale_id}>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--primary-400)', fontWeight: 600 }}>
                        {s.receipt_number}
                      </td>
                      <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {s.sale_date ? s.sale_date.split('T')[0] : 'Today'}
                      </td>
                      <td>{s.items_count} items ({s.total_units_sold} units)</td>
                      <td>
                        <span className="badge badge-pending">{s.payment_method}</span>
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 600 }}>
                        ₹{s.total_amount.toFixed(2)}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          style={{ padding: '0.2rem 0.5rem' }}
                          onClick={() => handleViewSaleDetail(s.sale_id)}
                          title="View Line Items"
                        >
                          <Eye size={12} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Sale Detail Modal */}
      {selectedSaleDetail && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.75)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 50,
          padding: '1.5rem'
        }}>
          <div className="card" style={{ maxWidth: '560px', width: '100%', maxHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
            <div className="card-header">
              <div>
                <h3 className="card-title">Receipt #{selectedSaleDetail.receipt_number}</h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {selectedSaleDetail.sale_date} • Paid via {selectedSaleDetail.payment_method}
                </p>
              </div>
              <button 
                onClick={() => setSelectedSaleDetail(null)}
                style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            <div className="table-container" style={{ flex: 1, overflowY: 'auto' }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Item</th>
                    <th>Qty</th>
                    <th>Price</th>
                    <th style={{ textAlign: 'right' }}>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedSaleDetail.items.map((item) => (
                    <tr key={item.sale_item_id}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{item.product_name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>SKU: {item.sku}</div>
                      </td>
                      <td>{item.quantity}</td>
                      <td>₹{item.unit_price.toFixed(2)}</td>
                      <td style={{ textAlign: 'right', fontWeight: 600 }}>₹{item.line_total.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              paddingTop: '1rem',
              marginTop: '1rem',
              borderTop: '1px solid var(--border-subtle)'
            }}>
              <span style={{ fontWeight: 600 }}>Grand Total</span>
              <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary-400)' }}>
                ₹{selectedSaleDetail.total_amount.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
