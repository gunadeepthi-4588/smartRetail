import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Store, User, Database, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { getBackendHealth } from '../services/api';
import Badge from '../components/common/Badge';

export default function Settings() {
  const [dbStatus, setDbStatus] = useState({ status: 'checking', message: 'Checking API...' });
  const [isRefreshing, setIsRefreshing] = useState(false);

  const checkHealth = () => {
    setIsRefreshing(true);
    getBackendHealth()
      .then((data) => {
        setDbStatus(data);
        setIsRefreshing(false);
      })
      .catch((err) => {
        setDbStatus({ status: 'offline', error: err.message });
        setIsRefreshing(false);
      });
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <div>
      <div className="placeholder-banner">
        <AlertCircle size={16} />
        <span>Phase 6 Visual Shell — Store preferences & system configuration. Real settings persistence activates in later phases.</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Store Profile */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Store size={18} color="var(--primary-400)" />
              <h2 className="card-title">Store Profile</h2>
            </div>
            <Badge status="Healthy" text="Single Store" />
          </div>

          <form onSubmit={(e) => e.preventDefault()} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Store Name</label>
              <input type="text" className="form-input" defaultValue="Metro Mart Superstore" />
            </div>

            <div className="form-group">
              <label className="form-label">Owner Name</label>
              <input type="text" className="form-input" defaultValue="Rajesh Kumar" />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Currency Code</label>
                <input type="text" className="form-input" defaultValue="INR" disabled />
              </div>
              <div className="form-group">
                <label className="form-label">Currency Symbol</label>
                <input type="text" className="form-input" defaultValue="₹" disabled />
              </div>
            </div>

            <button type="button" className="btn btn-primary" style={{ alignSelf: 'flex-start' }}>
              Save Store Changes
            </button>
          </form>
        </div>

        {/* Account & System Diagnostics */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Account Card */}
          <div className="card">
            <div className="card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <User size={18} color="var(--text-muted)" />
                <h2 className="card-title">User Account</h2>
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.875rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Username:</span>
                <span style={{ fontWeight: 600 }}>rajesh_owner</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Email:</span>
                <span>rajesh@metromart.com</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Role:</span>
                <span>Primary Store Administrator</span>
              </div>
            </div>
          </div>

          {/* System Diagnostics Card */}
          <div className="card">
            <div className="card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Database size={18} color="var(--primary-400)" />
                <h2 className="card-title">System & API Status</h2>
              </div>
              <button className="btn btn-secondary btn-sm" onClick={checkHealth} disabled={isRefreshing}>
                <RefreshCw size={13} className={isRefreshing ? 'spin' : ''} />
                <span>Test API</span>
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Frontend Client</span>
                <span className="badge badge-healthy">React + Vite Active</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Flask REST Backend</span>
                {dbStatus.status === 'online' ? (
                  <span className="badge badge-healthy">API Online</span>
                ) : (
                  <span className="badge badge-low-stock">Connecting...</span>
                )}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Database Engine</span>
                <span className="badge badge-healthy">MySQL InnoDB</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
