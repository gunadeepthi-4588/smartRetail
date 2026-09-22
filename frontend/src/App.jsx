import React, { useState, useEffect } from 'react';
import { getBackendHealth } from './services/api';

export default function App() {
  const [backendStatus, setBackendStatus] = useState({ status: 'checking', service: 'Connecting to Flask API...' });

  useEffect(() => {
    getBackendHealth()
      .then((data) => setBackendStatus(data))
      .catch((err) => setBackendStatus({ status: 'offline', error: err.message }));
  }, []);

  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
      <header className="card" style={{ maxWidth: '640px', width: '100%', textAlign: 'center' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.75rem', background: 'linear-gradient(135deg, #818cf8, #c084fc)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          SmartRetail Platform
        </h1>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
          End-to-End Retail Inventory Intelligence & Demand Forecasting
        </p>

        <section style={{ padding: '1rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', textAlign: 'left' }}>
          <h2 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>
            System Architecture Status
          </h2>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.875rem' }}>Frontend Application</span>
            <span className="badge badge-success">Vite + React Active</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.875rem' }}>Flask REST API Bridge</span>
            {backendStatus.status === 'online' ? (
              <span className="badge badge-success">API Online</span>
            ) : backendStatus.status === 'checking' ? (
              <span className="badge badge-warning">Checking...</span>
            ) : (
              <span className="badge badge-danger">Offline / Ready for Phase 4</span>
            )}
          </div>
        </section>

        <footer style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Phase 2 Project Setup Complete • Single Store Architecture
        </footer>
      </header>
    </main>
  );
}
